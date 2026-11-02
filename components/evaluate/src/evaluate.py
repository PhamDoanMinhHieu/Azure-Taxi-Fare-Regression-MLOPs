import argparse
import os
import pickle
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from azureml.core import Run, Model

run = Run.get_context()
ws = run.experiment.workspace

parser = argparse.ArgumentParser("evaluate")
parser.add_argument("--model_name", type=str, help="Name of registered model")
parser.add_argument("--model_input", type=str, help="Path of input model")
parser.add_argument("--test_data", type=str, help="Path to test data")
parser.add_argument("--predictions", type=str, help="Path of predictions")
parser.add_argument("--score_report", type=str, help="Path to score report")
parser.add_argument("--deploy_flag", type=str, help="A deploy flag whether to deploy or not")
args = parser.parse_args()

FEATURE_COLUMNS = [
    "distance",
    "dropoff_latitude",
    "dropoff_longitude",
    "passengers",
    "pickup_latitude",
    "pickup_longitude",
    "store_forward",
    "vendor",
    "pickup_weekday",
    "pickup_month",
    "pickup_monthday",
    "pickup_hour",
    "pickup_minute",
    "pickup_second",
    "dropoff_weekday",
    "dropoff_month",
    "dropoff_monthday",
    "dropoff_hour",
    "dropoff_minute",
    "dropoff_second",
]

test_data = pd.read_csv(Path(args.test_data) / "test.csv")
testy = test_data["cost"]
testX = test_data[FEATURE_COLUMNS]

with open(Path(args.model_input) / "model.sav", "rb") as f:
    model = pickle.load(f)

output_data = testX.copy()
output_data["actual_cost"] = testy
output_data["predicted_cost"] = model.predict(testX)
output_data.to_csv(Path(args.predictions) / "predictions.csv", index=False)

actuals = output_data["actual_cost"]
predictions = output_data["predicted_cost"]
mse = mean_squared_error(actuals, predictions)
r2 = r2_score(actuals, predictions)

print("Coefficients:", model.coef_)
print(f"Mean squared error: {mse:.2f}")
print(f"Coefficient of determination (R2): {r2:.2f}")

with open(Path(args.score_report) / "score.txt", "w") as f:
    f.write(f"Scored with the following model:\n{model}\n")
    f.write(f"Coefficients:\n{model.coef_}\n")
    f.write(f"Mean squared error: {mse:.2f}\n")
    f.write(f"Coefficient of determination: {r2:.2f}\n")

run.log("mse", mse)
run.log("r2", r2)
run.parent.log("mse", mse)
run.parent.log("r2", r2)

# -------------------- So sánh với model đang được đăng ký (nếu có) -------------------- #
test_scores = {}
current_score = r2

for model_run in Model.list(ws, name=args.model_name):
    model_dir = Model.download(model_run, exist_ok=True)
    model_file = Path(model_dir) / "model.sav"
    if not model_file.exists():
        # phòng trường hợp model được đăng ký trực tiếp từ file .sav thay vì folder
        candidates = list(Path(model_dir).rglob("*.sav"))
        if not candidates:
            continue
        model_file = candidates[0]
    with open(model_file, "rb") as f:
        prior_model = pickle.load(f)
    prior_predictions = prior_model.predict(testX)
    test_scores[model_run.id] = r2_score(actuals, prior_predictions)

print("Previous model scores:", test_scores)

deploy_flag = 1 if not test_scores or current_score >= max(test_scores.values()) else 0

with open(Path(args.deploy_flag) / "deploy_flag", "w") as f:
    f.write(str(int(deploy_flag)))

run.log("deploy flag", bool(deploy_flag))
run.parent.log("deploy flag", bool(deploy_flag))

test_scores["current model"] = current_score
plot_df = pd.DataFrame(test_scores, index=["r2 score"])
ax = plot_df.plot(kind="bar", figsize=(15, 10), legend=False, title="R2 score: candidate vs. registered models")
ax.figure.savefig(Path(args.score_report) / "model_runs_metrics_plot.png")
run.log_image(name="MODEL RUNS METRICS COMPARISON", path=str(Path(args.score_report) / "model_runs_metrics_plot.png"))
run.parent.log_image(name="MODEL RUNS METRICS COMPARISON", path=str(Path(args.score_report) / "model_runs_metrics_plot.png"))

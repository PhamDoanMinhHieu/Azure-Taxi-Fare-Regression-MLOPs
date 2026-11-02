import argparse
from pathlib import Path
import pickle

import pandas as pd
from sklearn.linear_model import LinearRegression
import mlflow
import mlflow.sklearn

parser = argparse.ArgumentParser("train")
parser.add_argument("--training_data", type=str, help="Path to training data")
parser.add_argument("--model_output", type=str, help="Path of output model")
args = parser.parse_args()

mlflow.sklearn.autolog()

print(f"Training data path: {args.training_data}")
print(f"Model output path: {args.model_output}")

train_data = pd.read_csv(Path(args.training_data) / "train.csv")

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

trainy = train_data["cost"]
trainX = train_data[FEATURE_COLUMNS]

print(trainX.shape, trainX.columns.tolist())

model = LinearRegression().fit(trainX, trainy)
print("train R2:", model.score(trainX, trainy))

with open(Path(args.model_output) / "model.sav", "wb") as f:
    pickle.dump(model, f)

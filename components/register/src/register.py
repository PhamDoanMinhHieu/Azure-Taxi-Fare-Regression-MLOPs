import argparse
from pathlib import Path
from azureml.core import Run, Model

parser = argparse.ArgumentParser("register")
parser.add_argument("--model_name", type=str, help="Name under which model will be registered")
parser.add_argument("--model_path", type=str, help="Model directory")
parser.add_argument("--deploy_flag", type=str, help="A deploy flag whether to deploy or not")
args = parser.parse_args()

with open(Path(args.deploy_flag) / "deploy_flag", "r") as f:
    deploy_flag = int(f.read())

run = Run.get_context()
ws = run.experiment.workspace

if deploy_flag == 1:
    print("Registering", args.model_name)
    registered_model = Model.register(
        model_path=args.model_path,
        model_name=args.model_name,
        workspace=ws,
    )
    print("Registered", registered_model.id)
else:
    print("Model will not be registered: it did not outperform the current registered model.")

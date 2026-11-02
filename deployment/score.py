import json
import os
import pickle
from pathlib import Path

import pandas as pd

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

model = None


def init():
    global model
    model_root = Path(os.environ["AZUREML_MODEL_DIR"])
    model_file = next(model_root.rglob("model.sav"))
    with open(model_file, "rb") as f:
        model = pickle.load(f)


def run(raw_data):
    records = json.loads(raw_data)["data"]
    df = pd.DataFrame(records)[FEATURE_COLUMNS]
    predictions = model.predict(df)
    return predictions.tolist()

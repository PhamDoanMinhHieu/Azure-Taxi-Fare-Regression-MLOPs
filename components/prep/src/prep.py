import argparse
from pathlib import Path
import os
import numpy as np
import pandas as pd

from azureml.core import Run

run = Run.get_context()

parser = argparse.ArgumentParser("prep")
parser.add_argument("--raw_data", type=str, help="Path to raw data")
parser.add_argument("--transformed_data", type=str, help="Path of prepped data")

args = parser.parse_args()

print(f"Raw data path: {args.raw_data}")
print(f"Data output path: {args.transformed_data}")

# ------------ Reading Data ------------ #
# -------------------------------------- #

raw_files = sorted(f for f in os.listdir(args.raw_data) if f.endswith(".csv"))
print("csv files found:", raw_files)

green_file = next(f for f in raw_files if "green" in f.lower())
yellow_file = next(f for f in raw_files if "yellow" in f.lower())

green_data = pd.read_csv(Path(args.raw_data) / green_file)
yellow_data = pd.read_csv(Path(args.raw_data) / yellow_file)

# ------------ Cleanse Data ------------ #
# -------------------------------------- #

useful_columns = [
    "cost",
    "distance",
    "dropoff_datetime",
    "dropoff_latitude",
    "dropoff_longitude",
    "passengers",
    "pickup_datetime",
    "pickup_latitude",
    "pickup_longitude",
    "store_forward",
    "vendor",
]

green_columns = {
    "vendorID": "vendor",
    "lpepPickupDatetime": "pickup_datetime",
    "lpepDropoffDatetime": "dropoff_datetime",
    "storeAndFwdFlag": "store_forward",
    "pickupLongitude": "pickup_longitude",
    "pickupLatitude": "pickup_latitude",
    "dropoffLongitude": "dropoff_longitude",
    "dropoffLatitude": "dropoff_latitude",
    "passengerCount": "passengers",
    "fareAmount": "cost",
    "tripDistance": "distance",
}

yellow_columns = {
    "vendorID": "vendor",
    "tpepPickupDateTime": "pickup_datetime",
    "tpepDropoffDateTime": "dropoff_datetime",
    "storeAndFwdFlag": "store_forward",
    "startLon": "pickup_longitude",
    "startLat": "pickup_latitude",
    "endLon": "dropoff_longitude",
    "endLat": "dropoff_latitude",
    "passengerCount": "passengers",
    "fareAmount": "cost",
    "tripDistance": "distance",
}


def cleanse_data(data, columns, keep_columns):
    new_df = data.dropna(how="all").rename(columns=columns)[keep_columns]
    new_df.reset_index(inplace=True, drop=True)
    return new_df


green_data_clean = cleanse_data(green_data, green_columns, useful_columns)
yellow_data_clean = cleanse_data(yellow_data, yellow_columns, useful_columns)

# Merge yellow + green taxi data
combined_df = pd.concat([green_data_clean, yellow_data_clean], ignore_index=True)

green_data_clean.to_csv(Path(args.transformed_data) / "green_prep_data.csv", index=False)
yellow_data_clean.to_csv(Path(args.transformed_data) / "yellow_prep_data.csv", index=False)
combined_df.to_csv(Path(args.transformed_data) / "merged_data.csv", index=False)

# ------------ Filter Data ------------ #
# ------------------------------------- #

# Drop coordinates that fall outside New York City's bounds.
combined_df = combined_df.astype(
    {
        "pickup_longitude": "float64",
        "pickup_latitude": "float64",
        "dropoff_longitude": "float64",
        "dropoff_latitude": "float64",
    }
)

latlong_filtered_df = combined_df[
    (combined_df.pickup_longitude <= -73.72)
    & (combined_df.pickup_longitude >= -74.09)
    & (combined_df.pickup_latitude <= 40.88)
    & (combined_df.pickup_latitude >= 40.53)
    & (combined_df.dropoff_longitude <= -73.72)
    & (combined_df.dropoff_longitude >= -74.09)
    & (combined_df.dropoff_latitude <= 40.88)
    & (combined_df.dropoff_latitude >= 40.53)
]
latlong_filtered_df.reset_index(inplace=True, drop=True)

replaced_stfor_vals_df = latlong_filtered_df.replace(
    {"store_forward": "0"}, {"store_forward": "N"}
).fillna({"store_forward": "N"})

replaced_distance_vals_df = replaced_stfor_vals_df.replace(
    {"distance": ".00"}, {"distance": 0}
).fillna({"distance": 0})

normalized_df = replaced_distance_vals_df.astype({"distance": "float64"})

# Split pickup/dropoff datetime into time-based features (weekday, month, hour, ...)
temp = pd.DatetimeIndex(normalized_df["pickup_datetime"], dtype="datetime64[ns]")
normalized_df["pickup_weekday"] = temp.dayofweek
normalized_df["pickup_month"] = temp.month
normalized_df["pickup_monthday"] = temp.day
normalized_df["pickup_hour"] = temp.hour
normalized_df["pickup_minute"] = temp.minute
normalized_df["pickup_second"] = temp.second

temp = pd.DatetimeIndex(normalized_df["dropoff_datetime"], dtype="datetime64[ns]")
normalized_df["dropoff_weekday"] = temp.dayofweek
normalized_df["dropoff_month"] = temp.month
normalized_df["dropoff_monthday"] = temp.day
normalized_df["dropoff_hour"] = temp.hour
normalized_df["dropoff_minute"] = temp.minute
normalized_df["dropoff_second"] = temp.second

del normalized_df["pickup_datetime"]
del normalized_df["dropoff_datetime"]
normalized_df.reset_index(inplace=True, drop=True)

# store_forward -> binary
normalized_df["store_forward"] = np.where(normalized_df.store_forward == "N", 0, 1)

# Drop abnormal rows: cost/distance must be positive
final_df = normalized_df[(normalized_df.distance > 0) & (normalized_df.cost > 0)]
final_df.reset_index(inplace=True, drop=True)

final_df.to_csv(Path(args.transformed_data) / "transformed_data.csv", index=False)

# Split into train / validation / test sets
random_data = np.random.rand(len(final_df))
msk_train = random_data < 0.7
msk_val = (random_data >= 0.7) & (random_data < 0.85)
msk_test = random_data >= 0.85

train = final_df[msk_train]
val = final_df[msk_val]
test = final_df[msk_test]

run.log("train size", train.shape[0])
run.log("val size", val.shape[0])
run.log("test size", test.shape[0])

train.to_csv(Path(args.transformed_data) / "train.csv", index=False)
val.to_csv(Path(args.transformed_data) / "val.csv", index=False)
test.to_csv(Path(args.transformed_data) / "test.csv", index=False)

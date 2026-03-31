import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from datetime import datetime
from utils.ml_utils import encode_crop, encode_equipment, encode_district

FEATURE_COLUMNS = ["month","day_of_week","crop_type","equipment_type","district_code","rain_chance","temp_c"]
TARGET_COLUMN   = "demand_level"

def preprocess_df(df):
    out = pd.DataFrame()
    if "booking_date" in df.columns:
        dates = pd.to_datetime(df["booking_date"], errors="coerce")
        out["month"]       = dates.dt.month.fillna(datetime.utcnow().month).astype(int)
        out["day_of_week"] = dates.dt.dayofweek.fillna(0).astype(int)
    else:
        out["month"]       = df.get("month", datetime.utcnow().month)
        out["day_of_week"] = df.get("day_of_week", 0)
    out["crop_type"]      = df["crop_type"].apply(lambda x: encode_crop(str(x)))
    out["equipment_type"] = df["equipment_type"].apply(lambda x: encode_equipment(str(x)))
    out["district_code"]  = df.get("district", pd.Series([""]*len(df))).apply(lambda x: encode_district(str(x)))
    out["rain_chance"]    = pd.to_numeric(df.get("rain_chance",20), errors="coerce").fillna(20.0).round(1)
    out["temp_c"]         = pd.to_numeric(df.get("temp_c",28),      errors="coerce").fillna(28.0).round(1)
    if TARGET_COLUMN in df.columns:
        out[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)
    return out

def load_csv(filepath):
    df = pd.read_csv(filepath)
    return preprocess_df(df)

def bookings_to_df(bookings):
    rows = [{"booking_date":b.get("booking_date",datetime.utcnow()),
             "crop_type":b.get("crop_type","other"),
             "equipment_type":b.get("equipment_type","tractor"),
             "district":b.get("district",""),
             "rain_chance":20.0,"temp_c":28.0} for b in bookings]
    return preprocess_df(pd.DataFrame(rows))

def validate_features(features):
    if len(features) != len(FEATURE_COLUMNS): return False
    month,dow,crop,equip,dist,rain,temp = features
    return all([1<=month<=12, 0<=dow<=6, 0<=crop<=5, 0<=equip<=7,
                0<=dist<=19, 0<=rain<=100, 0<=temp<=60])

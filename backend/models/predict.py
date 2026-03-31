import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import joblib
import numpy as np
from datetime import datetime

MODEL_PATH = os.path.join(os.path.dirname(__file__), "demand_model.pkl")
_cache = {}

def _load_model():
    if "meta" not in _cache:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("demand_model.pkl not found. Run: python models/train_model.py")
        _cache["meta"] = joblib.load(MODEL_PATH)
    return _cache["meta"]

def predict_demand(crop_type, equipment_type, booking_date, district="", rain_chance=20.0, temp_c=28.0):
    meta    = _load_model()
    model   = meta["model"]
    c_map   = meta["crop_map"]
    e_map   = meta["equipment_map"]
    l_names = meta["label_names"]

    crop_code     = c_map.get(crop_type.lower(), c_map["other"])
    equip_code    = e_map.get(equipment_type.lower(), 0)
    district_code = abs(hash(district)) % 20

    features = np.array([[booking_date.month, booking_date.weekday(),
                          crop_code, equip_code, district_code,
                          round(rain_chance,1), round(temp_c,1)]])

    proba      = model.predict_proba(features)[0]
    pred_code  = int(np.argmax(proba))
    pred_label = l_names[pred_code]
    confidence = round(float(proba[pred_code]), 3)
    prob_dict  = {l_names[i]: round(float(p), 3) for i, p in enumerate(proba)}
    advice     = {
        2:"🔴 HIGH demand expected. Book immediately and consider group booking to reduce costs.",
        1:"🟡 MODERATE demand. Book in the next 2–3 days to secure your slot.",
        0:"🟢 LOW demand. Flexible scheduling available at normal prices."
    }[pred_code]
    icons = {"High":"🔴","Moderate":"🟡","Low":"🟢"}

    return {"demand_level":pred_label,"demand_code":pred_code,"confidence":confidence,
            "advice":advice,"icon":icons.get(pred_label,""),"probabilities":prob_dict}

def predict_area_demand(district, equipment_type, month=None):
    meta   = _load_model()
    c_map  = meta["crop_map"]
    if month is None:
        month = datetime.utcnow().month
    results = []
    for crop in c_map:
        r = predict_demand(crop, equipment_type,
                           datetime(datetime.utcnow().year, month, 15), district)
        results.append({"crop": crop, **r})
    results.sort(key=lambda x: x["demand_code"], reverse=True)
    return {"district": district, "month": month, "crop_demand": results}

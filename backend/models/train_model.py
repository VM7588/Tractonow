import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

CROP_MAP = {
    "rice": 0, "wheat": 1, "cotton": 2,
    "sugarcane": 3, "maize": 4, "other": 5
}
EQUIPMENT_MAP = {
    "tractor": 0, "harvester": 1, "rotavator": 2,
    "seed_drill": 3, "sprayer": 4, "cultivator": 5,
    "plough": 6, "thresher": 7
}

def generate_synthetic_data(n=3000):
    np.random.seed(42)
    months         = np.random.randint(1, 13, n)
    days_of_week   = np.random.randint(0, 7, n)
    crop_types     = np.random.choice(list(CROP_MAP.keys()), n)
    equip_types    = np.random.choice(list(EQUIPMENT_MAP.keys()), n)
    district_codes = np.random.randint(0, 20, n)
    rain_chance    = np.random.uniform(0, 100, n)
    temp_c         = np.random.uniform(20, 45, n)

    labels = []
    for i in range(n):
        score = 0
        if crop_types[i] == "rice"      and months[i] in [6,7,8,10,11]: score += 3
        if crop_types[i] == "wheat"     and months[i] in [3,4,10,11]:   score += 3
        if crop_types[i] == "cotton"    and months[i] in [6,7,9,10]:    score += 2
        if crop_types[i] == "sugarcane" and months[i] in [1,2,11,12]:   score += 2
        if days_of_week[i] in [0,1,2,3,4]: score += 1
        if rain_chance[i] > 70: score -= 2
        if temp_c[i] > 40:      score -= 1
        labels.append(0 if score <= 1 else 1 if score <= 3 else 2)

    return pd.DataFrame({
        "month": months, "day_of_week": days_of_week,
        "crop_type":      [CROP_MAP[c] for c in crop_types],
        "equipment_type": [EQUIPMENT_MAP[e] for e in equip_types],
        "district_code":  district_codes,
        "rain_chance":    rain_chance.round(1),
        "temp_c":         temp_c.round(1),
        "demand_level":   labels
    })

def train():
    print("🤖 Training demand prediction model...")
    df = generate_synthetic_data(3000)

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    df.to_csv(os.path.join(data_dir, "sample_data.csv"), index=False)
    print(f"  [✓] Sample data saved ({len(df)} rows)")

    X = df.drop("demand_level", axis=1)
    y = df["demand_level"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=150, max_depth=10,
                                   random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n📊 Model Performance:")
    print(classification_report(y_test, y_pred, target_names=["Low","Moderate","High"]))

    model_path = os.path.join(os.path.dirname(__file__), "demand_model.pkl")
    joblib.dump({
        "model": model,
        "crop_map": CROP_MAP,
        "equipment_map": EQUIPMENT_MAP,
        "feature_names": list(X.columns),
        "label_names": {0:"Low", 1:"Moderate", 2:"High"}
    }, model_path)
    print(f"\n✅  Model saved → {model_path}")

if __name__ == "__main__":
    train()

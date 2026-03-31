import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CROP_MAP = {"rice":0,"wheat":1,"cotton":2,"sugarcane":3,"maize":4,"other":5}
EQUIPMENT_MAP = {"tractor":0,"harvester":1,"rotavator":2,"seed_drill":3,"sprayer":4,"cultivator":5,"plough":6,"thresher":7}
DEMAND_LABELS = {0:"Low",1:"Moderate",2:"High"}
DEMAND_COLORS = {"Low":"#22c55e","Moderate":"#f59e0b","High":"#ef4444"}
DEMAND_ICONS  = {"Low":"🟢","Moderate":"🟡","High":"🔴"}

def encode_crop(crop):      return CROP_MAP.get(crop.lower().strip(), CROP_MAP["other"])
def encode_equipment(eq):   return EQUIPMENT_MAP.get(eq.lower().strip(), 0)
def encode_district(dist):  return abs(hash(dist.strip().lower())) % 20

def build_feature_vector(crop_type, equipment_type, month, day_of_week, district="", rain_chance=20.0, temp_c=28.0):
    return [month, day_of_week, encode_crop(crop_type), encode_equipment(equipment_type),
            encode_district(district), round(float(rain_chance),1), round(float(temp_c),1)]

def format_prediction(pred_code, confidence, probabilities):
    label  = DEMAND_LABELS[pred_code]
    advice = {2:"🔴 HIGH demand. Book immediately and consider group booking.",
              1:"🟡 MODERATE demand. Book in the next 2–3 days.",
              0:"🟢 LOW demand. Flexible scheduling at normal prices."}[pred_code]
    return {"demand_level":label,"demand_code":pred_code,"confidence":round(confidence,3),
            "advice":advice,"color":DEMAND_COLORS[label],"icon":DEMAND_ICONS[label],"probabilities":probabilities}

CROP_SEASONS = {
    "rice":      {"sowing":[6,7],   "harvest":[10,11]},
    "wheat":     {"sowing":[10,11], "harvest":[3,4]},
    "cotton":    {"sowing":[6,7],   "harvest":[9,10]},
    "sugarcane": {"sowing":[1,2],   "harvest":[11,12]},
    "maize":     {"sowing":[6,7],   "harvest":[9,10]},
}

def get_season_info(crop, month):
    seasons = CROP_SEASONS.get(crop.lower(), {})
    if month in seasons.get("harvest",[]): return {"season":"harvest","label":"🌾 Harvest Season","peak":True}
    if month in seasons.get("sowing",[]):  return {"season":"sowing", "label":"🌱 Sowing Season", "peak":True}
    return {"season":"off","label":"😴 Off Season","peak":False}

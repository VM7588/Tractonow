import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from utils.auth import token_required
from utils.weather import get_weather, get_forecast, farming_suggestion
from database.db import users_col
from bson import ObjectId

weather_bp = Blueprint("weather", __name__)

DISTRICT_COORDS = {
    "Bhadradri Kothagudem":(17.5524,80.6194),"Warangal":(18.0000,79.5800),
    "Khammam":(17.2473,80.1514),"Nalgonda":(17.0575,79.2673),
    "Karimnagar":(18.4386,79.1288),"Adilabad":(19.6640,78.5320),
    "Nizamabad":(18.6725,78.0940),"Hyderabad":(17.3850,78.4867),
    "Kurnool":(15.8281,78.0373),"Guntur":(16.3067,80.4365),
    "Vijayawada":(16.5062,80.6480),"Visakhapatnam":(17.6868,83.2185),
    "Tirupati":(13.6288,79.4192),"Anantapur":(14.6819,77.6006),
}

@weather_bp.route("/forecast", methods=["GET"])
@token_required
def forecast():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    if not lat or not lng:
        user     = users_col.find_one({"_id":ObjectId(request.user_id)})
        district = user.get("district","") if user else ""
        lat, lng = DISTRICT_COORDS.get(district, (17.3850, 78.4867))
    else:
        lat, lng = float(lat), float(lng)

    current  = get_weather(lat, lng)
    forecast = get_forecast(lat, lng, days=5)
    advice   = farming_suggestion(current)

    daily = {}
    for f in forecast.get("forecasts",[]):
        day = f["datetime"][:10]
        if day not in daily: daily[day] = {"temps":[],"conditions":[],"rain_mm":0}
        daily[day]["temps"].append(f["temp_c"])
        daily[day]["conditions"].append(f["condition"])
        daily[day]["rain_mm"] += f.get("rain_mm",0)

    icons_map = {"Rain":"🌧️","Thunderstorm":"⛈️","Drizzle":"🌦️","Clouds":"⛅","Clear":"☀️","Mist":"🌫️","Snow":"❄️"}
    daily_summary = []
    for day,d in list(daily.items())[:5]:
        conds     = d["conditions"]
        main_cond = max(set(conds), key=conds.count)
        daily_summary.append({
            "date":day,"min_temp":round(min(d["temps"]),1),"max_temp":round(max(d["temps"]),1),
            "condition":main_cond,"icon":icons_map.get(main_cond,"🌤️"),
            "rain_mm":round(d["rain_mm"],1),
            "safe":"rain" not in main_cond.lower() and "thunderstorm" not in main_cond.lower()
        })
    return jsonify({"success":True,"current":current,"advice":advice,"daily_forecast":daily_summary})

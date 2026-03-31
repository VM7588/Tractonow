import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from config import Config

BASE_URL = "https://api.openweathermap.org/data/2.5"

def get_weather(lat: float, lon: float) -> dict:
    if not Config.OPENWEATHER_KEY:
        return _mock_weather()
    try:
        resp = requests.get(f"{BASE_URL}/weather",
            params={"lat":lat,"lon":lon,"appid":Config.OPENWEATHER_KEY,"units":"metric"},
            timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "temp_c":      data["main"]["temp"],
            "humidity":    data["main"]["humidity"],
            "condition":   data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_kph":    round(data["wind"]["speed"] * 3.6, 1),
            "city":        data.get("name", "")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_forecast(lat, lon, days=5):
    if not Config.OPENWEATHER_KEY:
        return _mock_forecast()
    try:
        resp = requests.get(f"{BASE_URL}/forecast",
            params={"lat":lat,"lon":lon,"appid":Config.OPENWEATHER_KEY,"units":"metric","cnt":days*8},
            timeout=5)
        resp.raise_for_status()
        raw = resp.json()
        forecasts = [{"datetime":item["dt_txt"],"temp_c":item["main"]["temp"],
                      "condition":item["weather"][0]["main"],"description":item["weather"][0]["description"],
                      "rain_mm":item.get("rain",{}).get("3h",0)} for item in raw["list"]]
        return {"success": True, "forecasts": forecasts}
    except Exception as e:
        return {"success": False, "error": str(e)}

def farming_suggestion(weather: dict) -> dict:
    if not weather.get("success"):
        return {"suggestion":"Unable to fetch weather. Proceed with caution.","safe_to_operate":True}
    cond    = weather.get("condition","").lower()
    temp    = weather.get("temp_c", 25)
    humidity= weather.get("humidity", 50)
    wind    = weather.get("wind_kph", 0)
    if "rain" in cond or "thunderstorm" in cond or "drizzle" in cond:
        return {"suggestion":"🌧️ Rain detected — delay field operations.","safe_to_operate":False,"alert_type":"rain"}
    if wind > 40:
        return {"suggestion":"💨 High winds — avoid spraying pesticides.","safe_to_operate":False,"alert_type":"wind"}
    if temp > 42:
        return {"suggestion":"🌡️ Extreme heat — schedule early morning.","safe_to_operate":True,"alert_type":"heat"}
    if humidity > 85:
        return {"suggestion":"💧 High humidity — monitor for fungal diseases.","safe_to_operate":True,"alert_type":"humidity"}
    return {"suggestion":"✅ Weather is suitable for field operations.","safe_to_operate":True,"alert_type":"none"}

def _mock_weather():
    return {"success":True,"temp_c":28,"humidity":65,"condition":"Clear","description":"clear sky","wind_kph":12,"city":"Yellandu"}

def _mock_forecast():
    return {"success":True,"forecasts":[
        {"datetime":"2024-06-10 06:00:00","temp_c":27,"condition":"Clouds","description":"scattered clouds","rain_mm":0},
        {"datetime":"2024-06-11 06:00:00","temp_c":25,"condition":"Rain","description":"light rain","rain_mm":2.4}
    ]}

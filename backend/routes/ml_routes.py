import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, request, jsonify
from database.db import ml_logs_col
from utils.auth import token_required
from utils.weather import get_weather, farming_suggestion
from utils.pricing import suggest_best_time
from models.predict import predict_demand, predict_area_demand
from datetime import datetime
from dateutil import parser as date_parser

ml_bp = Blueprint("ml", __name__)

# ── Predict Demand ────────────────────────────────────────────────────────────
@ml_bp.route("/predict", methods=["POST"])
@token_required
def predict():
    data = request.get_json()
    required = ["crop_type", "equipment_type", "booking_date"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing: {', '.join(missing)}"}), 400

    try:
        booking_date = date_parser.parse(data["booking_date"])
    except Exception:
        return jsonify({"success": False, "message": "Invalid booking_date format"}), 400

    lat     = float(data.get("lat", 17.58))
    lng     = float(data.get("lng", 80.64))
    weather = get_weather(lat, lng)

    result      = predict_demand(
        crop_type      = data["crop_type"],
        equipment_type = data["equipment_type"],
        booking_date   = booking_date,
        district       = data.get("district", ""),
        rain_chance    = weather.get("humidity", 20),
        temp_c         = weather.get("temp_c", 28)
    )
    pricing_tip = suggest_best_time(data["crop_type"], data.get("district", ""))
    weather_tip = farming_suggestion(weather)

    # Log to MongoDB
    ml_logs_col.insert_one({
        "user_id":        request.user_id,
        "crop_type":      data["crop_type"],
        "equipment_type": data["equipment_type"],
        "booking_date":   booking_date,
        "demand_level":   result["demand_level"],
        "confidence":     result["confidence"],
        "timestamp":      datetime.utcnow()
    })

    return jsonify({
        "success":     True,
        "prediction":  result,
        "pricing_tip": pricing_tip,
        "weather_tip": weather_tip
    })

# ── Area Demand Heatmap ───────────────────────────────────────────────────────
@ml_bp.route("/area-demand", methods=["GET"])
@token_required
def area_demand():
    district       = request.args.get("district", "Bhadradri Kothagudem")
    equipment_type = request.args.get("equipment_type", "tractor")
    month_str      = request.args.get("month")
    month          = int(month_str) if month_str else None
    result         = predict_area_demand(district, equipment_type, month)
    return jsonify({"success": True, **result})

# ── Weather + Farming Advice ──────────────────────────────────────────────────
@ml_bp.route("/weather-advice", methods=["GET"])
@token_required
def weather_advice():
    lat     = float(request.args.get("lat", 17.58))
    lng     = float(request.args.get("lng", 80.64))
    weather = get_weather(lat, lng)
    advice  = farming_suggestion(weather)
    return jsonify({"success": True, "weather": weather, "advice": advice})

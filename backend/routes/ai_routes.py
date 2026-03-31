import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from utils.auth import token_required
from models.predict import predict_area_demand
from database.db import bookings_col
from datetime import datetime

ai_bp = Blueprint("ai", __name__)

SEASONAL_DEMAND = {
    1: {"sugarcane":"High","wheat":"High","rice":"Low","cotton":"Low","maize":"Low"},
    2: {"sugarcane":"High","wheat":"Moderate","rice":"Low","cotton":"Low","maize":"Low"},
    3: {"wheat":"High","sugarcane":"Moderate","rice":"Low","cotton":"Low","maize":"Low"},
    4: {"wheat":"High","rice":"Low","cotton":"Low","sugarcane":"Low","maize":"Low"},
    5: {"rice":"Moderate","cotton":"Moderate","maize":"Moderate","wheat":"Low","sugarcane":"Low"},
    6: {"rice":"High","cotton":"High","maize":"High","wheat":"Low","sugarcane":"Low"},
    7: {"rice":"High","cotton":"High","maize":"Moderate","wheat":"Low","sugarcane":"Low"},
    8: {"rice":"High","cotton":"Moderate","maize":"Moderate","wheat":"Low","sugarcane":"Low"},
    9: {"cotton":"High","maize":"High","rice":"Moderate","wheat":"Moderate","sugarcane":"Low"},
    10:{"rice":"High","cotton":"High","maize":"Moderate","wheat":"High","sugarcane":"Low"},
    11:{"rice":"High","wheat":"High","sugarcane":"High","cotton":"Moderate","maize":"Low"},
    12:{"wheat":"High","sugarcane":"High","rice":"Low","cotton":"Low","maize":"Low"},
}
CROP_ADVICE = {
    "rice":"🌾 Rice needs tractors for transplanting & harvesters for cutting. Book 2 weeks early.",
    "wheat":"🌿 Wheat season — rotavators for land prep, harvesters for cutting are in high demand.",
    "cotton":"🌸 Cotton needs sprayers for pest control and tractors. Group booking recommended.",
    "sugarcane":"🎋 Sugarcane harvest needs heavy tractors. Book well in advance.",
    "maize":"🌽 Maize season — threshers and tractors most needed.",
}
EQUIPMENT_FOR = {
    "rice":["tractor","harvester","rotavator"],"wheat":["tractor","harvester","seed_drill"],
    "cotton":["tractor","sprayer","seed_drill"],"sugarcane":["tractor","plough"],
    "maize":["tractor","thresher","seed_drill"],
}
ICONS = {"High":"🔴","Moderate":"🟡","Low":"🟢"}
COLORS= {"High":"#ef4444","Moderate":"#f59e0b","Low":"#22c55e"}
MONTH_NAMES=["","January","February","March","April","May","June","July","August","September","October","November","December"]

@ai_bp.route("/crop-demand", methods=["GET"])
@token_required
def crop_demand():
    month    = int(request.args.get("month", datetime.utcnow().month))
    district = request.args.get("district","")
    seasonal = SEASONAL_DEMAND.get(month,{})
    # Enrich with real booking data
    pipeline = [{"$group":{"_id":"$crop_type","count":{"$sum":1}}},{"$sort":{"count":-1}}]
    real_counts = {r["_id"]:r["count"] for r in bookings_col.aggregate(pipeline)}
    score_map   = {"High":3,"Moderate":2,"Low":1}
    combined    = []
    for crop in ["rice","wheat","cotton","sugarcane","maize"]:
        s_level  = seasonal.get(crop,"Low")
        s_score  = score_map[s_level]
        # Boost if real bookings exist
        if real_counts.get(crop,0) > 5: s_score = min(3, s_score+1)
        final = {3:"High",2:"Moderate",1:"Low"}[s_score]
        combined.append({
            "crop":crop,"demand":final,"icon":ICONS[final],"color":COLORS[final],
            "confidence":0.85 if real_counts.get(crop,0)>0 else 0.70,
            "advice":CROP_ADVICE.get(crop,""),"equipment_needed":EQUIPMENT_FOR.get(crop,[]),
            "real_bookings":real_counts.get(crop,0)
        })
    combined.sort(key=lambda x:score_map[x["demand"]],reverse=True)
    top = combined[0] if combined else {}
    return jsonify({
        "success":True,"month":month,"month_name":MONTH_NAMES[month],
        "top_crop":top,"all_crops":combined,
        "tip":f"🤖 AI Tip: {top.get('crop','').capitalize()} has highest demand this month. {top.get('advice','')}"
    })

@ai_bp.route("/smart-suggestion", methods=["POST"])
@token_required
def smart_suggestion():
    data  = request.get_json()
    crop  = data.get("crop_type","rice")
    month = datetime.utcnow().month
    level = SEASONAL_DEMAND.get(month,{}).get(crop,"Low")
    mult  = {"High":1.6,"Moderate":1.3,"Low":1.0}[level]
    cheaper = [MONTH_NAMES[m] for m in range(1,13)
               if SEASONAL_DEMAND.get(m,{}).get(crop,"Low")=="Low" and m!=month]
    return jsonify({
        "success":True,"crop":crop,"current_demand":level,"price_multiplier":mult,
        "estimated_cost":f"₹{int(350*mult*4)}/day (4 hrs)",
        "cheaper_months":cheaper[:3],"book_now":level=="High",
        "suggestion":{"High":"📢 Book immediately! High demand = higher prices.",
                      "Moderate":"✅ Good time. Moderate demand, book soon.",
                      "Low":"😊 Low demand — flexible schedule & normal prices."}[level]
    })

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from database.db import users_col, bookings_col
from utils.auth import token_required
from datetime import datetime
from bson import ObjectId

notification_bp = Blueprint("notifications", __name__)

SEASON_ALERTS = {
    1: [("sugarcane","harvest","🎋 Sugarcane harvest season! Book heavy tractors early.","warning"),
        ("wheat","sowing","🌿 Wheat sowing begins. Prepare seed drills.","info")],
    2: [("sugarcane","harvest","🎋 Peak sugarcane harvest. High tractor demand.","warning"),
        ("wheat","sowing","🌿 Wheat sowing continues. Book rotavators.","info")],
    3: [("wheat","harvest","🌾 Wheat harvest season! Harvesters in high demand. Book NOW!","warning")],
    4: [("wheat","harvest","🌾 Wheat harvest peak. Avoid afternoon field operations — extreme heat.","warning")],
    5: [("rice","sowing","🌾 Pre-monsoon rice prep. Book tractors for land prep.","info"),
        ("cotton","sowing","🌸 Cotton sowing starts. Seed drills needed.","info")],
    6: [("rice","sowing","🌾 Monsoon arrived! Rice & cotton sowing season. PEAK DEMAND!","warning"),
        ("cotton","sowing","🌸 Cotton sowing peak. Sprayers in high demand.","warning")],
    7: [("rice","transplanting","🌾 Rice transplanting peak. Highest tractor demand of year!","warning"),
        ("maize","sowing","🌽 Maize sowing season. Book equipment early.","info")],
    8: [("rice","care","🌾 Rice crop care. Sprayers needed for pest control.","info")],
    9: [("cotton","harvest","🌸 Cotton harvest starts. Pickers & tractors needed.","info"),
        ("maize","harvest","🌽 Maize harvest begins. Book threshers.","info")],
    10:[("rice","harvest","🌾 RICE HARVEST! Highest demand month of the year. Book immediately!","warning"),
        ("cotton","harvest","🌸 Cotton harvest peak. High demand continues.","warning"),
        ("wheat","sowing","🌿 Wheat sowing starts. Book seed drills.","info")],
    11:[("rice","harvest","🌾 Late rice harvest. Harvesters still in demand.","info"),
        ("wheat","sowing","🌿 Peak wheat sowing. Rotavators & tractors needed.","warning"),
        ("sugarcane","harvest","🎋 Sugarcane harvest begins. Heavy tractors needed.","info")],
    12:[("wheat","growth","🌿 Wheat growing. Irrigate regularly.","info"),
        ("sugarcane","harvest","🎋 Sugarcane harvest peak. High demand.","warning")],
}

@notification_bp.route("/", methods=["GET"])
@token_required
def get_notifications():
    user  = users_col.find_one({"_id":ObjectId(request.user_id)})
    if not user: return jsonify({"success":False,"message":"User not found"}),404
    month = datetime.utcnow().month
    notes = []

    # Season alerts
    for crop, activity, msg, ntype in SEASON_ALERTS.get(month, []):
        notes.append({"id":f"{crop}_{activity}_{month}","title":f"{crop.capitalize()} Alert",
                       "message":msg,"type":ntype,"crop":crop,"read":False,
                       "created_at":datetime.utcnow().isoformat()})

    # Upcoming booking reminders
    upcoming = list(bookings_col.find({
        "farmer_id":str(user["_id"]),
        "status":{"$in":["confirmed","pending"]},
        "booking_date":{"$gte":datetime.utcnow()}
    }).limit(3))
    for b in upcoming:
        notes.append({"id":f"booking_{str(b['_id'])}",
                       "title":"📅 Upcoming Booking",
                       "message":f"{b.get('crop_type','').capitalize()} booking on {str(b.get('booking_date',''))[:10]}.",
                       "type":"success","read":False,"created_at":datetime.utcnow().isoformat()})

    # Cancellation window alerts
    conf_bookings = list(bookings_col.find({
        "farmer_id":str(user["_id"]),"status":"confirmed",
        "cancel_deadline":{"$gte":datetime.utcnow()}
    }))
    for b in conf_bookings:
        secs = max(0,int((b["cancel_deadline"] - datetime.utcnow()).total_seconds()))
        if secs > 0:
            notes.insert(0,{"id":f"cancel_{str(b['_id'])}",
                "title":"⏰ Cancellation Window Open",
                "message":f"You can cancel booking #{str(b['_id'])[-6:]} for {secs//60}m {secs%60}s more.",
                "type":"warning","read":False,"created_at":datetime.utcnow().isoformat()})

    return jsonify({"success":True,"count":len(notes),"unread":len(notes),"notifications":notes})

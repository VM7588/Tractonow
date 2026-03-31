import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from database.db import bookings_col, equipment_col, users_col
from utils.auth import token_required, farmer_required, owner_required
from utils.pricing import calculate_price
from config import Config
from datetime import datetime, timedelta
from bson import ObjectId
from dateutil import parser as date_parser

booking_bp = Blueprint("booking", __name__)

def _s(b):
    accepted_at      = b.get("accepted_at")
    cancel_deadline  = b.get("cancel_deadline")
    can_cancel       = False
    secs_remaining   = 0
    if b.get("status") == "confirmed" and cancel_deadline:
        secs_remaining = max(0, int((cancel_deadline - datetime.utcnow()).total_seconds()))
        can_cancel = secs_remaining > 0
    elif b.get("status") == "pending":
        can_cancel = True
    return {
        "id":str(b["_id"]),"farmer_id":b["farmer_id"],"equipment_id":b["equipment_id"],
        "owner_id":b.get("owner_id",""),"crop_type":b.get("crop_type",""),
        "booking_date":str(b.get("booking_date","")),"hours_required":b.get("hours_required",1),
        "total_price":b.get("total_price",0),"price_breakdown":b.get("price_breakdown",{}),
        "status":b.get("status","pending"),"payment_status":b.get("payment_status","unpaid"),
        "payment_txn_id":b.get("payment_txn_id",""),"district":b.get("district",""),
        "mandal":b.get("mandal",""),"village":b.get("village",""),"notes":b.get("notes",""),
        "can_cancel":can_cancel,"cancel_seconds_remaining":secs_remaining,
        "created_at":str(b.get("created_at",""))
    }

@booking_bp.route("/", methods=["POST"])
@farmer_required
def create_booking():
    data = request.get_json()
    required = ["equipment_id","crop_type","booking_date","hours_required"]
    missing  = [f for f in required if not data.get(f)]
    if missing: return jsonify({"success":False,"message":f"Missing: {', '.join(missing)}"}),400
    try: eq = equipment_col.find_one({"_id":ObjectId(data["equipment_id"])})
    except: return jsonify({"success":False,"message":"Invalid equipment ID"}),400
    if not eq: return jsonify({"success":False,"message":"Equipment not found"}),404
    if not eq.get("availability",True): return jsonify({"success":False,"message":"Not available"}),409
    booking_date = date_parser.parse(data["booking_date"])
    hours        = int(data["hours_required"])
    breakdown    = calculate_price(eq["price_per_hour"],hours,data["crop_type"],booking_date)
    farmer       = users_col.find_one({"_id":ObjectId(request.user_id)})
    booking = {
        "farmer_id":request.user_id,"equipment_id":data["equipment_id"],
        "owner_id":eq["owner_id"],"crop_type":data["crop_type"],
        "booking_date":booking_date,"hours_required":hours,
        "total_price":breakdown["gross_total"],"price_breakdown":breakdown,
        "status":"pending","payment_status":"unpaid",
        "district":farmer.get("district","") if farmer else "",
        "mandal":farmer.get("mandal","") if farmer else "",
        "village":farmer.get("village","") if farmer else "",
        "notes":data.get("notes",""),"created_at":datetime.utcnow()
    }
    result = bookings_col.insert_one(booking)
    return jsonify({"success":True,"message":"Booking created",
                    "booking_id":str(result.inserted_id),"price_breakdown":breakdown}),201

@booking_bp.route("/my", methods=["GET"])
@farmer_required
def my_bookings():
    rows = list(bookings_col.find({"farmer_id":request.user_id}).sort("created_at",-1))
    return jsonify({"success":True,"bookings":[_s(b) for b in rows]})

@booking_bp.route("/incoming", methods=["GET"])
@owner_required
def incoming_bookings():
    rows = list(bookings_col.find({"owner_id":request.user_id}).sort("created_at",-1))
    return jsonify({"success":True,"bookings":[_s(b) for b in rows]})

@booking_bp.route("/<booking_id>", methods=["GET"])
@token_required
def get_booking(booking_id):
    try: b = bookings_col.find_one({"_id":ObjectId(booking_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not b: return jsonify({"success":False,"message":"Not found"}),404
    if b["farmer_id"] != request.user_id and b.get("owner_id") != request.user_id:
        return jsonify({"success":False,"message":"Forbidden"}),403
    return jsonify({"success":True,"booking":_s(b)})

@booking_bp.route("/<booking_id>/status", methods=["PUT"])
@owner_required
def update_status(booking_id):
    status = request.get_json().get("status")
    if status not in Config.BOOKING_STATUS:
        return jsonify({"success":False,"message":"Invalid status"}),400
    try: b = bookings_col.find_one({"_id":ObjectId(booking_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not b: return jsonify({"success":False,"message":"Not found"}),404
    if b.get("owner_id") != request.user_id: return jsonify({"success":False,"message":"Forbidden"}),403
    updates = {"status":status,"updated_at":datetime.utcnow()}
    if status == "confirmed":
        updates["accepted_at"]     = datetime.utcnow()
        updates["cancel_deadline"] = datetime.utcnow() + timedelta(minutes=10)
    bookings_col.update_one({"_id":ObjectId(booking_id)},{"$set":updates})
    msg = f"Status updated to {status}"
    if status == "confirmed":
        msg += " — Farmer has 10 minutes to cancel."
    return jsonify({"success":True,"message":msg})

@booking_bp.route("/<booking_id>/cancel", methods=["PUT"])
@farmer_required
def cancel_booking(booking_id):
    try: b = bookings_col.find_one({"_id":ObjectId(booking_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not b: return jsonify({"success":False,"message":"Not found"}),404
    if b["farmer_id"] != request.user_id: return jsonify({"success":False,"message":"Forbidden"}),403
    if b["status"] in ("completed","in_progress","cancelled"):
        return jsonify({"success":False,"message":"Cannot cancel this booking"}),409
    if b["status"] == "confirmed":
        deadline = b.get("cancel_deadline")
        if deadline and datetime.utcnow() > deadline:
            return jsonify({"success":False,
                "message":"⏰ 10-minute cancellation window has expired. Cannot cancel."}),409
    bookings_col.update_one({"_id":ObjectId(booking_id)},{"$set":{"status":"cancelled"}})
    return jsonify({"success":True,"message":"Booking cancelled successfully"})

@booking_bp.route("/stats/demand", methods=["GET"])
@token_required
def demand_stats():
    pipeline = [{"$group":{"_id":"$crop_type","count":{"$sum":1},
                            "revenue":{"$sum":"$total_price"}}},{"$sort":{"count":-1}}]
    stats = list(bookings_col.aggregate(pipeline))
    total = sum(s["count"] for s in stats) or 1
    return jsonify({"success":True,"demand_stats":[
        {"crop":s["_id"],"bookings":s["count"],
         "revenue":round(s["revenue"],2),
         "percent":round(s["count"]/total*100,1)} for s in stats
    ]})

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from database.db import group_col, equipment_col, users_col
from utils.auth import token_required, farmer_required
from utils.pricing import calculate_price
from config import Config
from datetime import datetime
from bson import ObjectId
from dateutil import parser as date_parser

group_bp = Blueprint("group", __name__)

def _member_details(member_ids):
    details = []
    for mid in member_ids:
        try:
            u = users_col.find_one({"_id": ObjectId(mid)})
            if u:
                details.append({"id": str(u["_id"]), "name": u["name"],
                                 "village": u.get("village",""), "district": u.get("district","")})
        except: pass
    return details

def _s(g):
    members     = g.get("members", [])
    member_det  = _member_details(members)
    return {
        "id": str(g["_id"]), "creator_id": g["creator_id"],
        "group_name": g.get("group_name", ""),
        "equipment_id": g["equipment_id"], "equipment_type": g.get("equipment_type",""),
        "crop_type": g.get("crop_type",""), "booking_date": str(g.get("booking_date","")),
        "hours_required": g.get("hours_required",1), "district": g.get("district",""),
        "village": g.get("village",""), "mandal": g.get("mandal",""),
        "max_farmers": g.get("max_farmers", Config.MAX_GROUP_SIZE),
        "members": members, "member_details": member_det,
        "member_count": len(members),
        "base_price": g.get("base_price",0), "per_farmer_share": g.get("per_farmer_share",0),
        "status": g.get("status","open"), "created_at": str(g.get("created_at",""))
    }

# ── Create Group ──────────────────────────────────────────────────────────────
@group_bp.route("/", methods=["POST"])
@farmer_required
def create_group():
    data = request.get_json()
    required = ["equipment_id","crop_type","booking_date","hours_required"]
    missing  = [f for f in required if not data.get(f)]
    if missing: return jsonify({"success":False,"message":f"Missing: {', '.join(missing)}"}),400
    try: eq = equipment_col.find_one({"_id":ObjectId(data["equipment_id"])})
    except: return jsonify({"success":False,"message":"Invalid equipment ID"}),400
    if not eq: return jsonify({"success":False,"message":"Equipment not found"}),404
    booking_date = date_parser.parse(data["booking_date"])
    hours        = int(data["hours_required"])
    max_farmers  = min(int(data.get("max_farmers", Config.MAX_GROUP_SIZE)), Config.MAX_GROUP_SIZE)
    breakdown    = calculate_price(eq["price_per_hour"],hours,data["crop_type"],booking_date,group_size=max_farmers)
    farmer       = users_col.find_one({"_id":ObjectId(request.user_id)})
    gid = ObjectId()
    group = {
        "_id": gid,
        "group_name": data.get("group_name","").strip() or f"Group-{str(gid)[-6:]}",
        "creator_id": request.user_id, "equipment_id": data["equipment_id"],
        "equipment_type": eq["type"], "crop_type": data["crop_type"],
        "booking_date": booking_date, "hours_required": hours,
        "district": farmer.get("district","") if farmer else "",
        "mandal":   farmer.get("mandal","")   if farmer else "",
        "village":  farmer.get("village","")  if farmer else "",
        "max_farmers": max_farmers, "members": [request.user_id],
        "base_price": breakdown["gross_total"],
        "per_farmer_share": breakdown["per_farmer_share"],
        "status": "open", "created_at": datetime.utcnow()
    }
    group_col.insert_one(group)
    join_link = f"/group-booking?join={str(gid)}"
    return jsonify({
        "success":True, "message":"Group created! Share the link to invite farmers.",
        "group_id": str(gid), "join_link": join_link,
        "per_farmer": breakdown["per_farmer_share"], "max_farmers": max_farmers
    }), 201

# ── List Open Groups ──────────────────────────────────────────────────────────
@group_bp.route("/open", methods=["GET"])
@token_required
def open_groups():
    query = {"status":{"$in":["open","full"]}}
    if d := request.args.get("district"): query["district"] = {"$regex":d,"$options":"i"}
    groups = list(group_col.find(query).sort("booking_date",1))
    return jsonify({"success":True,"groups":[_s(g) for g in groups]})

# ── Get Single Group ──────────────────────────────────────────────────────────
@group_bp.route("/<group_id>", methods=["GET"])
@token_required
def get_group(group_id):
    try: g = group_col.find_one({"_id":ObjectId(group_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not g: return jsonify({"success":False,"message":"Not found"}),404
    return jsonify({"success":True,"group":_s(g)})

# ── Join Group ────────────────────────────────────────────────────────────────
@group_bp.route("/<group_id>/join", methods=["POST"])
@farmer_required
def join_group(group_id):
    try: g = group_col.find_one({"_id":ObjectId(group_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not g: return jsonify({"success":False,"message":"Group not found"}),404
    if g["status"] not in ("open",): return jsonify({"success":False,"message":"Group is not open for joining"}),409
    if request.user_id in g["members"]: return jsonify({"success":False,"message":"Already a member"}),409
    if len(g["members"]) >= g["max_farmers"]: return jsonify({"success":False,"message":"Group is full"}),409
    new_members   = g["members"] + [request.user_id]
    new_share     = round(g["base_price"]/len(new_members),2)
    new_status    = "full" if len(new_members) >= g["max_farmers"] else "open"
    group_col.update_one({"_id":ObjectId(group_id)},
        {"$set":{"members":new_members,"per_farmer_share":new_share,"status":new_status}})
    return jsonify({"success":True,"message":"Joined group successfully!",
                    "your_share":new_share,"total_members":len(new_members)})

# ── Leave Group (anytime) ─────────────────────────────────────────────────────
@group_bp.route("/<group_id>/leave", methods=["POST"])
@farmer_required
def leave_group(group_id):
    try: g = group_col.find_one({"_id":ObjectId(group_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not g: return jsonify({"success":False,"message":"Group not found"}),404
    if request.user_id not in g["members"]: return jsonify({"success":False,"message":"Not a member"}),409
    if g["creator_id"] == request.user_id:
        return jsonify({"success":False,"message":"Creator cannot leave. Cancel the group instead."}),409
    new_members = [m for m in g["members"] if m != request.user_id]
    new_share   = round(g["base_price"]/len(new_members),2) if new_members else 0
    group_col.update_one({"_id":ObjectId(group_id)},
        {"$set":{"members":new_members,"per_farmer_share":new_share,"status":"open"}})
    return jsonify({"success":True,"message":"Left the group."})

# ── Cancel Group (creator only) ───────────────────────────────────────────────
@group_bp.route("/<group_id>/cancel", methods=["POST"])
@farmer_required
def cancel_group(group_id):
    try: g = group_col.find_one({"_id":ObjectId(group_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not g: return jsonify({"success":False,"message":"Not found"}),404
    if g["creator_id"] != request.user_id: return jsonify({"success":False,"message":"Only creator can cancel"}),403
    group_col.update_one({"_id":ObjectId(group_id)},{"$set":{"status":"cancelled"}})
    return jsonify({"success":True,"message":"Group cancelled."})

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from database.db import equipment_col, ratings_col
from utils.auth import token_required, owner_required
from config import Config
from datetime import datetime
from bson import ObjectId
import base64, os as _os

equipment_bp = Blueprint("equipment", __name__)

def _s(eq):
    ratings = list(ratings_col.find({"equipment_id":str(eq["_id"])}))
    loc     = eq.get("location",{})
    return {
        "id":str(eq["_id"]),"name":eq["name"],"type":eq["type"],
        "brand":eq.get("brand",""),"model":eq.get("model",""),"hp":eq.get("hp",0),
        "price_per_hour":eq["price_per_hour"],"owner_id":eq["owner_id"],
        "location":loc,"availability":eq.get("availability",True),
        "description":eq.get("description",""),"image_url":eq.get("image_url",""),
        "avg_rating":round(sum(r["rating"] for r in ratings)/len(ratings),1) if ratings else 0,
        "total_ratings":len(ratings),"created_at":str(eq.get("created_at",""))
    }

def _save_image(data_field, ext_field="jpg"):
    """Save base64 image to disk, return URL."""
    img_data = data_field
    if "," in img_data: img_data = img_data.split(",",1)[1]
    img_dir  = _os.path.join(_os.path.dirname(__file__),"../../frontend/static/images/equipment")
    _os.makedirs(img_dir, exist_ok=True)
    fname = f"{str(ObjectId())}.{ext_field}"
    fpath = _os.path.join(img_dir, fname)
    with open(fpath, "wb") as f:
        f.write(base64.b64decode(img_data))
    return f"/static/images/equipment/{fname}"

@equipment_bp.route("/", methods=["GET"])
def list_equipment():
    query = {}
    if t := request.args.get("type"):     query["type"] = t
    if v := request.args.get("village"):  query["location.village"]  = {"$regex":v,"$options":"i"}
    if m := request.args.get("mandal"):   query["location.mandal"]   = {"$regex":m,"$options":"i"}
    if d := request.args.get("district"): query["location.district"] = {"$regex":d,"$options":"i"}
    if s := request.args.get("state"):    query["location.state"]    = {"$regex":s,"$options":"i"}
    if request.args.get("available") == "true": query["availability"] = True
    items = list(equipment_col.find(query))
    return jsonify({"success":True,"equipment":[_s(e) for e in items],"count":len(items)})

@equipment_bp.route("/<eq_id>", methods=["GET"])
def get_equipment(eq_id):
    try: eq = equipment_col.find_one({"_id":ObjectId(eq_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not eq: return jsonify({"success":False,"message":"Not found"}),404
    return jsonify({"success":True,"equipment":_s(eq)})

@equipment_bp.route("/", methods=["POST"])
@owner_required
def add_equipment():
    data    = request.get_json()
    required = ["name","type","price_per_hour"]
    missing  = [f for f in required if not data.get(f)]
    if missing: return jsonify({"success":False,"message":f"Missing: {', '.join(missing)}"}),400
    if data["type"] not in Config.EQUIPMENT_TYPES:
        return jsonify({"success":False,"message":f"Invalid type. Choose: {Config.EQUIPMENT_TYPES}"}),400
    image_url = data.get("image_url","")
    if data.get("image_base64"):
        try:
            ext = data.get("image_ext","jpg").lower().replace(".","")
            image_url = _save_image(data["image_base64"], ext)
        except Exception as e:
            return jsonify({"success":False,"message":f"Image upload failed: {e}"}),400
    eq = {
        "name":data["name"],"type":data["type"],
        "brand":data.get("brand",""),"model":data.get("model",""),
        "hp":int(data.get("hp",0)),"price_per_hour":float(data["price_per_hour"]),
        "owner_id":request.user_id,
        "location":{
            "village":data.get("village",""),"mandal":data.get("mandal",""),
            "district":data.get("district",""),"state":data.get("state","Telangana"),
            "lat":float(data.get("lat",0)),"lng":float(data.get("lng",0))
        },
        "availability":True,"description":data.get("description",""),
        "image_url":image_url,"created_at":datetime.utcnow()
    }
    result = equipment_col.insert_one(eq)
    return jsonify({"success":True,"message":"Equipment added successfully!","id":str(result.inserted_id)}),201

@equipment_bp.route("/<eq_id>", methods=["PUT"])
@owner_required
def update_equipment(eq_id):
    try: eq = equipment_col.find_one({"_id":ObjectId(eq_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not eq: return jsonify({"success":False,"message":"Not found"}),404
    if eq["owner_id"] != request.user_id: return jsonify({"success":False,"message":"Forbidden"}),403
    data    = request.get_json()
    allowed = ["name","price_per_hour","availability","description","image_url","hp"]
    updates = {k:v for k,v in data.items() if k in allowed}
    if data.get("image_base64"):
        try:
            ext = data.get("image_ext","jpg").lower().replace(".","")
            updates["image_url"] = _save_image(data["image_base64"], ext)
        except: pass
    if updates: equipment_col.update_one({"_id":ObjectId(eq_id)},{"$set":updates})
    return jsonify({"success":True,"message":"Equipment updated"})

@equipment_bp.route("/<eq_id>", methods=["DELETE"])
@owner_required
def delete_equipment(eq_id):
    try: eq = equipment_col.find_one({"_id":ObjectId(eq_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not eq: return jsonify({"success":False,"message":"Not found"}),404
    if eq["owner_id"] != request.user_id: return jsonify({"success":False,"message":"Forbidden"}),403
    equipment_col.delete_one({"_id":ObjectId(eq_id)})
    return jsonify({"success":True,"message":"Equipment deleted"})

@equipment_bp.route("/owner/mine", methods=["GET"])
@owner_required
def my_equipment():
    items = list(equipment_col.find({"owner_id":request.user_id}))
    return jsonify({"success":True,"equipment":[_s(e) for e in items]})

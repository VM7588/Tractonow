import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from database.db import users_col
from utils.auth import token_required
from utils.translator import get_all_strings
from bson import ObjectId

user_bp = Blueprint("user", __name__)

def _s(u):
    return {"id":str(u["_id"]),"name":u["name"],"email":u["email"],"phone":u["phone"],
            "role":u["role"],"language":u.get("language","en"),
            "village":u.get("village",""),"mandal":u.get("mandal",""),
            "district":u.get("district",""),"state":u.get("state","")}

@user_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    u=users_col.find_one({"_id":ObjectId(request.user_id)})
    if not u: return jsonify({"success":False,"message":"Not found"}),404
    return jsonify({"success":True,"user":_s(u)})

@user_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    data=request.get_json()
    allowed=["name","phone","language","village","mandal","district","state"]
    updates={k:v for k,v in data.items() if k in allowed and v is not None}
    if not updates: return jsonify({"success":False,"message":"Nothing to update"}),400
    users_col.update_one({"_id":ObjectId(request.user_id)},{"$set":updates})
    u=users_col.find_one({"_id":ObjectId(request.user_id)})
    return jsonify({"success":True,"message":"Profile updated","user":_s(u)})

@user_bp.route("/translations", methods=["GET"])
def translations():
    return jsonify({"success":True,"strings":get_all_strings(request.args.get("lang","en"))})

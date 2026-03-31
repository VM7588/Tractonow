import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, request, jsonify
from database.db import users_col
from utils.auth import hash_password, verify_password, generate_token
from datetime import datetime
from bson import ObjectId

auth_bp = Blueprint("auth", __name__)

# ── Register ──────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["name","email","phone","password","role"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success":False,"message":f"Missing: {', '.join(missing)}"}),400
    if data["role"] not in ("farmer","owner"):
        return jsonify({"success":False,"message":"Role must be farmer or owner"}),400
    if users_col.find_one({"email":data["email"].lower()}):
        return jsonify({"success":False,"message":"Email already registered"}),409
    if users_col.find_one({"phone":data["phone"]}):
        return jsonify({"success":False,"message":"Phone already registered"}),409
    user = {
        "name":data["name"].strip(),"email":data["email"].strip().lower(),
        "phone":data["phone"].strip(),"password":hash_password(data["password"]),
        "role":data["role"],"language":data.get("language","en"),
        "village":data.get("village","").strip(),"mandal":data.get("mandal","").strip(),
        "district":data.get("district","").strip(),"state":data.get("state","Telangana").strip(),
        "created_at":datetime.utcnow()
    }
    result = users_col.insert_one(user)
    token  = generate_token(str(result.inserted_id), data["role"])
    return jsonify({
        "success":True,"message":"Registered successfully","token":token,
        "user":{
            "id":str(result.inserted_id),"name":user["name"],"email":user["email"],
            "role":user["role"],"language":user["language"],
            "village":user["village"],"mandal":user["mandal"],
            "district":user["district"],"state":user["state"]
        }
    }),201

# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data  = request.get_json()
    email = data.get("email","").strip().lower()
    pw    = data.get("password","")
    if not email or not pw:
        return jsonify({"success":False,"message":"Email and password required"}),400
    user = users_col.find_one({"email":email})
    if not user or not verify_password(pw, user["password"]):
        return jsonify({"success":False,"message":"Invalid email or password"}),401
    token = generate_token(str(user["_id"]), user["role"])
    return jsonify({
        "success":True,"message":"Login successful","token":token,
        "user":{
            "id":str(user["_id"]),"name":user["name"],"email":user["email"],
            "role":user["role"],"language":user.get("language","en"),
            "village":user.get("village",""),"mandal":user.get("mandal",""),
            "district":user.get("district",""),"state":user.get("state","")
        }
    })

# ── Check phone (forgot password step 1) ─────────────────────────────────────
@auth_bp.route("/check-phone", methods=["POST"])
def check_phone():
    data  = request.get_json()
    phone = data.get("phone","").strip()
    if not phone:
        return jsonify({"success":False,"message":"Phone required"}),400
    user = users_col.find_one({"phone":phone})
    if not user:
        return jsonify({"success":False,"message":"Phone number not found in our records"}),404
    return jsonify({"success":True,"message":"Phone verified","name":user["name"]})

# ── Reset password (forgot password step 2) ───────────────────────────────────
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data     = request.get_json()
    phone    = data.get("phone","").strip()
    new_pw   = data.get("new_password","")
    if not phone or not new_pw:
        return jsonify({"success":False,"message":"Phone and new_password required"}),400
    if len(new_pw) < 6:
        return jsonify({"success":False,"message":"Password must be at least 6 characters"}),400
    user = users_col.find_one({"phone":phone})
    if not user:
        return jsonify({"success":False,"message":"Phone not found"}),404
    users_col.update_one(
        {"phone":phone},
        {"$set":{"password":hash_password(new_pw),"updated_at":datetime.utcnow()}}
    )
    return jsonify({"success":True,"message":"Password reset successfully! Please login."})

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import Blueprint, request, jsonify
from database.db import bookings_col, db
from utils.auth import token_required, farmer_required
from datetime import datetime
from bson import ObjectId

payment_bp  = Blueprint("payment", __name__)
methods_col = db["payment_methods"]   # persistent MongoDB collection

@payment_bp.route("/methods", methods=["GET"])
@token_required
def get_methods():
    methods = list(methods_col.find({"user_id":request.user_id}))
    return jsonify({"success":True,"methods":[{
        "id":str(m["_id"]),"type":m["type"],"display":m["display"],
        "added_at":str(m.get("added_at",""))} for m in methods]})

@payment_bp.route("/methods", methods=["POST"])
@token_required
def add_method():
    data  = request.get_json()
    mtype = data.get("type","")
    if mtype not in ("upi","card","netbanking"):
        return jsonify({"success":False,"message":"Type must be upi, card, or netbanking"}),400
    doc = {"user_id":request.user_id,"type":mtype,"added_at":datetime.utcnow()}
    if mtype == "upi":
        upi = data.get("upi_id","").strip()
        if not upi or "@" not in upi:
            return jsonify({"success":False,"message":"Invalid UPI ID (e.g. name@upi)"}),400
        doc.update({"upi_id":upi,"display":f"UPI — {upi}"})
    elif mtype == "card":
        num = data.get("card_number","").replace(" ","")
        if len(num) < 12:
            return jsonify({"success":False,"message":"Enter valid card number"}),400
        doc.update({"last4":num[-4:],"card_name":data.get("card_name",""),
                    "expiry":data.get("expiry",""),"display":f"Card •••• {num[-4:]}"})
    elif mtype == "netbanking":
        bank = data.get("bank","").strip()
        if not bank: return jsonify({"success":False,"message":"Bank name required"}),400
        doc.update({"bank":bank,"display":f"Net Banking — {bank}"})
    result = methods_col.insert_one(doc)
    return jsonify({"success":True,"message":"Payment method added!",
                    "method":{"id":str(result.inserted_id),"type":mtype,"display":doc["display"]}}),201

@payment_bp.route("/methods/<mid>", methods=["DELETE"])
@token_required
def remove_method(mid):
    try: methods_col.delete_one({"_id":ObjectId(mid),"user_id":request.user_id})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    return jsonify({"success":True,"message":"Removed"})

@payment_bp.route("/pay", methods=["POST"])
@farmer_required
def pay():
    data       = request.get_json()
    booking_id = data.get("booking_id","")
    method_id  = data.get("method_id","direct")
    try: b = bookings_col.find_one({"_id":ObjectId(booking_id)})
    except: return jsonify({"success":False,"message":"Invalid booking ID"}),400
    if not b: return jsonify({"success":False,"message":"Booking not found"}),404
    if b["farmer_id"] != request.user_id: return jsonify({"success":False,"message":"Forbidden"}),403
    if b.get("payment_status") == "paid":
        return jsonify({"success":False,"message":"Already paid"}),409
    txn = f"TXN{str(ObjectId()).upper()[:12]}"
    bookings_col.update_one({"_id":ObjectId(booking_id)},{"$set":{
        "payment_status":"paid","payment_txn_id":txn,
        "payment_method":method_id,"paid_at":datetime.utcnow()
    }})
    return jsonify({"success":True,"message":"✅ Payment successful! (Demo)",
                    "txn_id":txn,"amount":b["total_price"],"booking_id":booking_id})

@payment_bp.route("/status/<booking_id>", methods=["GET"])
@token_required
def pay_status(booking_id):
    try: b = bookings_col.find_one({"_id":ObjectId(booking_id)})
    except: return jsonify({"success":False,"message":"Invalid ID"}),400
    if not b: return jsonify({"success":False,"message":"Not found"}),404
    return jsonify({"success":True,"payment_status":b.get("payment_status","unpaid"),
                    "txn_id":b.get("payment_txn_id",""),"amount":b.get("total_price",0)})

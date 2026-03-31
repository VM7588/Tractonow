import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, request, jsonify
from database.db import ratings_col, bookings_col
from utils.auth import token_required, farmer_required
from datetime import datetime
from bson import ObjectId

rating_bp = Blueprint("rating", __name__)

# ── Submit Rating ─────────────────────────────────────────────────────────────
@rating_bp.route("/", methods=["POST"])
@farmer_required
def submit_rating():
    data = request.get_json()
    if data.get("rating") is None or not data.get("booking_id"):
        return jsonify({"success": False, "message": "booking_id and rating required"}), 400
    rating_val = int(data["rating"])
    if not 1 <= rating_val <= 5:
        return jsonify({"success": False, "message": "Rating must be 1–5"}), 400

    try:
        booking = bookings_col.find_one({"_id": ObjectId(data["booking_id"])})
    except Exception:
        return jsonify({"success": False, "message": "Invalid booking ID"}), 400
    if not booking:
        return jsonify({"success": False, "message": "Booking not found"}), 404
    if booking["farmer_id"] != request.user_id:
        return jsonify({"success": False, "message": "Forbidden"}), 403
    if booking["status"] != "completed":
        return jsonify({"success": False, "message": "Can only rate completed bookings"}), 409
    if ratings_col.find_one({"booking_id": data["booking_id"]}):
        return jsonify({"success": False, "message": "Already rated this booking"}), 409

    rating_doc = {
        "booking_id":   data["booking_id"],
        "equipment_id": booking["equipment_id"],
        "farmer_id":    request.user_id,
        "owner_id":     booking.get("owner_id", ""),
        "rating":       rating_val,
        "review":       data.get("review", "").strip(),
        "created_at":   datetime.utcnow()
    }
    result = ratings_col.insert_one(rating_doc)
    return jsonify({
        "success":   True,
        "message":   "Rating submitted. Thank you!",
        "rating_id": str(result.inserted_id)
    }), 201

# ── Get Ratings for Equipment ─────────────────────────────────────────────────
@rating_bp.route("/equipment/<eq_id>", methods=["GET"])
def equipment_ratings(eq_id):
    ratings = list(ratings_col.find({"equipment_id": eq_id}).sort("created_at", -1))
    serialized = [{
        "id":         str(r["_id"]),
        "rating":     r["rating"],
        "review":     r.get("review", ""),
        "farmer_id":  r["farmer_id"],
        "created_at": str(r["created_at"])
    } for r in ratings]
    avg = round(sum(r["rating"] for r in ratings) / len(ratings), 1) if ratings else 0
    return jsonify({
        "success":    True,
        "avg_rating": avg,
        "total":      len(ratings),
        "ratings":    serialized
    })

# ── Owner: My Rating Summary ──────────────────────────────────────────────────
@rating_bp.route("/owner/summary", methods=["GET"])
@token_required
def owner_rating_summary():
    ratings = list(ratings_col.find({"owner_id": request.user_id}))
    avg     = round(sum(r["rating"] for r in ratings) / len(ratings), 1) if ratings else 0
    return jsonify({
        "success":    True,
        "avg_rating": avg,
        "total":      len(ratings),
        "breakdown":  {str(i): sum(1 for r in ratings if r["rating"] == i) for i in range(1, 6)}
    })

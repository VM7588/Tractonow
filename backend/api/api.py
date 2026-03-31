import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
"""
api/api.py
Registers a /api/docs blueprint that returns a full API reference as JSON.
Also provides a /api/stats endpoint (admin overview from MongoDB).
"""
from flask import Blueprint, jsonify, request
from database.db import (users_col, equipment_col, bookings_col,
                          group_col, ratings_col, ml_logs_col)
from utils.auth import token_required

api_bp = Blueprint("api_docs", __name__)

# ── API Reference ─────────────────────────────────────────────────────────────
API_REFERENCE = {
    "app":     "TractoNow",
    "version": "1.0.0",
    "base_url": "/api",
    "auth": "Bearer <JWT token> in Authorization header",
    "endpoints": {
        "Auth": [
            {"method": "POST", "path": "/auth/register",
             "desc": "Register a new farmer or owner",
             "body": {"name":"str","email":"str","phone":"str","password":"str",
                      "role":"farmer|owner","language":"en|te|hi (optional)",
                      "village":"str (optional)","district":"str (optional)"},
             "auth": False},
            {"method": "POST", "path": "/auth/login",
             "desc": "Login and receive JWT token",
             "body": {"email":"str","password":"str"},
             "auth": False},
        ],
        "Users": [
            {"method": "GET",  "path": "/users/profile",      "desc": "Get logged-in user profile",          "auth": True},
            {"method": "PUT",  "path": "/users/profile",      "desc": "Update profile fields",               "auth": True},
            {"method": "GET",  "path": "/users/translations", "desc": "Get UI strings for a language (?lang=te)", "auth": False},
        ],
        "Equipment": [
            {"method": "GET",    "path": "/equipment/",          "desc": "List all equipment (filters: type, district, available=true)", "auth": False},
            {"method": "GET",    "path": "/equipment/<id>",      "desc": "Get single equipment details",       "auth": False},
            {"method": "POST",   "path": "/equipment/",          "desc": "Add new equipment (owner only)",     "auth": True,
             "body": {"name":"str","type":"tractor|harvester|rotavator|seed_drill|sprayer|cultivator|plough|thresher",
                      "price_per_hour":"float","brand":"str","model":"str","hp":"int",
                      "village":"str","district":"str","lat":"float","lng":"float","description":"str"}},
            {"method": "PUT",    "path": "/equipment/<id>",      "desc": "Update equipment (owner only)",      "auth": True},
            {"method": "DELETE", "path": "/equipment/<id>",      "desc": "Delete equipment (owner only)",      "auth": True},
            {"method": "GET",    "path": "/equipment/owner/mine","desc": "List owner's own equipment",          "auth": True},
        ],
        "Bookings": [
            {"method": "POST", "path": "/bookings/",              "desc": "Create a new booking (farmer only)",
             "body": {"equipment_id":"str","crop_type":"str","booking_date":"ISO date",
                      "hours_required":"int","notes":"str (optional)"},
             "auth": True},
            {"method": "GET",  "path": "/bookings/my",            "desc": "Farmer: list my bookings",          "auth": True},
            {"method": "GET",  "path": "/bookings/incoming",      "desc": "Owner: list incoming bookings",     "auth": True},
            {"method": "GET",  "path": "/bookings/<id>",          "desc": "Get single booking",                "auth": True},
            {"method": "PUT",  "path": "/bookings/<id>/status",   "desc": "Owner: update booking status",
             "body": {"status":"pending|confirmed|in_progress|completed|cancelled"},
             "auth": True},
            {"method": "PUT",  "path": "/bookings/<id>/cancel",   "desc": "Farmer: cancel booking",            "auth": True},
        ],
        "Group Bookings": [
            {"method": "POST", "path": "/groups/",            "desc": "Create a group booking (farmer only)",
             "body": {"equipment_id":"str","crop_type":"str","booking_date":"ISO date",
                      "hours_required":"int","max_farmers":"int (max 5)"},
             "auth": True},
            {"method": "GET",  "path": "/groups/open",        "desc": "List open groups to join (?district=)",  "auth": True},
            {"method": "POST", "path": "/groups/<id>/join",   "desc": "Join an existing group",                "auth": True},
            {"method": "POST", "path": "/groups/<id>/leave",  "desc": "Leave a group",                         "auth": True},
            {"method": "GET",  "path": "/groups/<id>",        "desc": "Get group details",                     "auth": True},
        ],
        "Ratings": [
            {"method": "POST", "path": "/ratings/",                  "desc": "Submit rating for a completed booking",
             "body": {"booking_id":"str","rating":"1-5","review":"str (optional)"},
             "auth": True},
            {"method": "GET",  "path": "/ratings/equipment/<eq_id>", "desc": "Get all ratings for equipment",  "auth": False},
            {"method": "GET",  "path": "/ratings/owner/summary",     "desc": "Owner: get own rating summary",  "auth": True},
        ],
        "Tracking": [
            {"method": "POST", "path": "/tracking/update",          "desc": "Owner: push GPS location update",
             "body": {"booking_id":"str","lat":"float","lng":"float",
                      "speed_kmh":"float","heading":"float"},
             "auth": True},
            {"method": "GET",  "path": "/tracking/<booking_id>",         "desc": "Get current location + ETA",      "auth": True},
            {"method": "GET",  "path": "/tracking/<booking_id>/history", "desc": "Get full GPS path history",       "auth": True},
        ],
        "ML / Intelligence": [
            {"method": "POST", "path": "/ml/predict",       "desc": "Predict demand for a booking request",
             "body": {"crop_type":"str","equipment_type":"str","booking_date":"ISO date",
                      "district":"str (optional)","lat":"float (optional)","lng":"float (optional)"},
             "auth": True},
            {"method": "GET",  "path": "/ml/area-demand",   "desc": "Area-wise demand heatmap (?district=&equipment_type=&month=)", "auth": True},
            {"method": "GET",  "path": "/ml/weather-advice","desc": "Get weather + farming advice (?lat=&lng=)",  "auth": True},
        ],
    }
}

@api_bp.route("/docs", methods=["GET"])
def api_docs():
    return jsonify({"success": True, "reference": API_REFERENCE})

# ── Platform Stats (for admin / owner dashboard) ──────────────────────────────
@api_bp.route("/stats", methods=["GET"])
@token_required
def platform_stats():
    """Returns high-level platform statistics from MongoDB."""
    total_users      = users_col.count_documents({})
    total_farmers    = users_col.count_documents({"role": "farmer"})
    total_owners     = users_col.count_documents({"role": "owner"})
    total_equipment  = equipment_col.count_documents({})
    avail_equipment  = equipment_col.count_documents({"availability": True})
    total_bookings   = bookings_col.count_documents({})
    active_bookings  = bookings_col.count_documents({"status": {"$in": ["confirmed", "in_progress"]}})
    completed_bookings = bookings_col.count_documents({"status": "completed"})
    open_groups      = group_col.count_documents({"status": "open"})
    total_ratings    = ratings_col.count_documents({})
    total_predictions= ml_logs_col.count_documents({})

    # Revenue estimate
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_price"}}}]
    rev_result = list(bookings_col.aggregate(pipeline))
    total_revenue = round(rev_result[0]["total"], 2) if rev_result else 0

    # Equipment type breakdown
    type_pipeline = [{"$group": {"_id": "$type", "count": {"$sum": 1}}}]
    equipment_by_type = {r["_id"]: r["count"]
                         for r in equipment_col.aggregate(type_pipeline)}

    # Demand level breakdown from ML logs
    demand_pipeline = [{"$group": {"_id": "$demand_level", "count": {"$sum": 1}}}]
    demand_breakdown = {r["_id"]: r["count"]
                        for r in ml_logs_col.aggregate(demand_pipeline)}

    return jsonify({
        "success": True,
        "stats": {
            "users": {
                "total":   total_users,
                "farmers": total_farmers,
                "owners":  total_owners
            },
            "equipment": {
                "total":     total_equipment,
                "available": avail_equipment,
                "by_type":   equipment_by_type
            },
            "bookings": {
                "total":     total_bookings,
                "active":    active_bookings,
                "completed": completed_bookings
            },
            "groups": {
                "open": open_groups
            },
            "ratings": {
                "total": total_ratings
            },
            "revenue": {
                "estimated_total_inr": total_revenue
            },
            "ml": {
                "total_predictions": total_predictions,
                "demand_breakdown":  demand_breakdown
            }
        }
    })

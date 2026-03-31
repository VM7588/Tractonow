import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math, requests as req_lib
from flask import Blueprint, request, jsonify
from database.db import tracking_col, bookings_col, users_col
from utils.auth import token_required, owner_required
from datetime import datetime
from bson import ObjectId

tracking_bp = Blueprint("tracking", __name__)

# ── Owner: push real GPS ──────────────────────────────────────────────────────
@tracking_bp.route("/update", methods=["POST"])
@owner_required
def update_location():
    data = request.get_json()
    required = ["booking_id", "lat", "lng"]
    missing  = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"success": False, "message": f"Missing: {', '.join(missing)}"}), 400
    try:
        booking = bookings_col.find_one({"_id": ObjectId(data["booking_id"])})
    except Exception:
        return jsonify({"success": False, "message": "Invalid booking ID"}), 400
    if not booking:
        return jsonify({"success": False, "message": "Booking not found"}), 404
    if booking.get("owner_id") != request.user_id:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    entry = {
        "booking_id": data["booking_id"],
        "owner_id":   request.user_id,
        "lat":        float(data["lat"]),
        "lng":        float(data["lng"]),
        "speed_kmh":  float(data.get("speed_kmh", 0)),
        "heading":    float(data.get("heading", 0)),
        "accuracy":   float(data.get("accuracy", 0)),
        "timestamp":  datetime.utcnow()
    }
    tracking_col.insert_one(entry)
    return jsonify({"success": True, "message": "Location updated"})

# ── Get current location + routing ───────────────────────────────────────────
@tracking_bp.route("/<booking_id>", methods=["GET"])
@token_required
def get_location(booking_id):
    try:
        booking = bookings_col.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        return jsonify({"success": False, "message": "Invalid booking ID"}), 400
    if not booking:
        return jsonify({"success": False, "message": "Booking not found"}), 404
    if booking["farmer_id"] != request.user_id and booking.get("owner_id") != request.user_id:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    # Get latest real GPS point
    latest = tracking_col.find_one(
        {"booking_id": booking_id},
        sort=[("timestamp", -1)]
    )

    # Get farmer's location as destination
    farmer = users_col.find_one({"_id": ObjectId(booking["farmer_id"])})
    dest_lat = float(booking.get("dest_lat", 0)) or 17.5800
    dest_lng = float(booking.get("dest_lng", 0)) or 80.6400
    if farmer:
        dest_lat = float(farmer.get("lat", dest_lat) or dest_lat)
        dest_lng = float(farmer.get("lng", dest_lng) or dest_lng)

    if latest:
        location = {
            "lat":       latest["lat"],
            "lng":       latest["lng"],
            "speed_kmh": latest.get("speed_kmh", 0),
            "heading":   latest.get("heading", 0),
            "accuracy":  latest.get("accuracy", 0),
            "timestamp": str(latest["timestamp"]),
            "simulated": False
        }
    else:
        location = {
            "lat": dest_lat + 0.02, "lng": dest_lng + 0.02,
            "speed_kmh": 0, "heading": 0, "accuracy": 0,
            "timestamp": str(datetime.utcnow()), "simulated": True
        }

    # Calculate road-based route using OSRM (free, no API key)
    route_data = get_road_route(
        location["lat"], location["lng"],
        dest_lat, dest_lng
    )

    eta = {
        "distance_km":  route_data.get("distance_km",  _haversine(location["lat"],location["lng"],dest_lat,dest_lng)),
        "eta_minutes":  route_data.get("eta_minutes",  0),
        "eta_seconds":  route_data.get("eta_seconds",  0),
        "road_distance":route_data.get("road_distance",""),
    }

    return jsonify({
        "success":     True,
        "location":    location,
        "destination": {"lat": dest_lat, "lng": dest_lng},
        "eta":         eta,
        "route":       route_data.get("route", []),
        "steps":       route_data.get("steps", [])
    })

# ── History ───────────────────────────────────────────────────────────────────
@tracking_bp.route("/<booking_id>/history", methods=["GET"])
@token_required
def track_history(booking_id):
    try:
        booking = bookings_col.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        return jsonify({"success": False, "message": "Invalid booking ID"}), 400
    if not booking:
        return jsonify({"success": False, "message": "Not found"}), 404
    if booking["farmer_id"] != request.user_id and booking.get("owner_id") != request.user_id:
        return jsonify({"success": False, "message": "Forbidden"}), 403
    history = list(tracking_col.find(
        {"booking_id": booking_id}
    ).sort("timestamp", 1).limit(500))
    return jsonify({
        "success": True,
        "count":   len(history),
        "path":    [{"lat":p["lat"],"lng":p["lng"],"ts":str(p["timestamp"])} for p in history]
    })

# ── Set destination (farmer sets their field location) ────────────────────────
@tracking_bp.route("/<booking_id>/destination", methods=["POST"])
@token_required
def set_destination(booking_id):
    data = request.get_json()
    lat  = data.get("lat")
    lng  = data.get("lng")
    if lat is None or lng is None:
        return jsonify({"success": False, "message": "lat and lng required"}), 400
    try:
        bookings_col.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"dest_lat": float(lat), "dest_lng": float(lng)}}
        )
    except Exception:
        return jsonify({"success": False, "message": "Invalid booking ID"}), 400
    return jsonify({"success": True, "message": "Destination set"})

# ── Road routing via OSRM (free, no API key needed) ──────────────────────────
def get_road_route(src_lat, src_lng, dst_lat, dst_lng):
    """
    Uses OSRM public API for real road-based routing.
    Returns route geometry, steps with instructions, distance, ETA.
    """
    try:
        url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{src_lng},{src_lat};{dst_lng},{dst_lat}"
            f"?overview=full&geometries=geojson&steps=true&annotations=false"
        )
        resp = req_lib.get(url, timeout=6)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            return _fallback_route(src_lat, src_lng, dst_lat, dst_lng)

        route    = data["routes"][0]
        legs     = route.get("legs", [{}])
        geometry = route["geometry"]["coordinates"]  # [[lng,lat], ...]

        # Convert to [lat,lng] for Leaflet
        latlngs = [[pt[1], pt[0]] for pt in geometry]

        # Extract turn-by-turn steps
        steps = []
        for leg in legs:
            for step in leg.get("steps", []):
                maneuver   = step.get("maneuver", {})
                instruction = _osrm_instruction(
                    maneuver.get("type",""),
                    maneuver.get("modifier",""),
                    step.get("name","")
                )
                steps.append({
                    "instruction": instruction,
                    "distance_m":  round(step.get("distance", 0)),
                    "duration_s":  round(step.get("duration", 0)),
                    "name":        step.get("name",""),
                })

        dist_km  = round(route["distance"] / 1000, 2)
        dur_sec  = round(route["duration"])
        dur_min  = round(dur_sec / 60)

        return {
            "distance_km":  dist_km,
            "road_distance": f"{dist_km} km",
            "eta_seconds":  dur_sec,
            "eta_minutes":  dur_min,
            "route":        latlngs,
            "steps":        steps
        }
    except Exception as e:
        print(f"[OSRM] Route error: {e}")
        return _fallback_route(src_lat, src_lng, dst_lat, dst_lng)

def _fallback_route(src_lat, src_lng, dst_lat, dst_lng):
    """Straight-line fallback when OSRM is unavailable."""
    dist = _haversine(src_lat, src_lng, dst_lat, dst_lng)
    return {
        "distance_km":  dist,
        "road_distance": f"{dist} km (straight line)",
        "eta_seconds":  int(dist / 20 * 3600),
        "eta_minutes":  int(dist / 20 * 60),
        "route":        [[src_lat, src_lng], [dst_lat, dst_lng]],
        "steps":        []
    }

def _haversine(lat1, lng1, lat2, lng2):
    R  = 6371
    d1 = math.radians(lat2 - lat1)
    d2 = math.radians(lng2 - lng1)
    a  = math.sin(d1/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d2/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

def _osrm_instruction(mtype, modifier, name):
    """Convert OSRM maneuver to human-readable instruction."""
    road = f" on {name}" if name else ""
    instructions = {
        ("depart",   ""):        f"Head{road}",
        ("turn",     "left"):    f"Turn left{road}",
        ("turn",     "right"):   f"Turn right{road}",
        ("turn",     "slight left"):  f"Bear left{road}",
        ("turn",     "slight right"): f"Bear right{road}",
        ("turn",     "sharp left"):   f"Sharp left{road}",
        ("turn",     "sharp right"):  f"Sharp right{road}",
        ("continue", "straight"):     f"Continue straight{road}",
        ("merge",    ""):        f"Merge{road}",
        ("roundabout",""):       f"Enter roundabout{road}",
        ("arrive",   ""):        "You have arrived",
        ("arrive",   "left"):    "Arrive — destination is on your left",
        ("arrive",   "right"):   "Arrive — destination is on your right",
    }
    return instructions.get((mtype, modifier),
           instructions.get((mtype, ""),
           f"{mtype.capitalize()} {modifier}{road}".strip()))

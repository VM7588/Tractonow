import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
"""
routes/page_routes.py
Serves all HTML pages (Jinja2 templates).
The frontend JS handles data via the /api/* endpoints.
"""
from flask import Blueprint, render_template, redirect, url_for, request

page_bp = Blueprint("pages", __name__)

# ── Public pages ──────────────────────────────────────────────────────────────
@page_bp.route("/")
def index():
    return render_template("index.html")

@page_bp.route("/login")
def login():
    return render_template("login.html")

@page_bp.route("/register")
def register():
    return render_template("register.html")

@page_bp.route("/offline")
def offline():
    return render_template("offline.html")

# ── Protected pages (auth enforced in JS via redirectIfNotLoggedIn) ────────────
@page_bp.route("/dashboard/farmer")
def dashboard_farmer():
    return render_template("dashboard_farmer.html")

@page_bp.route("/dashboard/owner")
def dashboard_owner():
    return render_template("dashboard_owner.html")

@page_bp.route("/booking")
def booking():
    return render_template("booking.html")

@page_bp.route("/group-booking")
def group_booking():
    return render_template("group_booking.html")

@page_bp.route("/tracking")
def tracking():
    booking_id = request.args.get("booking_id", "")
    return render_template("tracking.html", booking_id=booking_id)

@page_bp.route("/rating")
def rating():
    booking_id   = request.args.get("booking_id", "")
    equipment_id = request.args.get("equipment_id", "")
    return render_template("rating.html",
                           booking_id=booking_id,
                           equipment_id=equipment_id)

# ── Redirect /dashboard → role-specific page (resolved by JS) ─────────────────
@page_bp.route("/dashboard")
def dashboard():
    return redirect(url_for("pages.dashboard_farmer"))

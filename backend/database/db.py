import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from config import Config

try:
    client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("[DB] ✅  MongoDB connected successfully")
except ConnectionFailure as e:
    print(f"[DB] ❌  MongoDB connection failed: {e}")
    sys.exit(1)

db = client["tractonow"]

users_col      = db["users"]
equipment_col  = db["equipment"]
bookings_col   = db["bookings"]
group_col      = db["group_bookings"]
ratings_col    = db["ratings"]
tracking_col   = db["tracking"]
ml_logs_col    = db["ml_logs"]

def create_indexes():
    users_col.create_index([("email", ASCENDING)], unique=True)
    users_col.create_index([("phone", ASCENDING)], unique=True)
    equipment_col.create_index([("owner_id", ASCENDING)])
    equipment_col.create_index([("type", ASCENDING)])
    equipment_col.create_index([("location.district", ASCENDING)])
    bookings_col.create_index([("farmer_id", ASCENDING)])
    bookings_col.create_index([("equipment_id", ASCENDING)])
    bookings_col.create_index([("status", ASCENDING)])
    bookings_col.create_index([("booking_date", DESCENDING)])
    group_col.create_index([("district", ASCENDING)])
    group_col.create_index([("status", ASCENDING)])
    ratings_col.create_index([("equipment_id", ASCENDING)])
    ratings_col.create_index([("booking_id", ASCENDING)], unique=True)
    tracking_col.create_index([("booking_id", ASCENDING)])
    print("[DB] ✅  Indexes created")

create_indexes()

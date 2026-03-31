import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI        = os.getenv("MONGO_URI", "mongodb://localhost:27017/tractonow")
    JWT_SECRET       = os.getenv("JWT_SECRET", "tractonow_secret")
    JWT_EXPIRY       = int(os.getenv("JWT_EXPIRY", 86400))
    OPENWEATHER_KEY  = os.getenv("OPENWEATHER_API_KEY", "")
    DEBUG            = os.getenv("FLASK_DEBUG", "True") == "True"
    PORT             = int(os.getenv("PORT", 5000))

    LANGUAGES = ["en", "te", "hi"]

    EQUIPMENT_TYPES = [
        "tractor", "harvester", "rotavator",
        "seed_drill", "sprayer", "cultivator", "plough", "thresher"
    ]

    BOOKING_STATUS = ["pending", "confirmed", "in_progress", "completed", "cancelled"]

    MAX_GROUP_SIZE = 5

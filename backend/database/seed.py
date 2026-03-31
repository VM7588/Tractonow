import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import users_col, equipment_col, bookings_col
from datetime import datetime, timedelta
import bcrypt

def hash_pw(plain): return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def seed():
    print("🌱 Checking seed data...")

    # ── Only seed if collections are EMPTY — never wipe real data ──────────
    if users_col.count_documents({}) > 0:
        print("  [✓] Users already exist — skipping seed (data preserved)")
        print("\n📋 Demo login credentials (if using seeded data):")
        print("   Farmer  → ramu@farm.com     / ramu123")
        print("   Owner   → suresh@owner.com  / suresh123")
        return

    print("  [→] Empty database detected — inserting sample data...")

    sample_users = [
        {"name":"Ramu Farmer",   "email":"ramu@farm.com",    "phone":"9000000001",
         "password":hash_pw("ramu123"),   "role":"farmer","language":"te",
         "village":"Yellandu","mandal":"Yellandu","district":"Bhadradri Kothagudem","state":"Telangana","created_at":datetime.utcnow()},
        {"name":"Suresh Owner",  "email":"suresh@owner.com", "phone":"9000000002",
         "password":hash_pw("suresh123"), "role":"owner", "language":"te",
         "village":"Kothagudem","mandal":"Kothagudem","district":"Bhadradri Kothagudem","state":"Telangana","created_at":datetime.utcnow()},
        {"name":"Lakshmi Farmer","email":"lakshmi@farm.com", "phone":"9000000003",
         "password":hash_pw("lakshmi123"),"role":"farmer","language":"hi",
         "village":"Palvancha","mandal":"Palvancha","district":"Bhadradri Kothagudem","state":"Telangana","created_at":datetime.utcnow()},
        {"name":"Venkat Owner",  "email":"venkat@owner.com", "phone":"9000000004",
         "password":hash_pw("venkat123"), "role":"owner", "language":"en",
         "village":"Bhadrachalam","mandal":"Bhadrachalam","district":"Bhadradri Kothagudem","state":"Telangana","created_at":datetime.utcnow()},
    ]
    result   = users_col.insert_many(sample_users)
    user_ids = {u["email"]: str(i) for u, i in zip(sample_users, result.inserted_ids)}
    print(f"  [✓] Inserted {len(result.inserted_ids)} users")

    if equipment_col.count_documents({}) == 0:
        sample_equipment = [
            {"name":"Mahindra 575 DI","type":"tractor","brand":"Mahindra","model":"575 DI","hp":45,
             "price_per_hour":350.0,"owner_id":user_ids["suresh@owner.com"],
             "location":{"village":"Kothagudem","mandal":"Kothagudem","district":"Bhadradri Kothagudem","state":"Telangana","lat":17.5524,"lng":80.6194},
             "availability":True,"description":"Well maintained tractor","image_url":"","created_at":datetime.utcnow()},
            {"name":"John Deere Harvester","type":"harvester","brand":"John Deere","model":"W70","hp":110,
             "price_per_hour":800.0,"owner_id":user_ids["venkat@owner.com"],
             "location":{"village":"Bhadrachalam","mandal":"Bhadrachalam","district":"Bhadradri Kothagudem","state":"Telangana","lat":17.6696,"lng":80.8937},
             "availability":True,"description":"Ideal for rice and wheat","image_url":"","created_at":datetime.utcnow()},
            {"name":"Sonalika Rotavator","type":"rotavator","brand":"Sonalika","model":"RT-125","hp":35,
             "price_per_hour":200.0,"owner_id":user_ids["suresh@owner.com"],
             "location":{"village":"Kothagudem","mandal":"Kothagudem","district":"Bhadradri Kothagudem","state":"Telangana","lat":17.5524,"lng":80.6194},
             "availability":True,"description":"For land preparation","image_url":"","created_at":datetime.utcnow()},
            {"name":"Kirloskar Sprayer","type":"sprayer","brand":"Kirloskar","model":"HTP-35","hp":0,
             "price_per_hour":150.0,"owner_id":user_ids["venkat@owner.com"],
             "location":{"village":"Palvancha","mandal":"Palvancha","district":"Bhadradri Kothagudem","state":"Telangana","lat":17.5951,"lng":80.7170},
             "availability":True,"description":"High pressure sprayer","image_url":"","created_at":datetime.utcnow()},
        ]
        eq_result = equipment_col.insert_many(sample_equipment)
        eq_ids    = [str(i) for i in eq_result.inserted_ids]
        print(f"  [✓] Inserted {len(eq_ids)} equipment")

        if bookings_col.count_documents({}) == 0:
            bookings_col.insert_many([
                {"farmer_id":user_ids["ramu@farm.com"],"equipment_id":eq_ids[0],
                 "owner_id":user_ids["suresh@owner.com"],"crop_type":"rice",
                 "booking_date":datetime.utcnow()+timedelta(days=3),"hours_required":4,
                 "total_price":1400.0,"price_breakdown":{},"status":"confirmed",
                 "payment_status":"unpaid","district":"Bhadradri Kothagudem",
                 "mandal":"Yellandu","village":"Yellandu","notes":"Need early morning",
                 "created_at":datetime.utcnow()},
            ])
            print("  [✓] Inserted 1 sample booking")

    print("\n✅  Seeding complete!")
    print("\n📋 Login credentials:")
    print("   Farmer  → ramu@farm.com     / ramu123")
    print("   Farmer  → lakshmi@farm.com  / lakshmi123")
    print("   Owner   → suresh@owner.com  / suresh123")
    print("   Owner   → venkat@owner.com  / venkat123")

if __name__ == "__main__":
    seed()

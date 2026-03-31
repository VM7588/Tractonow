import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime

CROP_PEAK_MONTHS = {
    "rice":     [6, 7, 8, 10, 11],
    "wheat":    [3, 4, 10, 11],
    "cotton":   [6, 7, 9, 10],
    "sugarcane":[1, 2, 11, 12],
    "maize":    [6, 7, 9, 10],
    "default":  []
}

def get_demand_multiplier(crop_type: str, booking_date: datetime) -> float:
    month  = booking_date.month
    peaks  = CROP_PEAK_MONTHS.get(crop_type.lower(), CROP_PEAK_MONTHS["default"])
    if month in peaks:
        return 1.6
    shoulders = {(m % 12) + 1 for m in peaks} | {((m - 2) % 12) + 1 for m in peaks}
    if month in shoulders:
        return 1.3
    return 1.0

def calculate_price(base_price_per_hour, hours, crop_type, booking_date, group_size=1):
    multiplier   = get_demand_multiplier(crop_type, booking_date)
    gross_total  = round(base_price_per_hour * hours * multiplier, 2)
    per_farmer   = round(gross_total / max(group_size, 1), 2)
    platform_fee = round(gross_total * 0.05, 2)
    owner_payout = round(gross_total - platform_fee, 2)
    return {
        "base_price_per_hour": base_price_per_hour,
        "hours": hours,
        "demand_multiplier": multiplier,
        "gross_total": gross_total,
        "per_farmer_share": per_farmer,
        "platform_fee": platform_fee,
        "owner_payout": owner_payout,
        "group_size": group_size
    }

def suggest_best_time(crop_type: str, district: str) -> dict:
    now   = datetime.utcnow()
    peaks = CROP_PEAK_MONTHS.get(crop_type.lower(), [])
    if now.month in peaks:
        return {
            "is_peak_season": True,
            "message": "⚠️ Peak season — prices are higher. Book early.",
            "tip": "Consider group booking to split costs."
        }
    return {
        "is_peak_season": False,
        "message": "✅ Off-peak season — prices are normal.",
        "tip": "Good time to book at standard rates."
    }

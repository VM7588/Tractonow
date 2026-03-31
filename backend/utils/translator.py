import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TRANSLATIONS = {
    "en": {
        "welcome":"Welcome to TractoNow","book_equipment":"Book Equipment",
        "available":"Available","not_available":"Not Available",
        "booking_confirmed":"Booking Confirmed","booking_pending":"Booking Pending",
        "high_demand":"High Demand — Book Early","low_demand":"Low Demand — Good Time to Book",
        "group_booking":"Group Booking","join_group":"Join a Group",
        "total_price":"Total Price","per_farmer":"Your Share",
        "rain_alert":"Rain Alert — Delay Operations","login":"Login","register":"Register",
        "my_bookings":"My Bookings","my_equipment":"My Equipment",
        "add_equipment":"Add Equipment","rate_service":"Rate Service","track":"Track Equipment",
    },
    "te": {
        "welcome":"TractoNow కి స్వాగతం","book_equipment":"పరికరాన్ని బుక్ చేయండి",
        "available":"అందుబాటులో ఉంది","not_available":"అందుబాటులో లేదు",
        "booking_confirmed":"బుకింగ్ నిర్ధారించబడింది","booking_pending":"బుకింగ్ పెండింగ్‌లో ఉంది",
        "high_demand":"అధిక డిమాండ్ — ముందుగా బుక్ చేయండి","low_demand":"తక్కువ డిమాండ్",
        "group_booking":"గ్రూప్ బుకింగ్","join_group":"గ్రూప్‌లో చేరండి",
        "total_price":"మొత్తం ధర","per_farmer":"మీ వాటా",
        "rain_alert":"వర్షపు హెచ్చరిక","login":"లాగిన్","register":"నమోదు చేయండి",
        "my_bookings":"నా బుకింగ్‌లు","my_equipment":"నా పరికరాలు",
        "add_equipment":"పరికరం జోడించండి","rate_service":"సేవను రేట్ చేయండి","track":"ట్రాక్ చేయండి",
    },
    "hi": {
        "welcome":"TractoNow में आपका स्वागत है","book_equipment":"उपकरण बुक करें",
        "available":"उपलब्ध है","not_available":"उपलब्ध नहीं है",
        "booking_confirmed":"बुकिंग की पुष्टि हो गई","booking_pending":"बुकिंग लंबित है",
        "high_demand":"अधिक मांग — जल्दी बुक करें","low_demand":"कम मांग",
        "group_booking":"समूह बुकिंग","join_group":"समूह में शामिल हों",
        "total_price":"कुल कीमत","per_farmer":"आपका हिस्सा",
        "rain_alert":"बारिश की चेतावनी","login":"लॉगिन","register":"पंजीकरण करें",
        "my_bookings":"मेरी बुकिंग","my_equipment":"मेरे उपकरण",
        "add_equipment":"उपकरण जोड़ें","rate_service":"सेवा रेट करें","track":"ट्रैक करें",
    }
}

def translate(key: str, lang: str = "en") -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

def get_all_strings(lang: str = "en") -> dict:
    return {**TRANSLATIONS.get("en", {}), **TRANSLATIONS.get(lang, {})}

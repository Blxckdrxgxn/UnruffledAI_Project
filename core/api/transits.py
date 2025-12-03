import requests
from django.conf import settings

BASE_URL = "https://json.astrologyapi.com/v1"


def convert_nature_to_risk(nature: str) -> str:
    if not nature:
        return "Low"
    n = nature.lower()
    if any(word in n for word in ["stress", "challenge", "restriction", "crisis"]):
        return "High"
    if any(word in n for word in ["mixed", "lesson", "growth"]):
        return "Moderate"
    return "Low"


def get_transit_alerts(birth_date, birth_time, lat, lon, timezone):
    user = settings.ASTROLOGY_API_USER_ID
    key = settings.ASTROLOGY_API_KEY

    if not user or not key:
        return []

    url = f"{BASE_URL}/transits_natal"
    payload = {
        "day": birth_date.day,
        "month": birth_date.month,
        "year": birth_date.year,
        "hour": birth_time.hour,
        "min": birth_time.minute,
        "lat": lat,
        "lon": lon,
        "tzone": timezone,
    }

    try:
        resp = requests.post(url, json=payload, auth=(user, key))
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"transit_name": "API error", "description": str(e), "risk_level": "Low"}]

    alerts = []
    for item in data.get("transits", []):
        name = f"{item.get('transit_planet')} {item.get('aspect_type')} {item.get('natal_planet')}"
        alerts.append({
            "transit_name": name,
            "description": item.get("description", "No description provided."),
            "impact_area": item.get("nature", "General"),
            "risk_level": convert_nature_to_risk(item.get("nature")),
            "start_date": item.get("start_date", ""),
            "end_date": item.get("end_date", ""),
        })
    return alerts

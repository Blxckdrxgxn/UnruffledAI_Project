import requests
from django.conf import settings

BASE_URL = "https://json.astrologyapi.com/v1"


def astrology_api_request(endpoint: str, payload: dict):
    """
    Low-level helper for POSTing to AstrologyAPI.
    """
    user = settings.ASTROLOGY_API_USER_ID
    key = settings.ASTROLOGY_API_KEY

    if not user or not key:
        return {"error": "Missing AstrologyAPI credentials"}

    url = f"{BASE_URL}/{endpoint}"

    try:
        resp = requests.post(url, json=payload, auth=(user, key))
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_natal_interpretation(birth_date, birth_time, latitude, longitude, timezone):
    payload = {
        "day": birth_date.day,
        "month": birth_date.month,
        "year": birth_date.year,
        "hour": birth_time.hour,
        "min": birth_time.minute,
        "lat": latitude,
        "lon": longitude,
        "tzone": timezone,
    }
    return astrology_api_request("natal_chart_interpretation", payload)


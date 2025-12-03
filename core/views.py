# ---------------------------------------------------
# LOGIN VIEW
# ---------------------------------------------------
def login_view(request):
    return render(request, "core/login.html")
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from datetime import date

from .models import (
    UserProfile, 
    AIPrediction, 
    BiometricData, 
    NatalChart, 
    UserPreference, 
    UserFeedback
)

from .burnout_model import predict_burnout
from .api.astrology import get_natal_interpretation
from core.api.transits import get_transit_alerts


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def get_active_profile():
    """Always returns the first user profile (demo mode)."""
    profile = UserProfile.objects.get(id=1)
    return profile



def compute_transit_pressure(transits):
    if not transits:
        return 0

    high_risk_count = 0
    for t in transits:
        if isinstance(t, dict) and t.get("severity", "").lower() in ("high", "major"):
            high_risk_count += 1

    return min(high_risk_count * 10, 100)


# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
def dashboard_view(request):
    profile = get_active_profile()

    latest_bio = BiometricData.objects.order_by("-timestamp").first()
    latest_ai = AIPrediction.objects.order_by("-prediction_date").first()
    ai_score = latest_ai.prediction_burnout_risk if latest_ai else 0

    # Get transit alerts if birth data exists
    transits = []
    if profile and profile.birth_date and profile.birth_time:
        transits = get_transit_alerts(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            lat=profile.birth_latitude,
            lon=profile.birth_longitude,
            timezone=profile.birth_timezone,
        )

    transit_pressure = compute_transit_pressure(transits)

    combined_score = (
        ai_score * 0.65 +
        ((100 - (latest_bio.hrv_score or 50)) * 0.10 if latest_bio else 0) +
        (((7 - (latest_bio.sleep_hours or 7)) * 10) * 0.10 if latest_bio else 0) +
        ((latest_bio.stress_level or 5) * 0.15 if latest_bio else 0) +
        transit_pressure * 0.20
    )

    combined_score = round(min(max(combined_score, 0), 100), 1)

    remaining_risk = 100 - combined_score
    return render(request, "core/dashboard.html", {
        "combined_risk": combined_score,
        "remaining_risk": remaining_risk,
        "transit_alerts": transits,
        "latest_biometric": latest_bio,
        "latest_prediction": latest_ai,
    })


# ---------------------------------------------------
# REPORTS
# ---------------------------------------------------
def burnout_report_view(request):
    profile = get_active_profile()
    predictions = AIPrediction.objects.filter(user_profile=profile).order_by("-prediction_date")

    dates = [p.prediction_date.strftime("%Y-%m-%d") for p in predictions]
    scores = [round(p.prediction_burnout_risk * 100, 2) for p in predictions]

    if predictions:
        avg_score = round(sum(scores) / len(scores), 2)
        latest = predictions[0]
    else:
        avg_score = 0
        latest = None

    return render(request, "core/reports.html", {
        "predictions": predictions,
        "dates": dates,
        "scores": scores,
        "avg_score": avg_score,
        "latest": latest,
    })


# ---------------------------------------------------
# NATAL CHART
# ---------------------------------------------------
def natal_chart_view(request, full_name):
    profile = UserProfile.objects.filter(full_name=full_name).first()
    if not profile:
        return render(request, "core/natal_chart.html", {"error": "Profile not found."})

    api_response = get_natal_interpretation(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        latitude=profile.birth_latitude,
        longitude=profile.birth_longitude,
        timezone=profile.birth_timezone,
    )

    if not api_response or "planets" not in api_response:
        return render(request, "core/natal_chart.html", {"profile": profile, "error": "No chart data available."})

    planets = api_response.get("planets", [])
    houses = api_response.get("houses", [])
    aspects = api_response.get("aspects", [])

    sun_sign = next((p["sign"] for p in planets if p["name"] == "Sun"), None)
    moon_sign = next((p["sign"] for p in planets if p["name"] == "Moon"), None)
    rising_sign = houses[0]["sign"] if houses else None

    chart = {
        "sun": sun_sign,
        "moon": moon_sign,
        "rising": rising_sign,
        "planets": planets,
        "houses": houses,
        "aspects": aspects,
        "elements": api_response.get("elements", {}),
        "modes": api_response.get("modes", {}),
        "moon_phase": api_response.get("moon_phase", {}),
        "dominant_sign": api_response.get("dominant_sign", {}),
        "hemisphere": api_response.get("hemisphere", {}),
    }

    # Also show transits on this page
    transits = get_transit_alerts(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        lat=profile.birth_latitude,
        lon=profile.birth_longitude,
        timezone=profile.birth_timezone,
    )

    # Simple AI-generated guidance
    daily_guidance = None
    if sun_sign and moon_sign:
        daily_guidance = (
            f"Your {sun_sign} Sun drives your actions today, "
            f"while your {moon_sign} Moon influences emotions. "
            f"Your Rising sign, {rising_sign}, shapes how you respond to events."
        )

    return render(request, "core/natal_chart.html", {
        "profile": profile,
        "chart": chart,
        "transits": transits,
        "daily_guidance": daily_guidance,
    })


# ---------------------------------------------------
# REGISTRATION (NO AUTH)
# ---------------------------------------------------
def registration_view(request):
    if request.method == "POST":

        profile = UserProfile.objects.create(
            full_name=request.POST.get("full_name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            birth_date=request.POST.get("dob"),
            birth_time=request.POST.get("tob"),
            birth_city=request.POST.get("birth_city"),
            birth_latitude=request.POST.get("birth_latitude"),
            birth_longitude=request.POST.get("birth_longitude"),
            birth_timezone=request.POST.get("birth_timezone"),
        )

        messages.success(request, "Registration complete!")
        return redirect("dashboard")

    return render(request, "core/registration.html")


# ---------------------------------------------------
# SETTINGS
# ---------------------------------------------------
def settings_view(request):
    profile = get_active_profile()

    user_pref, _ = UserPreference.objects.get_or_create(user_profile=profile)

    if request.method == "POST":
        user_pref.notify_burnout_risk = bool(request.POST.get("notify_burnout"))
        user_pref.notify_astrological_events = bool(request.POST.get("notify_astrology"))
        user_pref.device_sync_enabled = bool(request.POST.get("device_sync"))
        user_pref.dark_mode = bool(request.POST.get("dark_mode"))
        user_pref.save()

        UserFeedback.objects.create(
            user_profile=profile,
            rating=int(request.POST.get("rating") or 5),
            comments=request.POST.get("feedback") or "",
            feature_requests=request.POST.get("feature_request") or "",
        )

        return render(request, "core/settings.html", {
            "user_pref": user_pref,
            "success": True,
        })

    return render(request, "core/settings.html", {
        "user_pref": user_pref,
    })


# ---------------------------------------------------
# DARK MODE
# ---------------------------------------------------
def toggle_dark_mode_view(request):
    profile = get_active_profile()

    user_pref, _ = UserPreference.objects.get_or_create(user_profile=profile)
    value = request.POST.get("dark_mode")

    user_pref.dark_mode = value.lower() in ("1", "true", "yes", "on")
    user_pref.save()

    return JsonResponse({"dark_mode": user_pref.dark_mode})


# ---------------------------------------------------
# ADD BIOMETRIC DATA
# ---------------------------------------------------
def add_biometric_view(request):
    if request.method == "POST":
        profile = get_active_profile()

        BiometricData.objects.create(
            user_profile=profile,
            heart_rate=request.POST.get("heart_rate"),
            hrv_score=request.POST.get("hrv_score"),
            sleep_hours=request.POST.get("sleep_hours"),
            activity_level=request.POST.get("activity_level"),
            stress_level=request.POST.get("stress_index"),
        )

        messages.success(request, "Biometric data added!")
        return redirect("dashboard")

    return redirect("dashboard")


# ---------------------------------------------------
# AI BURNOUT API
# ---------------------------------------------------
def burnout_api(request):
    profile = get_active_profile()

    category, score = predict_burnout(
        heart_rate=int(request.GET.get("heart_rate")),
        hrv_score=float(request.GET.get("hrv_score")),
        sleep_hours=float(request.GET.get("sleep_hours")),
        activity_level=int(request.GET.get("activity_level")),
        stress_level=int(request.GET.get("stress_level")),
        transit_planet=request.GET.get("transit_planet"),
        natal_house=request.GET.get("natal_house"),
        sleep_quality=request.GET.get("sleep_quality"),
    )

    AIPrediction.objects.create(
        user_profile=profile,
        prediction_date=date.today(),
        prediction_burnout_risk=score,
        predicted_burnout_level=category,
        contributing_factors="Generated by AI burnout analysis.",
        recommendations="Rest, hydrate, and meditate.",
        meditation_link="https://calm.com/meditation",
    )

    return JsonResponse({
        "burnout_category": category,
        "burnout_score": round(score * 100, 2),
    })


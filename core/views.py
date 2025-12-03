from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import date

from .models import (
    UserProfile, 
    AIPrediction, 
    BiometricData, 
    NatalChart, 
    UserPreference, 
    UserFeedback
)

from .burnout_model import predict_burnout  # correct burnout AI model
from .api.astrology import get_natal_interpretation
from core.api.transits import get_transit_alerts


# Utility function to compute a 'pressure' score from transits
def compute_transit_pressure(transits):
    """
    Computes a pressure score based on the number and severity of transits.
    Adjust logic as needed for your domain.
    """
    if not transits:
        return 0
    # Example: count 'high' or 'major' transits, or just total
    high_risk_count = 0
    for t in transits:
        # If your transit dicts have a 'severity' or 'risk' key, adjust here
        if isinstance(t, dict) and t.get('severity', '').lower() in ('high', 'major'):
            high_risk_count += 1
    # Simple formula: 10 points per high/major transit, capped at 100
    return min(high_risk_count * 10, 100)

# ---------------------------
# DASHBOARD VIEW (single consolidated implementation)
# ---------------------------
@login_required
def dashboard_view(request):
    profile = UserProfile.objects.first()

    latest_bio = BiometricData.objects.order_by("-timestamp").first()
    latest_ai = AIPrediction.objects.order_by("-prediction_date").first()
    ai_score = latest_ai.prediction_burnout_risk if latest_ai else 0

    transits = []
    if profile and profile.birth_date and profile.birth_time:
        transits = get_transit_alerts(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            lat=getattr(profile, "birth_latitude", 0),
            lon=getattr(profile, "birth_longitude", 0),
            timezone=getattr(profile, "birth_timezone", 0),
        )

    transit_pressure = compute_transit_pressure(transits or [])

    combined_score = (
        ai_score * 0.65 +
        ((100 - (latest_bio.hrv_score or 50)) * 0.10 if latest_bio else 0) +
        (((7 - (latest_bio.sleep_hours or 7)) * 10) * 0.10 if latest_bio else 0) +
        ((latest_bio.stress_level or 5) * 0.15 if latest_bio else 0) +
        transit_pressure * 0.20
    )
    combined_score = round(min(max(combined_score, 0), 100), 1)

    return render(request, "core/dashboard.html", {
        "combined_risk": combined_score,
        "transit_alerts": transits,
        "latest_biometric": latest_bio,
        "latest_prediction": latest_ai,
    })


# ---------------------------
# REPORTS VIEW
# ---------------------------
def burnout_report_view(request):
    predictions = AIPrediction.objects.select_related("user_profile").order_by('-prediction_date')

    # Chart data
    dates = [p.prediction_date.strftime("%Y-%m-%d") for p in predictions]
    scores = [round(p.prediction_burnout_risk * 100, 2) for p in predictions]

    # Summary data
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



# ---------------------------
# NATAL CHART VIEW
# ---------------------------
def natal_chart_view(request, full_name):

    profile = UserProfile.objects.filter(full_name=full_name).first()
    if not profile:
        return render(request, "core/natal_chart.html", {"error": "No profile found."})

    # ---- NATAl chart API ----
    api_response = get_natal_interpretation(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        latitude=profile.birth_latitude,
        longitude=profile.birth_longitude,
        timezone=profile.birth_timezone,
    )

    if api_response is None or "planets" not in api_response:
        return render(request, "core/natal_chart.html", {"profile": profile, "error": "Natal chart data unavailable."})

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

    # ---- TRANSITS ----
    transits = get_transit_alerts(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        lat=profile.birth_latitude,
        lon=profile.birth_longitude,
        timezone=profile.birth_timezone,
    )

    # --- DAILY GUIDANCE AI ---
    daily_guidance = None
    if profile and sun_sign and moon_sign:
        daily_guidance = f"""
        Today your {sun_sign} Sun pushes you toward expression,
        while your {moon_sign} Moon sets the emotional tone.
        Your Rising sign, {rising_sign}, shapes how you show up.
        Use these energies wisely—slow down, observe your body,
        and follow where your intuition feels open and expansive.
        """

    return render(
        request,
        "core/natal_chart.html",
        {
            "profile": profile,
            "chart": chart,
            "transits": transits,
            "daily_guidance": daily_guidance,
        },
    )



# ---------------------------
# AUTH VIEWS
# ---------------------------
def registration_view(request):
    if request.method == "POST":

        # Form values
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone")

        dob = request.POST.get("dob")
        tob = request.POST.get("tob")

        birth_city = request.POST.get("birth_city")
        birth_lat = request.POST.get("birth_latitude")
        birth_lon = request.POST.get("birth_longitude")
        birth_tz = request.POST.get("birth_timezone")

        # 1️⃣ Create Django auth user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # 2️⃣ Create UserProfile linked to the user
        profile = UserProfile.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            birth_date=dob,
            birth_time=tob,
            birth_city=birth_city,
            birth_latitude=birth_lat,
            birth_longitude=birth_lon,
            birth_timezone=birth_tz,
        )

        # 3️⃣ Log the user in automatically
        login(request, user)

        messages.success(request, "Account created successfully!")
        return redirect("dashboard")

    return render(request, "core/registration.html")





def login_view(request):
    return render(request, "core/login.html")

#settings 
@login_required
def settings_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    # Ensure Preference Model Exists
    user_pref, _ = UserPreference.objects.get_or_create(user_profile=profile)

    if request.method == "POST":

        # Notifications
        user_pref.notify_burnout_risk = bool(request.POST.get("notify_burnout"))
        user_pref.notify_astrological_events = bool(request.POST.get("notify_astrology"))
        user_pref.device_sync_enabled = bool(request.POST.get("device_sync"))

        # Appearance
        user_pref.dark_mode = bool(request.POST.get("dark_mode"))

        # Feedback
        feedback = request.POST.get("feedback")
        feature_request = request.POST.get("feature_request")
        rating = request.POST.get("rating")

        if feedback or feature_request:
            UserFeedback.objects.create(
                user_profile=profile,
                rating=rating or 5,
                comments=feedback,
                feature_requests=feature_request,
            )

        user_pref.save()

        return render(request, "core/settings.html", {
            "success": True,
            "user_pref": user_pref,
        })

    return render(request, "core/settings.html", {
        "user_pref": user_pref,
    })



from django.http import JsonResponse


def toggle_dark_mode_view(request):
    """AJAX endpoint to toggle dark mode and persist preference for current profile."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    profile = UserProfile.objects.first()
    if not profile:
        return JsonResponse({"error": "No profile found"}, status=404)

    user_pref, _ = UserPreference.objects.get_or_create(user_profile=profile)
    # Toggle based on posted value
    value = request.POST.get("dark_mode")
    if value is None:
        return JsonResponse({"error": "dark_mode required"}, status=400)

    user_pref.dark_mode = value.lower() in ("1", "true", "yes", "on")
    user_pref.save()
    return JsonResponse({"dark_mode": user_pref.dark_mode})

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")

def burnout_api(request):
    heart_rate = int(request.GET.get("heart_rate"))
    hrv_score = float(request.GET.get("hrv_score"))
    sleep_hours = float(request.GET.get("sleep_hours"))
    activity_level = int(request.GET.get("activity_level"))
    stress_level = int(request.GET.get("stress_level"))
    transit_planet = request.GET.get("transit_planet")
    natal_house = request.GET.get("natal_house")
    sleep_quality = request.GET.get("sleep_quality")

    # Run AI prediction
    category, score = predict_burnout(
        heart_rate=heart_rate,
        hrv_score=hrv_score,
        sleep_hours=sleep_hours,
        activity_level=activity_level,
        stress_level=stress_level,
        transit_planet=transit_planet,
        natal_house=natal_house,
        sleep_quality=sleep_quality
    )

    # TEMP: assign to test user (replace later with request.user)
    user = UserProfile.objects.first()

    # Save prediction to database
    AIPrediction.objects.create(
        user_profile=user,
        prediction_date=date.today(),
        prediction_burnout_risk=score,
        predicted_burnout_level=category,
        contributing_factors=f"HR={heart_rate}, HRV={hrv_score}, Sleep={sleep_hours}",
        recommendations="AI suggests rest, hydration, meditation.",
        meditation_link="https://calm.com/meditation"
    )

    return JsonResponse({
        "burnout_category": category,
        "burnout_score": round(score * 100, 2)
    })
    
def add_biometric_view(request):
    if request.method == "POST":
        profile = UserProfile.objects.first()  # temporary until auth is complete

        BiometricData.objects.create(
            user_profile=profile,
            heart_rate=request.POST.get("heart_rate"),
            hrv_score=request.POST.get("hrv_score"),
            sleep_hours=request.POST.get("sleep_hours"),
            activity_level=request.POST.get("activity_level"),
            stress_index=request.POST.get("stress_index"),
        )

        messages.success(request, "Biometric data added successfully!")
        return redirect("dashboard")

    return redirect("dashboard")

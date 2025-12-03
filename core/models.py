from django.db import models


# -------------------------------------------------------
# 1. USER PROFILE (standalone — no Django auth)
# -------------------------------------------------------
class UserProfile(models.Model):

    full_name = models.CharField(max_length=100)

    # Contact info
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    # Birth data
    birth_date = models.DateField(null=True, blank=True)
    birth_time = models.TimeField(null=True, blank=True)

    birth_city = models.CharField(max_length=100, null=True, blank=True)
    birth_state = models.CharField(max_length=100, null=True, blank=True)
    birth_country = models.CharField(max_length=100, null=True, blank=True)

    birth_latitude = models.FloatField(null=True, blank=True)
    birth_longitude = models.FloatField(null=True, blank=True)
    birth_timezone = models.FloatField(null=True, blank=True)

    # Device info
    wearable_device_type = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.full_name


# -------------------------------------------------------
# 2. BIOMETRIC DATA
# -------------------------------------------------------
class BiometricData(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    heart_rate = models.IntegerField(null=True, blank=True)
    hrv_score = models.FloatField(null=True, blank=True)
    sleep_hours = models.FloatField(null=True, blank=True)
    activity_level = models.IntegerField(null=True, blank=True)

    sleep_quality = models.CharField(max_length=50, null=True, blank=True)
    sleep_duration = models.FloatField(null=True, blank=True)

    # Used in dashboard + AI formula
    stress_level = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Biometric Data for {self.user_profile.full_name} at {self.timestamp}"


# -------------------------------------------------------
# 3. ASTROLOGICAL TRANSIT DATA
# -------------------------------------------------------
class AstrologicalTransit(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    transit_date = models.DateField()
    transit_planet = models.CharField(max_length=50)
    natal_house = models.CharField(max_length=50, default="1st")
    ruled_houses = models.CharField(max_length=50, default="1st")

    interpretation = models.TextField()

    def __str__(self):
        return f"{self.transit_planet} in {self.natal_house} for {self.user_profile.full_name}"


# -------------------------------------------------------
# 4. NATAL CHART
# -------------------------------------------------------
class NatalChart(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)

    sun_sign = models.CharField(max_length=50)
    moon_sign = models.CharField(max_length=50)
    rising_sign = models.CharField(max_length=50)

    key_aspects = models.TextField()
    houses = models.TextField()
    generated_chart_url = models.URLField(null=True, blank=True)
    raw_chart_data = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Natal Chart for {self.user_profile.full_name}"


# -------------------------------------------------------
# 5. AI PREDICTION DATA
# -------------------------------------------------------
class AIPrediction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    prediction_date = models.DateField()
    prediction_burnout_risk = models.FloatField()
    predicted_burnout_level = models.CharField(max_length=50)

    contributing_factors = models.TextField()
    recommendations = models.TextField()

    meditation_link = models.URLField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.user_profile.full_name} on {self.prediction_date}"


# -------------------------------------------------------
# 6. ALERTS
# -------------------------------------------------------
class Alert(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    alert_date = models.DateField(auto_now_add=True)
    alert_type = models.CharField(max_length=100)
    alert_message = models.TextField()

    related_prediction = models.ForeignKey(AIPrediction, on_delete=models.CASCADE, null=True, blank=True)

    burnout_percentage = models.FloatField(null=True, blank=True)
    recommended_action = models.TextField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.user_profile.full_name}"


# -------------------------------------------------------
# 7. TEAM MEMBER ACCESS
# -------------------------------------------------------
class TeamMember(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    member_name = models.CharField(max_length=100)
    member_email = models.EmailField()

    access_level = models.CharField(max_length=50)
    added_on = models.DateTimeField(auto_now_add=True)

    can_receive_alerts = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member_name} for {self.user_profile.full_name}"


# -------------------------------------------------------
# 8. USER PREFERENCES
# -------------------------------------------------------
class UserPreference(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)

    notify_burnout_risk = models.BooleanField(default=True)
    notify_astrological_events = models.BooleanField(default=True)

    data_sharing_consent = models.BooleanField(default=False)
    preferred_notification_method = models.CharField(
        max_length=50,
        choices=[("Email", "Email"), ("SMS", "SMS"), ("App", "App Notification")],
        default="Email"
    )

    device_sync_enabled = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)

    language_preference = models.CharField(max_length=50, default="English")
    astrology_opt_in = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user_profile.full_name}"


# -------------------------------------------------------
# 9. FEEDBACK
# -------------------------------------------------------
class UserFeedback(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    feedback_date = models.DateTimeField(auto_now_add=True)

    rating = models.IntegerField()
    comments = models.TextField()
    feature_requests = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Feedback from {self.user_profile.full_name}"

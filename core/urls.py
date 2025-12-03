from django.urls import path
from .views import (
    registration_view,
    dashboard_view,
    add_biometric_view,
    burnout_api,
    burnout_report_view,
    natal_chart_view,
    settings_view,
    login_view,
)

urlpatterns = [
    path("register/", registration_view, name="register"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("add-biometric/", add_biometric_view, name="add_biometric"),
    path("predict_burnout/", burnout_api, name="predict_burnout"),
    path("reports/", burnout_report_view, name="reports"),
    path("natal/<str:full_name>/", natal_chart_view, name="natal_chart"),
    path("settings/", settings_view, name="settings"),
    path("login/", login_view, name="login"),
]


from django.urls import path
from . import views
from .views import burnout_api


urlpatterns = [
    # Make login page the default landing page
    path("", views.login_view, name="login"),
    
    path("add_biometric/", views.add_biometric_view, name="add_biometric"),

    # Main Dashboard (protected)
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Reports Page (protected)
    path("reports/", views.burnout_report_view, name="reports"),
    
    path("predict_burnout/", burnout_api, name="predict_burnout"),

    # Natal Chart Page (protected)
    path("natal/<str:full_name>/", views.natal_chart_view, name="natal_chart"),

    # Settings Page (protected)
    path("settings/", views.settings_view, name="settings"),
    path("settings/toggle-dark-mode/", views.toggle_dark_mode_view, name="toggle_dark_mode"),

    # User Registration Page
    path("register/", views.registration_view, name="register"),

    # Login Page
    path("login/", views.login_view, name="login"),

    # Logout page
    path("logout/", views.logout_view, name="logout"), #redirect to login after logout
]

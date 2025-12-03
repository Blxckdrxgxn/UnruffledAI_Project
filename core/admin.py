from django.contrib import admin
from .models import (
    UserProfile, BiometricData, AstrologicalTransit, NatalChart,
    AIPrediction, Alert, TeamMember, UserPreference, UserFeedback
)
from .forms import UserProfileForm

# Custom admin with form for AM/PM birth_time support
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm

# Custom admin for astrological transit table
class AstrologicalTransitAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'transit_date', 'transit_planet', 'natal_house')
    search_fields = ('user_profile__full_name', 'transit_planet', 'natal_house')
    list_filter = ('transit_planet', 'transit_date')

# Register everything
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BiometricData)
admin.site.register(AstrologicalTransit, AstrologicalTransitAdmin)
admin.site.register(NatalChart)
admin.site.register(AIPrediction)
admin.site.register(Alert)
admin.site.register(TeamMember)
admin.site.register(UserPreference)
admin.site.register(UserFeedback)


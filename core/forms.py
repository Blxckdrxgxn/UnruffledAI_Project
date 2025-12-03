from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'

    # override birth_time field to support AM/PM format
    birth_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=['%I:%M %p', '%H:%M']
    )

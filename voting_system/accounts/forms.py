from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, AdminProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("surname", "name", "patronymic", "oblast", "city", "address")

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ("surname", "name", "patronymic", "country_of_origin", "institution")

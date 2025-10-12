from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    surname = models.CharField(max_length=100)          # Прізвище
    name = models.CharField(max_length=100)             # Ім'я
    patronymic = models.CharField(max_length=100, blank=True)  # По батькові (можна порожнім)
    oblast = models.CharField(max_length=100)           # Область
    city = models.CharField(max_length=100)             # Місто
    address = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.surname} {self.name} ({self.user.username})"

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")
    surname = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True)
    country_of_origin = models.CharField(max_length=100)  # Країна походження
    institution = models.CharField(max_length=150)        # Інституція

    def __str__(self):
        return f"Admin: {self.surname} {self.name} ({self.user.username})"
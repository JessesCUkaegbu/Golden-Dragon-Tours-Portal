from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True)
    nationality = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} — profile"

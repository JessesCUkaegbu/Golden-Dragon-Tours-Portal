from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models


class Event(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200)
    event_date = models.DateField()
    location = models.CharField(max_length=255)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    tickets_available = models.PositiveIntegerField()
    ticket_image = CloudinaryField('image', blank=True, null=True)
    description = models.TextField()
    payment_phone = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.creator.username}"

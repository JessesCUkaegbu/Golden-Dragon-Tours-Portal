import uuid

from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models


class TourPackage(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_days = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Ticket(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    tour_package = models.ForeignKey(
        TourPackage, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets'
    )
    event = models.ForeignKey(
        'events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets'
    )
    travel_date = models.DateField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    reference_code = models.CharField(max_length=100, unique=True, blank=True)
    barcode_image = CloudinaryField('image', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_reference_code():
        return f"TKT-{uuid.uuid4().hex[:10].upper()}"

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self.generate_reference_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference_code

    @property
    def status_display_class(self):
        return {
            self.STATUS_PENDING: 'pending',
            self.STATUS_CONFIRMED: 'confirmed',
            self.STATUS_CANCELLED: 'cancelled',
        }.get(self.status, 'pending')

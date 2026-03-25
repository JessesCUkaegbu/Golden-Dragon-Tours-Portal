from django.db import models
from django.contrib.auth.models import User
import uuid


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    nationality = models.CharField(max_length=100)
    tour_package = models.CharField(max_length=100)
    travel_date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    reference_code = models.CharField(max_length=100, unique=True, blank=True)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = f"TKT-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference_code
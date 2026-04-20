from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField  # add this import
import uuid



class TourPackage(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_days = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Ticket(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    tour_package = models.ForeignKey(
        TourPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
    event = models.ForeignKey(
        'Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
    travel_date = models.DateField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    reference_code = models.CharField(max_length=100, unique=True, blank=True)
    barcode_image = CloudinaryField('image', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = f"TKT-{uuid.uuid4().hex[:10].upper()}"
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
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30, blank=True)
    nationality = models.CharField(max_length=100, blank=True)


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


class Subscription(models.Model):
    PLAN_FREE = 'free'
    PLAN_STANDARD = 'standard'
    PLAN_PREMIUM = 'premium'

    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_STANDARD, 'Standard'),
        (PLAN_PREMIUM, 'Premium'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PAST_DUE = 'past_due'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_PAST_DUE, 'Past Due'),
    ]

    BUYER_TICKET_LIMITS = {
        PLAN_FREE: 10,
        PLAN_STANDARD: 50,
        PLAN_PREMIUM: None,  # unlimited
    }

    ORGANISER_EVENT_LIMITS = {
        PLAN_FREE: 1,
        PLAN_STANDARD: 10,
        PLAN_PREMIUM: None,  # unlimited
    }

    ORGANISER_ATTENDEE_LIMITS = {
        PLAN_FREE: 10,
        PLAN_STANDARD: 500,
        PLAN_PREMIUM: None,  # unlimited
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.get_plan_display()}"

    @property
    def ticket_limit(self):
        return self.BUYER_TICKET_LIMITS.get(self.plan)

    @property
    def max_events(self):
        return self.ORGANISER_EVENT_LIMITS.get(self.plan)

    @property
    def max_attendees_per_event(self):
        return self.ORGANISER_ATTENDEE_LIMITS.get(self.plan)

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def tickets_this_month(self):
        from django.utils import timezone
        now = timezone.now()
        return Ticket.objects.filter(
            user=self.user,
            created_at__year=now.year,
            created_at__month=now.month
        ).count()

    @property
    def can_create_ticket(self):
        if self.ticket_limit is None:
            return True  # unlimited
        return self.tickets_this_month < self.ticket_limit

    @property
    def active_event_count(self):
        return Event.objects.filter(
            creator=self.user,
            is_active=True
        ).count()

    @property
    def can_create_event(self):
        if self.max_events is None:
            return True
        return self.active_event_count < self.max_events

    @property
    def tickets_remaining(self):
        if self.ticket_limit is None:
            return None  # unlimited
        remaining = self.ticket_limit - self.tickets_this_month
        return max(0, remaining)

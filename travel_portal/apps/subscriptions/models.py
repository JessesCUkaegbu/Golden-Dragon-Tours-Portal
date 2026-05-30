from django.db import models
from django.contrib.auth.models import User


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
        PLAN_PREMIUM: None,
    }

    ORGANISER_EVENT_LIMITS = {
        PLAN_FREE: 1,
        PLAN_STANDARD: 10,
        PLAN_PREMIUM: None,
    }

    ORGANISER_ATTENDEE_LIMITS = {
        PLAN_FREE: 10,
        PLAN_STANDARD: 500,
        PLAN_PREMIUM: None,
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
        return self.user.tickets.filter(
            created_at__year=now.year,
            created_at__month=now.month,
        ).count()

    @property
    def can_create_ticket(self):
        if self.ticket_limit is None:
            return True
        return self.tickets_this_month < self.ticket_limit

    @property
    def active_event_count(self):
        return self.user.events.filter(is_active=True).count()

    @property
    def can_create_event(self):
        if self.max_events is None:
            return True
        return self.active_event_count < self.max_events

    @property
    def tickets_remaining(self):
        if self.ticket_limit is None:
            return None
        return max(0, self.ticket_limit - self.tickets_this_month)

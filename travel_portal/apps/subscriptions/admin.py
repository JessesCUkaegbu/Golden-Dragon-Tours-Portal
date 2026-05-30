from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'tickets_this_month', 'created_at']
    list_filter = ['plan', 'status']
    search_fields = ['user__username', 'stripe_customer_id']
    list_editable = ['plan', 'status']

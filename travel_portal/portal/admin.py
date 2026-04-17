from django.contrib import admin
from .models import Event, Ticket, TourPackage, Subscription


@admin.register(TourPackage)
class TourPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'price', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active', 'price']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['reference_code', 'full_name', 'tour_package', 'travel_date', 'status', 'created_at']
    list_filter = ['status', 'tour_package', 'travel_date']
    search_fields = ['reference_code', 'full_name', 'email']
    list_editable = ['status']
    readonly_fields = ['reference_code', 'barcode_image', 'created_at']
    

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'tickets_this_month', 'created_at']
    list_filter = ['plan', 'status']
    search_fields = ['user__username', 'stripe_customer_id']
    list_editable = ['plan', 'status']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'event_date', 'ticket_price', 'tickets_available', 'is_active']
    list_filter = ['is_active', 'event_date']
    search_fields = ['name', 'location', 'creator__username']
    list_editable = ['is_active']

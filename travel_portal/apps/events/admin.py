from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'event_date', 'ticket_price', 'tickets_available', 'is_active']
    list_filter = ['is_active', 'event_date']
    search_fields = ['name', 'location', 'creator__username']
    list_editable = ['is_active']

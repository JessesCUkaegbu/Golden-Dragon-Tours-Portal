from django.contrib import admin
from .models import Ticket, TourPackage


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
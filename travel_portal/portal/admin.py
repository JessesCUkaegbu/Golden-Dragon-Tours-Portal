from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'full_name', 'email', 'tour_package', 'travel_date', 'created_at')
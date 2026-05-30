from rest_framework import serializers
from .models import Ticket, TourPackage


class TourPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourPackage
        fields = ["id", "name", "description"]


class TicketSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source="event.name", read_only=True, default=None)
    tour_package_name = serializers.CharField(source="tour_package.name", read_only=True, default=None)

    class Meta:
        model = Ticket
        fields = [
            "id", "reference_code", "full_name", "email", "phone",
            "nationality", "quantity", "travel_date", "status",
            "barcode_image", "created_at", "event", "event_name",
            "tour_package", "tour_package_name",
        ]
        read_only_fields = ["id", "reference_code", "barcode_image", "created_at"]

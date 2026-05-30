from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source="creator.username", read_only=True)
    tickets_sold = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id", "name", "description", "event_date", "location",
            "ticket_price", "tickets_available", "ticket_image",
            "payment_phone", "is_active", "created_at",
            "creator_username", "tickets_sold",
        ]
        read_only_fields = ["id", "created_at", "creator_username"]

    def get_tickets_sold(self, obj):
        return obj.tickets.aggregate(total=__import__("django.db.models", fromlist=["Sum"]).Sum("quantity"))["total"] or 0

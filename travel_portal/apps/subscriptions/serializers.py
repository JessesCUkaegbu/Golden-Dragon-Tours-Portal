from rest_framework import serializers
from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_display = serializers.CharField(source="get_plan_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tickets_remaining = serializers.IntegerField(read_only=True)
    can_create_ticket = serializers.BooleanField(read_only=True)
    can_create_event = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "plan", "plan_display", "status", "status_display",
            "stripe_subscription_id", "created_at", "updated_at",
            "tickets_remaining", "can_create_ticket", "can_create_event",
        ]
        read_only_fields = ["id", "stripe_subscription_id", "created_at", "updated_at"]

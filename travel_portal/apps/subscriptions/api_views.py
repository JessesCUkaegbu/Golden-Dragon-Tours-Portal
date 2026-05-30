from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription
from .serializers import SubscriptionSerializer


class SubscriptionAPIView(APIView):
    """Retrieve the current user's subscription details."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={"plan": Subscription.PLAN_FREE, "status": Subscription.STATUS_ACTIVE},
        )
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


class StripeWebhookAPIView(APIView):
    """Stripe webhook endpoint — no authentication, verified by signature."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Delegate to the existing webhook handler
        from .webhook import stripe_webhook
        return stripe_webhook(request)

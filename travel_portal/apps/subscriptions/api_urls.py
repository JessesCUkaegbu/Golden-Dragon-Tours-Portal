from django.urls import path
from .api_views import SubscriptionAPIView, StripeWebhookAPIView

urlpatterns = [
    path("", SubscriptionAPIView.as_view(), name="api_subscription"),
    path("webhook/", StripeWebhookAPIView.as_view(), name="api_stripe_webhook"),
]

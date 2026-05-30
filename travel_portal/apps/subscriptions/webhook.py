import logging

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Subscription

logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith("sk_"):
        logger.error("Stripe webhook called without a valid secret key configured.")
        return HttpResponse(status=500)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "customer.subscription.deleted":
        subscription_data = event["data"]["object"]
        try:
            sub = Subscription.objects.get(stripe_subscription_id=subscription_data["id"])
            sub.plan = Subscription.PLAN_FREE
            sub.status = Subscription.STATUS_CANCELLED
            sub.save()
        except Subscription.DoesNotExist:
            pass

    elif event["type"] == "customer.subscription.updated":
        subscription_data = event["data"]["object"]
        try:
            sub = Subscription.objects.get(stripe_subscription_id=subscription_data["id"])
            sub.status = subscription_data["status"]
            sub.save()
        except Subscription.DoesNotExist:
            pass

    return HttpResponse(status=200)

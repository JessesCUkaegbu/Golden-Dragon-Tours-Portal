import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


def get_stripe_price_id(plan):
    price_map = {
        "standard": settings.STRIPE_STANDARD_PRICE_ID,
        "premium": settings.STRIPE_PREMIUM_PRICE_ID,
    }
    return price_map.get(plan)


def validate_stripe_config(plan):
    secret_key = settings.STRIPE_SECRET_KEY
    price_id = get_stripe_price_id(plan)

    if not secret_key or not secret_key.startswith("sk_"):
        return None, "Stripe is not configured correctly yet. Please update STRIPE_SECRET_KEY in your .env file."

    if not price_id or not price_id.startswith("price_"):
        return None, f"The Stripe price for the {plan.title()} plan is missing or invalid. Please update your .env file."

    return price_id, None

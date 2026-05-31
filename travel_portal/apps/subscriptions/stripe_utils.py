import logging

import stripe
from django.conf import settings
from django.utils import timezone

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


# Stripe statuses that mean the subscription is still usable
_ACTIVE_STRIPE_STATUSES = {"active", "trialing"}

# Stripe statuses that mean payment is overdue but not yet fully cancelled
_PAST_DUE_STRIPE_STATUSES = {"past_due", "unpaid"}

# Stripe statuses that mean the subscription is dead — downgrade to free
_CANCELLED_STRIPE_STATUSES = {"canceled", "incomplete_expired", "incomplete"}


def sync_subscription_with_stripe(subscription):
    """Verify a paid subscription's status against Stripe and update locally if it has changed.

    Strategy:
    1. Skip free-plan users and users without a Stripe subscription ID — nothing to check.
    2. Fast-path: if current_period_end is set and already in the past, downgrade immediately
       without an API call (the subscription is definitely expired).
    3. Otherwise, call the Stripe API to get the live status and reconcile.

    This is called on every login for paid users so that a missed webhook never leaves a user
    with premium access they are no longer paying for.

    Returns True if a change was made, False otherwise.
    Logs but never raises — a Stripe outage must not block login.
    """
    from .models import Subscription  # local import avoids circular dependency

    if subscription.plan == Subscription.PLAN_FREE:
        return False

    if not subscription.stripe_subscription_id:
        return False

    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith("sk_"):
        logger.warning("Stripe sync skipped for user %s — STRIPE_SECRET_KEY not configured.", subscription.user_id)
        return False

    # Fast-path: period already ended — downgrade without an API call
    if subscription.current_period_end and subscription.current_period_end < timezone.now():
        logger.info(
            "Subscription for user %s expired at %s (detected on login, no API call).",
            subscription.user_id,
            subscription.current_period_end,
        )
        return _downgrade_to_free(subscription)

    # Slow-path: ask Stripe for the live status
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        return _reconcile_status(subscription, stripe_sub["status"])
    except stripe.error.InvalidRequestError:
        # Subscription ID no longer exists on Stripe (e.g. deleted via dashboard)
        logger.warning(
            "Stripe subscription %s not found for user %s — downgrading to free.",
            subscription.stripe_subscription_id,
            subscription.user_id,
        )
        return _downgrade_to_free(subscription)
    except Exception:
        logger.exception(
            "Stripe sync failed for user %s — login not blocked, status unchanged.",
            subscription.user_id,
        )
        return False


def _reconcile_status(subscription, stripe_status):
    """Apply a Stripe status string to the local Subscription and save if anything changed."""
    from .models import Subscription  # local import avoids circular dependency

    if stripe_status in _ACTIVE_STRIPE_STATUSES:
        if subscription.status == Subscription.STATUS_ACTIVE:
            return False  # already correct
        subscription.status = Subscription.STATUS_ACTIVE
        subscription.save(update_fields=["status", "updated_at"])
        logger.info("Subscription for user %s restored to active via Stripe sync.", subscription.user_id)
        return True

    if stripe_status in _PAST_DUE_STRIPE_STATUSES:
        if subscription.status == Subscription.STATUS_PAST_DUE:
            return False
        subscription.status = Subscription.STATUS_PAST_DUE
        subscription.save(update_fields=["status", "updated_at"])
        logger.info("Subscription for user %s marked past_due via Stripe sync.", subscription.user_id)
        return True

    # cancelled / incomplete_expired / anything else → downgrade
    return _downgrade_to_free(subscription)


def _downgrade_to_free(subscription):
    """Downgrade subscription to the free plan and mark it cancelled."""
    from .models import Subscription  # local import avoids circular dependency

    if subscription.plan == Subscription.PLAN_FREE and subscription.status == Subscription.STATUS_CANCELLED:
        return False  # already downgraded

    subscription.plan = Subscription.PLAN_FREE
    subscription.status = Subscription.STATUS_CANCELLED
    subscription.save(update_fields=["plan", "status", "updated_at"])
    logger.info("Subscription for user %s downgraded to free via Stripe sync.", subscription.user_id)
    return True

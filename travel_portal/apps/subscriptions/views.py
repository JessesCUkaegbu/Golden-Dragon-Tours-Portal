import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Subscription
from .stripe_utils import validate_stripe_config

logger = logging.getLogger(__name__)


def _get_or_create_subscription(user):
    return Subscription.objects.get_or_create(
        user=user,
        defaults={"plan": Subscription.PLAN_FREE, "status": Subscription.STATUS_ACTIVE},
    )[0]


def pricing_view(request):
    subscription = None
    if request.user.is_authenticated:
        subscription = _get_or_create_subscription(request.user)
    return render(
        request,
        "subscriptions/pricing.html",
        {"stripe_public_key": settings.STRIPE_PUBLIC_KEY, "subscription": subscription},
    )


@login_required
def create_checkout_session(request, plan):
    price_id, config_error = validate_stripe_config(plan)
    if config_error:
        messages.error(request, config_error)
        return redirect("pricing")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=request.build_absolute_uri("/subscription/success/") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri("/pricing/"),
            metadata={"user_id": request.user.id, "plan": plan},
        )
        return redirect(checkout_session.url, code=303)
    except stripe.error.StripeError:
        logger.exception("Stripe checkout failed for user %s on %s plan.", request.user.id, plan)
        messages.error(request, "We could not start the payment session right now. Please verify your Stripe keys and price IDs, then try again.")
        return redirect("pricing")
    except Exception:
        logger.exception("Unexpected checkout failure for user %s on %s plan.", request.user.id, plan)
        messages.error(request, "Something went wrong while starting checkout. Please try again.")
        return redirect("pricing")


@login_required
def subscription_success(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return redirect("dashboard")

    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith("sk_"):
        messages.error(request, "Stripe is not configured correctly yet.")
        return redirect("pricing")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = getattr(session, "metadata", None)
        plan = metadata["plan"] if metadata and "plan" in metadata else Subscription.PLAN_FREE

        if plan not in {Subscription.PLAN_FREE, Subscription.PLAN_STANDARD, Subscription.PLAN_PREMIUM}:
            plan = Subscription.PLAN_FREE

        sub = _get_or_create_subscription(request.user)
        sub.plan = plan
        sub.status = "active"
        sub.stripe_customer_id = session.customer
        sub.stripe_subscription_id = session.subscription
        sub.save()
        messages.success(request, f"Successfully subscribed to the {plan.title()} plan!")
    except stripe.error.StripeError:
        logger.exception("Stripe subscription activation failed for user %s.", request.user.id)
        messages.error(request, "Your payment was received, but we could not confirm the subscription yet. Please contact support.")
    except Exception:
        logger.exception("Unexpected subscription activation failure for user %s.", request.user.id)
        messages.error(request, "Something went wrong while activating your subscription.")

    return redirect("dashboard")


@login_required
def cancel_subscription(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith("sk_"):
        messages.error(request, "Stripe is not configured correctly yet.")
        return redirect("pricing")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        sub = request.user.subscription
        if sub.stripe_subscription_id:
            stripe.Subscription.cancel(sub.stripe_subscription_id)
        sub.plan = Subscription.PLAN_FREE
        sub.status = Subscription.STATUS_CANCELLED
        sub.stripe_subscription_id = None
        sub.save()
        messages.success(request, "Subscription cancelled. You have been moved to the Free plan.")
    except stripe.error.StripeError:
        logger.exception("Stripe cancellation failed for user %s.", request.user.id)
        messages.error(request, "We could not cancel the subscription in Stripe right now. Please try again.")
    except Exception:
        logger.exception("Unexpected subscription cancellation failure for user %s.", request.user.id)
        messages.error(request, "Something went wrong while cancelling your subscription.")

    return redirect("dashboard")

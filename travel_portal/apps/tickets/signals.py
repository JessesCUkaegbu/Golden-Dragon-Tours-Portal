import logging

from django.db import transaction
from django.db.models import F
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Ticket

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Ticket)
def _capture_previous_status(sender, instance, **kwargs):
    """Store the previous status on the instance so post_save can detect cancellations.

    Attaches `_previous_status` to the in-memory instance only — never persisted.
    """
    if instance.pk:
        try:
            instance._previous_status = Ticket.objects.values_list(
                "status", flat=True
            ).get(pk=instance.pk)
        except Ticket.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Ticket)
def _update_event_availability(sender, instance, created, **kwargs):
    """Keep Event.tickets_available in sync with actual ticket sales.

    - New ticket  → decrement by ticket.quantity (clamped to 0).
    - Cancelled   → increment back by ticket.quantity.

    All updates use F() expressions so the arithmetic happens at the database
    level — safe under concurrent requests without a SELECT before the UPDATE.
    """
    if not instance.event_id:
        return

    from apps.events.models import Event  # local import avoids circular dependency

    if created:
        # Decrement, but never go below 0
        with transaction.atomic():
            Event.objects.filter(pk=instance.event_id).update(
                tickets_available=F("tickets_available") - instance.quantity
            )
            # Clamp to 0 in case of any edge-case oversell
            Event.objects.filter(pk=instance.event_id, tickets_available__lt=0).update(
                tickets_available=0
            )
        logger.debug(
            "tickets_available decremented by %s for event %s (ticket %s)",
            instance.quantity,
            instance.event_id,
            instance.reference_code,
        )
        return

    # Status change to cancelled — refund the seats
    previous = getattr(instance, "_previous_status", None)
    if previous != Ticket.STATUS_CANCELLED and instance.status == Ticket.STATUS_CANCELLED:
        Event.objects.filter(pk=instance.event_id).update(
            tickets_available=F("tickets_available") + instance.quantity
        )
        logger.debug(
            "tickets_available incremented by %s for event %s (ticket %s cancelled)",
            instance.quantity,
            instance.event_id,
            instance.reference_code,
        )

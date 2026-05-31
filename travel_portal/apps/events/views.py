from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.subscriptions.models import Subscription
from apps.tickets.forms import TicketForm
from apps.tickets.models import Ticket

from .forms import EventForm
from .models import Event


def _get_or_create_subscription(user):
    return Subscription.objects.get_or_create(
        user=user,
        defaults={"plan": Subscription.PLAN_FREE, "status": Subscription.STATUS_ACTIVE},
    )[0]


def event_list(request):
    qs = Event.objects.filter(is_active=True).order_by("event_date", "-created_at")

    # Server-side filtering — these params make URLs bookmarkable and work without JS
    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    location = request.GET.get("location", "").strip()

    if q:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))
    if location:
        qs = qs.filter(location__icontains=location)
    if date_from:
        try:
            qs = qs.filter(event_date__gte=date_from)
        except (ValueError, TypeError):
            pass
    if date_to:
        try:
            qs = qs.filter(event_date__lte=date_to)
        except (ValueError, TypeError):
            pass

    class EventTicketForm(TicketForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["tour_package"].required = False
            self.fields["travel_date"].required = False
            self.fields["nationality"].required = False

    form = EventTicketForm()
    return render(request, "events/event_list.html", {
        "events": qs,
        "form": form,
        "q": q,
        "date_from": date_from,
        "date_to": date_to,
        "location": location,
    })


@login_required
def event_studio(request):
    subscription = _get_or_create_subscription(request.user)
    events = Event.objects.filter(creator=request.user).order_by("-created_at")
    selected_event_id = request.GET.get("event")
    sold_tickets = (
        Ticket.objects.filter(event__creator=request.user)
        .select_related("event", "user")
        .order_by("-created_at")
    )
    if selected_event_id:
        sold_tickets = sold_tickets.filter(event_id=selected_event_id)

    return render(request, "events/event_studio.html", {
        "event_form": EventForm(),
        "events": events,
        "sold_tickets": sold_tickets,
        "subscription": subscription,
        "can_create_event": subscription.can_create_event,
        "active_event_count": subscription.active_event_count,
        "max_events": subscription.max_events,
        "selected_event_id": str(selected_event_id) if selected_event_id else "",
    })


@login_required
def create_event(request):
    subscription = _get_or_create_subscription(request.user)

    if request.method != "POST":
        return redirect("event_studio")

    if not subscription.can_create_event:
        messages.error(
            request,
            f"You have reached your limit of {subscription.max_events} active event(s) "
            f"on the {subscription.get_plan_display()} plan. Upgrade to publish more events."
        )
        return redirect("pricing")

    form = EventForm(request.POST, request.FILES)
    if form.is_valid():
        event = form.save(commit=False)
        event.creator = request.user
        event.save()
        messages.success(request, f"{event.name} was created successfully.")
        return redirect("event_studio")

    events = Event.objects.filter(creator=request.user).order_by("-created_at")
    return render(request, "events/event_studio.html", {
        "event_form": form,
        "events": events,
        "sold_tickets": Ticket.objects.filter(event__creator=request.user).select_related("event", "user").order_by("-created_at"),
        "subscription": subscription,
        "active_event_count": subscription.active_event_count,
        "max_events": subscription.max_events,
        "can_create_event": subscription.can_create_event,
        "open_event_modal": True,
        "editing_event_id": None,
    })


@login_required
def edit_event(request, event_id):
    subscription = _get_or_create_subscription(request.user)
    can_create_events = (
        subscription.plan in {Subscription.PLAN_STANDARD, Subscription.PLAN_PREMIUM}
        and subscription.is_active
    )

    if not can_create_events:
        messages.error(request, "Upgrade to the Standard or Premium plan to create events.")
        return redirect("pricing")

    event = get_object_or_404(Event, id=event_id, creator=request.user)
    if request.method != "POST":
        return redirect("event_studio")

    form = EventForm(request.POST, request.FILES, instance=event)
    if form.is_valid():
        form.save()
        messages.success(request, f"{event.name} was updated successfully.")
        return redirect("event_studio")

    events = Event.objects.filter(creator=request.user).order_by("-created_at")
    return render(request, "events/event_studio.html", {
        "event_form": form,
        "events": events,
        "sold_tickets": Ticket.objects.filter(event__creator=request.user).select_related("event", "user").order_by("-created_at"),
        "subscription": subscription,
        "active_event_count": subscription.active_event_count,
        "max_events": subscription.max_events,
        "can_create_event": subscription.can_create_event,
        "open_event_modal": True,
        "editing_event_id": event.id,
    })


@login_required
@require_POST
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, creator=request.user)
    event_name = event.name
    event.delete()
    messages.success(request, f"{event_name} was deleted successfully.")
    return redirect("event_studio")


@login_required
@require_POST
def update_event_ticket_status(request, ticket_id, status):
    if status not in {Ticket.STATUS_CONFIRMED, Ticket.STATUS_CANCELLED}:
        messages.error(request, "Invalid ticket status update.")
        return redirect("event_studio")

    ticket = get_object_or_404(
        Ticket.objects.select_related("event"),
        id=ticket_id,
        event__creator=request.user,
    )
    ticket.status = status
    ticket.save(update_fields=["status"])

    action_label = "confirmed" if status == Ticket.STATUS_CONFIRMED else "cancelled"
    messages.success(request, f"Ticket {ticket.reference_code} was {action_label}.")

    event_id = request.POST.get("event_id")
    if event_id:
        from django.urls import reverse
        return redirect(f"{reverse('event_studio')}?event={event_id}")
    return redirect("event_studio")

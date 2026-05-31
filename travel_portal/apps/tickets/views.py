import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.events.models import Event
from apps.subscriptions.models import Subscription

from .documents import build_ticket_pdf
from .forms import TicketForm
from .models import Ticket
from .services import prepare_barcode, send_confirmation

logger = logging.getLogger(__name__)


DASHBOARD_TICKETS_PER_PAGE = 15


@login_required
def dashboard(request):
    form = TicketForm()
    ticket_qs = Ticket.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(ticket_qs, DASHBOARD_TICKETS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    subscription, _ = Subscription.objects.get_or_create(
        user=request.user,
        defaults={"plan": Subscription.PLAN_FREE, "status": Subscription.STATUS_ACTIVE},
    )
    events = Event.objects.filter(is_active=True).order_by("event_date", "-created_at")
    return render(request, "tickets/dashboard.html", {
        "form": form,
        "tickets": page_obj,          # page_obj is iterable, len() works, and carries pagination metadata
        "page_obj": page_obj,
        "subscription": subscription,
        "events": events,
    })


def _check_event_capacity(event, requested_quantity):
    """Return an error message string if the event is over capacity, otherwise None.

    Reads Event.tickets_available directly — kept accurate by the post_save signal
    in tickets/signals.py, so no aggregation query is needed.
    """
    if event.tickets_available < requested_quantity:
        return (
            f"Not enough tickets available. "
            f"Only {event.tickets_available} ticket(s) remaining for this event."
        )
    return None


def _resolve_event(event_id):
    """Return (event, error_message). error_message is None on success."""
    try:
        return Event.objects.get(id=event_id, is_active=True), None
    except Event.DoesNotExist:
        return None, "Event not found or no longer available."


@login_required
def create_ticket(request):
    sub, _ = Subscription.objects.get_or_create(
        user=request.user,
        defaults={"plan": "free", "status": "active"},
    )

    if not sub.can_create_ticket:
        error = (
            f"You have reached your {sub.ticket_limit} ticket limit for this month "
            f"on the {sub.get_plan_display()} plan."
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error})
        messages.error(request, "Ticket limit reached. Please upgrade your plan.")
        return redirect("pricing")

    if request.method != "POST":
        return redirect("dashboard")

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    event_id = request.POST.get("event_id")
    form = TicketForm(request.POST)

    if not form.is_valid():
        return _form_error_response(request, form, sub, is_ajax, bool(event_id))

    ticket = form.save(commit=False)
    ticket.user = request.user
    ticket.status = "pending"

    if event_id:
        event, err = _resolve_event(event_id)
        if err:
            if is_ajax:
                return JsonResponse({"success": False, "error": err})
            messages.error(request, err)
            return redirect("event_list")

        capacity_err = _check_event_capacity(
            event, form.cleaned_data.get("quantity") or 1
        )
        if capacity_err:
            if is_ajax:
                return JsonResponse({"success": False, "error": capacity_err})
            messages.error(request, capacity_err)
            return redirect("event_list")

        ticket.event = event
        if not ticket.travel_date:
            ticket.travel_date = event.event_date

    prepare_barcode(ticket)  # sets reference_code + barcode_image before first DB write
    ticket.save()

    send_confirmation(
        ticket=ticket,
        dashboard_url=request.build_absolute_uri(reverse("dashboard")),
        download_url=request.build_absolute_uri(reverse("download_ticket_pdf", args=[ticket.id])),
    )

    if is_ajax:
        return JsonResponse({
            "success": True,
            "reference_code": ticket.reference_code,
            "ticket_id": ticket.id,
        })
    messages.success(request, "Ticket created successfully!")
    return redirect("ticket_success", ticket_id=ticket.id)


def _form_error_response(request, form, sub, is_ajax, came_from_events):
    if is_ajax:
        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                if field == "__all__":
                    errors.append(error)
                else:
                    label = form.fields[field].label or field
                    errors.append(f"{label}: {error}")
        return JsonResponse({
            "success": False,
            "error": " | ".join(errors) if errors else "Please fill in all required fields.",
        })

    messages.error(request, "Please fix the errors below.")
    if came_from_events:
        return redirect("event_list")

    tickets = Ticket.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "tickets/dashboard.html", {
        "form": form,
        "tickets": tickets,
        "subscription": sub,
        "open_ticket_modal": True,
    })


@login_required
@require_POST
def cancel_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    if ticket.status != Ticket.STATUS_PENDING:
        messages.error(request, "Only pending tickets can be cancelled.")
        return redirect("dashboard")
    ticket.status = Ticket.STATUS_CANCELLED
    ticket.save(update_fields=["status"])
    messages.success(request, f"Ticket {ticket.reference_code} has been cancelled.")
    return redirect("dashboard")


@login_required
def ticket_success(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    return render(request, "tickets/ticket_success.html", {"ticket": ticket})


@login_required
def download_ticket_pdf(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    pdf_buffer = build_ticket_pdf(ticket)
    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ticket-{ticket.reference_code}.pdf"'
    return response

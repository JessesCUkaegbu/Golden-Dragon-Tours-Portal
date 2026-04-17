from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm, forms
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import stripe
import logging
from django.http import HttpResponse

from .email_utils import send_ticket_confirmation_email, send_welcome_email
from .forms import EventForm, RegisterForm, TicketForm, UserCreationForm
from .models import Event, Ticket, Subscription
from .ticket_documents import build_ticket_pdf

import barcode
import cloudinary.uploader
from barcode.writer import ImageWriter
from io import BytesIO

logger = logging.getLogger(__name__)


def _get_or_create_subscription(user):
    return Subscription.objects.get_or_create(
        user=user,
        defaults={'plan': Subscription.PLAN_FREE, 'status': Subscription.STATUS_ACTIVE}
    )[0]


def _validate_stripe_config(plan):
    price_map = {
        'standard': settings.STRIPE_STANDARD_PRICE_ID,
        'premium': settings.STRIPE_PREMIUM_PRICE_ID,
    }

    secret_key = settings.STRIPE_SECRET_KEY
    price_id = price_map.get(plan)

    if not secret_key or not secret_key.startswith('sk_'):
        return None, 'Stripe is not configured correctly yet. Please update STRIPE_SECRET_KEY in your .env file.'

    if not price_id or not price_id.startswith('price_'):
        return None, f'The Stripe price for the {plan.title()} plan is missing or invalid. Please update your .env file.'

    return price_id, None

def home(request):
    return render(request, 'portal/home.html')


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control custom-input',
            'placeholder': 'Enter email address'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Choose a username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control custom-input',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control custom-input',
            'placeholder': 'Confirm your password'
        })


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            try:
                send_welcome_email(
                    user=user,
                    dashboard_url=request.build_absolute_uri(reverse('dashboard')),
                    login_url=request.build_absolute_uri(reverse('login')),
                )
            except Exception as exc:
                messages.warning(request, f'Account created, but welcome email could not be sent: {exc}')

            messages.success(request, "Account created successfully.")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'portal/register.html', {'form': form})



class PortalAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control custom-input',
            'placeholder': 'Enter username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control custom-input',
            'placeholder': 'Enter password',
        })


class PortalLoginView(LoginView):
    template_name = 'portal/login.html'
    form_class = PortalAuthForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Login successful. Welcome back!')
        return response


    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    form = TicketForm()
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    subscription = _get_or_create_subscription(request.user)
    return render(request, 'portal/dashboard.html', {
        'form': form,
        'tickets': tickets,
        'subscription': subscription,
    })



@login_required
def create_ticket(request):
    # Get or create subscription — defaults to free plan
    sub, created = Subscription.objects.get_or_create(
        user=request.user,
        defaults={'plan': 'free', 'status': 'active'}
    )

    # Check ticket limit before processing form
    if not sub.can_create_ticket:
        limit = sub.ticket_limit
        messages.error(
            request,
            f'You have reached your {limit} ticket limit for this month on the '
            f'{sub.get_plan_display()} plan. Please upgrade to create more tickets.'
        )
        return redirect('pricing')
    
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.status = 'pending'  # always starts as pending
            ticket.save()

            try:
                send_mail(
                    'Ticket Confirmation',
                    f'Hi {ticket.full_name}, your ticket is confirmed!',
                    'goldendragon026@zohomail.com',
                    [ticket.email],
                    fail_silently=False,
                )
            except Exception as exc:
                messages.warning(request, f'Ticket created, but basic confirmation email could not be sent: {exc}')

            try:
                code128 = barcode.get('code128', ticket.reference_code, writer=ImageWriter())
                buffer = BytesIO()
                code128.write(buffer)
                buffer.seek(0)

                result = cloudinary.uploader.upload(
                    buffer,
                    public_id=f"barcodes/{ticket.reference_code}",
                    resource_type="image"
                )
                ticket.barcode_image = result['public_id']
                ticket.save()

            except Exception as e:
                print(f"Barcode generation/upload error: {e}")
                messages.warning(request, f'Ticket created but barcode failed: {e}')

            try:
                send_ticket_confirmation_email(
                    ticket=ticket,
                    dashboard_url=request.build_absolute_uri(reverse('dashboard')),
                    download_url=request.build_absolute_uri(reverse('download_ticket_pdf', args=[ticket.id])),
                )
            except Exception as exc:
                messages.warning(request, f'Ticket created, but confirmation email could not be sent: {exc}')

            messages.success(request, 'Ticket submitted successfully! Status: Pending.')
            return redirect('ticket_success', ticket_id=ticket.id)
        else:
            messages.error(request, 'Please fix the errors below.')
            tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
            return render(
                request,
                'portal/dashboard.html',
                {
                    'form': form,
                    'tickets': tickets,
                    'subscription': sub,
                    'open_ticket_modal': True,
                },
            )

    return redirect('dashboard')





@login_required
def event_studio(request):
    subscription = _get_or_create_subscription(request.user)
    can_create_events = subscription.plan in {Subscription.PLAN_STANDARD, Subscription.PLAN_PREMIUM} and subscription.is_active

    if not can_create_events:
        messages.error(request, 'Upgrade to the Standard or Premium plan to create events.')
        return redirect('pricing')

    events = Event.objects.filter(creator=request.user).order_by('-created_at')
    active_events = events.filter(is_active=True).count()
    return render(request, 'portal/event_studio.html', {
        'event_form': EventForm(),
        'events': events,
        'subscription': subscription,
        'active_events': active_events,
    })


@login_required
def create_event(request):
    subscription = _get_or_create_subscription(request.user)
    can_create_events = subscription.plan in {Subscription.PLAN_STANDARD, Subscription.PLAN_PREMIUM} and subscription.is_active

    if not can_create_events:
        messages.error(request, 'Upgrade to the Standard or Premium plan to create events.')
        return redirect('pricing')

    if request.method != 'POST':
        return redirect('event_studio')

    form = EventForm(request.POST, request.FILES)
    if form.is_valid():
        event = form.save(commit=False)
        event.creator = request.user
        event.save()
        messages.success(request, f'{event.name} was created successfully.')
        return redirect('event_studio')

    events = Event.objects.filter(creator=request.user).order_by('-created_at')
    return render(
        request,
        'portal/event_studio.html',
        {
            'event_form': form,
            'events': events,
            'subscription': subscription,
            'active_events': events.filter(is_active=True).count(),
            'open_event_modal': True,
        },
    )


@login_required
def ticket_success(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    return render(request, 'portal/ticket_success.html', {'ticket': ticket})


@login_required
def download_ticket_pdf(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    pdf_buffer = build_ticket_pdf(ticket)

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket-{ticket.reference_code}.pdf"'
    return response


# ── Pricing Page ─────────────────────────────────────────
def pricing_view(request):
    subscription = None
    if request.user.is_authenticated:
        subscription = _get_or_create_subscription(request.user)

    return render(request, 'portal/pricing.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'subscription': subscription,
    })


@login_required
def create_checkout_session(request, plan):
    price_id, config_error = _validate_stripe_config(plan)
    if config_error:
        messages.error(request, config_error)
        return redirect('pricing')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri('/subscription/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/pricing/'),
            metadata={
                'user_id': request.user.id,
                'plan': plan,
            }
        )
        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError:
        logger.exception('Stripe checkout failed for user %s on %s plan.', request.user.id, plan)
        messages.error(
            request,
            'We could not start the payment session right now. Please verify your Stripe keys and price IDs, then try again.'
        )
        return redirect('pricing')
    except Exception:
        logger.exception('Unexpected checkout failure for user %s on %s plan.', request.user.id, plan)
        messages.error(request, 'Something went wrong while starting checkout. Please try again.')
        return redirect('pricing')


@login_required
def subscription_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('dashboard')

    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith('sk_'):
        messages.error(request, 'Stripe is not configured correctly yet. Please update STRIPE_SECRET_KEY in your .env file.')
        return redirect('pricing')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = getattr(session, 'metadata', None)
        plan = metadata['plan'] if metadata and 'plan' in metadata else Subscription.PLAN_FREE

        if plan not in {
            Subscription.PLAN_FREE,
            Subscription.PLAN_STANDARD,
            Subscription.PLAN_PREMIUM,
        }:
            plan = Subscription.PLAN_FREE

        sub = _get_or_create_subscription(request.user)
        sub.plan = plan
        sub.status = 'active'
        sub.stripe_customer_id = session.customer
        sub.stripe_subscription_id = session.subscription
        sub.save()

        messages.success(request, f'Successfully subscribed to the {plan.title()} plan!')

    except stripe.error.StripeError:
        logger.exception('Stripe subscription activation failed for user %s.', request.user.id)
        messages.error(request, 'Your payment was received, but we could not confirm the subscription yet. Please contact support.')
    except Exception:
        logger.exception('Unexpected subscription activation failure for user %s.', request.user.id)
        messages.error(request, 'Something went wrong while activating your subscription.')

    return redirect('dashboard')


@csrf_exempt
def stripe_webhook(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith('sk_'):
        logger.error('Stripe webhook called without a valid secret key configured.')
        return HttpResponse(status=500)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'customer.subscription.deleted':
        subscription_data = event['data']['object']
        try:
            sub = Subscription.objects.get(
                stripe_subscription_id=subscription_data['id']
            )
            sub.plan = Subscription.PLAN_FREE
            sub.status = Subscription.STATUS_CANCELLED
            sub.save()
        except Subscription.DoesNotExist:
            pass

    elif event['type'] == 'customer.subscription.updated':
        subscription_data = event['data']['object']
        try:
            sub = Subscription.objects.get(
                stripe_subscription_id=subscription_data['id']
            )
            sub.status = subscription_data['status']
            sub.save()
        except Subscription.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
def cancel_subscription(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.startswith('sk_'):
        messages.error(request, 'Stripe is not configured correctly yet. Please update STRIPE_SECRET_KEY in your .env file.')
        return redirect('pricing')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        sub = request.user.subscription
        if sub.stripe_subscription_id:
            stripe.Subscription.cancel(sub.stripe_subscription_id)
        sub.plan = Subscription.PLAN_FREE
        sub.status = Subscription.STATUS_CANCELLED
        sub.stripe_subscription_id = None
        sub.save()
        messages.success(request, 'Subscription cancelled. You have been moved to the Free plan.')
    except stripe.error.StripeError:
        logger.exception('Stripe cancellation failed for user %s.', request.user.id)
        messages.error(request, 'We could not cancel the subscription in Stripe right now. Please try again.')
    except Exception:
        logger.exception('Unexpected subscription cancellation failure for user %s.', request.user.id)
        messages.error(request, 'Something went wrong while cancelling your subscription.')

    return redirect('dashboard')




def event_list(request):
    events = Event.objects.filter(is_active=True).order_by('event_date', '-created_at')
    return render(request, 'portal/events.html', {'events': events})

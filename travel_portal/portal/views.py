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

from .email_utils import send_ticket_confirmation_email, send_welcome_email
from .forms import RegisterForm, TicketForm, UserCreationForm
from .models import Ticket
from .ticket_documents import build_ticket_pdf

import barcode
import cloudinary.uploader
from barcode.writer import ImageWriter
from io import BytesIO


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
    return render(request, 'portal/dashboard.html', {'form': form, 'tickets': tickets})



@login_required
def create_ticket(request):
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
                    'open_ticket_modal': True,
                },
            )

    return redirect('dashboard')



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

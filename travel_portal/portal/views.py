from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.contrib import messages
from .forms import RegisterForm, TicketForm
from .models import Ticket

import os
from io import BytesIO
from django.core.files.base import ContentFile
import barcode
from barcode.writer import ImageWriter




def home(request):
    return render(request, 'portal/home.html')



def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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
            ticket.save()
            # Generate barcode image
            code128 = barcode.get('code128', ticket.reference_code, writer=ImageWriter())
            buffer = BytesIO()
            code128.write(buffer)
            file_name = f"{ticket.reference_code}.png"
            ticket.barcode_image.save(file_name, ContentFile(buffer.getvalue()), save=True)
            
            messages.success(request, 'Ticket created successfully!')
            return redirect('ticket_success', ticket_id=ticket.id)
        else:
            # Show the user what went wrong
            messages.error(request, 'Please fix the errors below.')
            return render(request, 'portal/create_ticket.html', {'form': form})
    
    form = TicketForm()
    return render(request, 'portal/create_ticket.html', {'form': form})




@login_required
def ticket_success(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    return render(request, 'portal/ticket_success.html', {'ticket': ticket})
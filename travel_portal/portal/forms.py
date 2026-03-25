from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'full_name',
            'email',
            'phone',
            'nationality',
            'tour_package',
            'travel_date',
            'quantity'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Enter full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Enter phone number'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Enter nationality'}),
            'tour_package': forms.TextInput(attrs={'class': 'form-control custom-input', 'placeholder': 'e.g. Beijing 3-Day Tour'}),
            'travel_date': forms.DateInput(attrs={'class': 'form-control custom-input', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control custom-input', 'min': 1}),
        }
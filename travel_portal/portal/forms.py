from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket, TourPackage


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

        

class TicketForm(forms.ModelForm):
    tour_package = forms.ModelChoiceField(
        queryset=TourPackage.objects.filter(is_active=True),
        empty_label="— Select a tour package —",
        widget=forms.Select(attrs={
            'class': 'form-control custom-input',
        })
    )

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
            'full_name': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Enter full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Enter email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Enter phone number'
            }),
            'nationality': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Enter nationality'
            }),
            'travel_date': forms.DateInput(attrs={
                'class': 'form-control custom-input',
                'type': 'date'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control custom-input',
                'min': 1
            }),
        }
from django import forms
from .models import Ticket, TourPackage


class TicketForm(forms.ModelForm):
    tour_package = forms.ModelChoiceField(
        queryset=TourPackage.objects.filter(is_active=True),
        empty_label="— Select a ticket category —",
        required=False,
        widget=forms.Select(attrs={"class": "form-control custom-input"}),
    )

    class Meta:
        model = Ticket
        fields = ["full_name", "email", "phone", "nationality", "tour_package", "travel_date", "quantity"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Enter full name"}),
            "email": forms.EmailInput(attrs={"class": "form-control custom-input", "placeholder": "Enter email"}),
            "phone": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Enter phone number"}),
            "nationality": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Enter nationality"}),
            "travel_date": forms.DateInput(attrs={"class": "form-control custom-input", "type": "date"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control custom-input", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nationality"].required = False
        self.fields["travel_date"].required = False

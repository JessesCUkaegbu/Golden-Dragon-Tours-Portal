from django import forms
from django.utils import timezone

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["name", "event_date", "location", "ticket_price", "tickets_available", "ticket_image", "description", "payment_phone"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Enter event name"}),
            "event_date": forms.DateInput(attrs={"class": "form-control custom-input", "type": "date"}),
            "location": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Enter location"}),
            "ticket_price": forms.NumberInput(attrs={"class": "form-control custom-input", "min": 0, "step": "0.01", "placeholder": "Enter ticket price"}),
            "tickets_available": forms.NumberInput(attrs={"class": "form-control custom-input", "min": 1, "placeholder": "Enter number of tickets available"}),
            "ticket_image": forms.ClearableFileInput(attrs={"class": "form-control custom-input"}),
            "description": forms.Textarea(attrs={"class": "form-control custom-input", "placeholder": "Add a short description of the event", "rows": 4}),
            "payment_phone": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Add mobile payment number"}),
        }

    def clean_event_date(self):
        event_date = self.cleaned_data["event_date"]
        if event_date < timezone.localdate():
            raise forms.ValidationError("Event date cannot be in the past.")
        return event_date

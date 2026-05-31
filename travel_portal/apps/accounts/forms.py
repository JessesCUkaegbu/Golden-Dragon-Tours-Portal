from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control custom-input", "placeholder": "Enter email address"}
        )
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control custom-input", "placeholder": "Choose a username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control custom-input", "placeholder": "Create a password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control custom-input", "placeholder": "Confirm your password"}
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Last name"}),
    )

    class Meta:
        model = UserProfile
        fields = ["phone", "nationality"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Phone number"}),
            "nationality": forms.TextInput(attrs={"class": "form-control custom-input", "placeholder": "Nationality"}),
        }


class PortalAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control custom-input", "placeholder": "Enter username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control custom-input", "placeholder": "Enter password"}
        )

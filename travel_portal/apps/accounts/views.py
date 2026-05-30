from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.subscriptions.models import Subscription
from apps.notifications.emails import send_welcome_email

from .forms import PortalAuthForm, RegisterForm


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Subscription.objects.get_or_create(
                user=user,
                defaults={"plan": Subscription.PLAN_FREE, "status": Subscription.STATUS_ACTIVE},
            )
            login(request, user)
            try:
                send_welcome_email(
                    user=user,
                    dashboard_url=request.build_absolute_uri(reverse("dashboard")),
                    login_url=request.build_absolute_uri(reverse("login")),
                )
            except Exception as exc:
                messages.warning(request, f"Account created, but welcome email could not be sent: {exc}")
            messages.success(request, "Account created successfully. Welcome!")
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class PortalLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = PortalAuthForm

    def form_valid(self, form):
        storage = messages.get_messages(self.request)
        for _ in storage:
            pass
        response = super().form_valid(form)
        messages.success(self.request, "Login successful. Welcome back!")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

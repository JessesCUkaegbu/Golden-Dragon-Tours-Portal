from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.subscriptions.models import Subscription
from apps.subscriptions.stripe_utils import sync_subscription_with_stripe
from apps.notifications.emails import send_welcome_email

from .forms import PortalAuthForm, ProfileForm, RegisterForm
from .models import UserProfile


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
        # Clear any stale flash messages before adding the success message
        storage = messages.get_messages(self.request)
        for _ in storage:
            pass

        response = super().form_valid(form)

        # Verify the subscription against Stripe on every login for paid users.
        # If a webhook was missed, this ensures premium access is not kept indefinitely.
        try:
            sub = self.request.user.subscription
            changed = sync_subscription_with_stripe(sub)
            if changed and sub.status != Subscription.STATUS_ACTIVE:
                messages.warning(
                    self.request,
                    "Your subscription is no longer active. You have been moved to the Free plan.",
                )
        except Subscription.DoesNotExist:
            pass  # free user with no subscription row yet — nothing to sync

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


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        # Handle first/last name separately — they live on the User model
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        if form.is_valid():
            form.save()
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save(update_fields=["first_name", "last_name"])
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(
            instance=profile,
            initial={"first_name": request.user.first_name, "last_name": request.user.last_name},
        )

    return render(request, "accounts/profile.html", {"form": form, "profile": profile})

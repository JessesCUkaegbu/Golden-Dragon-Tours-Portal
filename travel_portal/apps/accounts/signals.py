from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=User)
def enforce_unique_email(sender, instance, **kwargs):
    """Prevent saving a User whose email already belongs to a different account.

    The RegisterForm already catches this at validation time, but this signal
    adds a second layer so programmatic saves (shell, admin, API) are also protected.
    """
    if not instance.email:
        return
    qs = User.objects.filter(email=instance.email)
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise ValidationError(f"A user with the email '{instance.email}' already exists.")

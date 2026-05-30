# Celery tasks — wired up once Celery is added to the project.
# from celery import shared_task


# @shared_task
# def send_welcome_email_task(user_id, dashboard_url, login_url):
#     """Send welcome email to a newly registered user asynchronously."""
#     from django.contrib.auth.models import User
#     from .emails import send_welcome_email
#     user = User.objects.get(id=user_id)
#     send_welcome_email(user, dashboard_url, login_url)


# @shared_task
# def send_ticket_confirmation_email_task(ticket_id, dashboard_url, download_url):
#     """Send ticket confirmation email asynchronously."""
#     from apps.tickets.models import Ticket
#     from .emails import send_ticket_confirmation_email
#     ticket = Ticket.objects.get(id=ticket_id)
#     send_ticket_confirmation_email(ticket, dashboard_url, download_url)

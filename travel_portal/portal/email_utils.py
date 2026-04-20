from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .ticket_documents import build_ticket_pdf


def _send_portal_email(subject, to_email, text_template, html_template, context, attachments=None):
    if not to_email:
        return False

    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_body, "text/html")

    for attachment in attachments or []:
        email.attach(*attachment)

    email.send(fail_silently=False)
    return True


def send_welcome_email(user, dashboard_url, login_url):
    context = {
        "user": user,
        "dashboard_url": dashboard_url,
        "login_url": login_url,
    }
    return _send_portal_email(
        subject="Welcome to Golden Dragon Ticketing",
        to_email=user.email,
        text_template="portal/emails/welcome_email.txt",
        html_template="portal/emails/welcome_email.html",
        context=context,
    )


def send_ticket_confirmation_email(ticket, dashboard_url, download_url):
    context = {
        "ticket": ticket,
        "dashboard_url": dashboard_url,
        "download_url": download_url,
    }
    pdf_buffer = build_ticket_pdf(ticket)
    attachment_name = f"ticket-{ticket.reference_code}.pdf"
    attachments = [(attachment_name, pdf_buffer.getvalue(), "application/pdf")]

    return _send_portal_email(
        subject=f"Your Golden Dragon Ticketing ticket {ticket.reference_code}",
        to_email=ticket.email,
        text_template="portal/emails/ticket_confirmation_email.txt",
        html_template="portal/emails/ticket_confirmation_email.html",
        context=context,
        attachments=attachments,
    )

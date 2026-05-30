# Celery tasks — wired up once Celery is added to the project.
# from celery import shared_task
# from .models import Ticket
# from apps.notifications.emails import send_ticket_confirmation_email


# @shared_task
# def generate_barcode_task(ticket_id):
#     """Generate barcode image and upload to Cloudinary for a given ticket."""
#     from io import BytesIO
#     import barcode
#     import cloudinary.uploader
#     from barcode.writer import ImageWriter
#     ticket = Ticket.objects.get(id=ticket_id)
#     code128 = barcode.get("code128", ticket.reference_code, writer=ImageWriter())
#     buffer = BytesIO()
#     code128.write(buffer)
#     buffer.seek(0)
#     result = cloudinary.uploader.upload(
#         buffer,
#         public_id=f"barcodes/{ticket.reference_code}",
#         resource_type="image",
#     )
#     ticket.barcode_image = result["public_id"]
#     ticket.save(update_fields=["barcode_image"])


# @shared_task
# def send_ticket_confirmation_task(ticket_id, dashboard_url, download_url):
#     """Send ticket confirmation email asynchronously."""
#     ticket = Ticket.objects.get(id=ticket_id)
#     send_ticket_confirmation_email(ticket, dashboard_url, download_url)

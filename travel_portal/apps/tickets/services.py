import logging
from io import BytesIO

import barcode
import cloudinary.uploader
from barcode.writer import ImageWriter

from apps.notifications.emails import send_ticket_confirmation_email
from .models import Ticket

logger = logging.getLogger(__name__)


def _build_barcode_buffer(reference_code):
    code128 = barcode.get("code128", reference_code, writer=ImageWriter())
    buffer = BytesIO()
    code128.write(buffer)
    buffer.seek(0)
    return buffer


def prepare_barcode(ticket):
    """Set reference_code and barcode_image on an *unsaved* ticket.

    Generates the reference code if not already set, builds the barcode image,
    uploads it to Cloudinary, and sets ticket.barcode_image — all before the
    first ticket.save() so only one DB write is needed.

    Returns True on success. On failure the reference_code is still set (so the
    ticket can be saved without a barcode), and the error is logged for retry.
    """
    if not ticket.reference_code:
        ticket.reference_code = Ticket.generate_reference_code()

    try:
        buffer = _build_barcode_buffer(ticket.reference_code)
        result = cloudinary.uploader.upload(
            buffer,
            public_id=f"barcodes/{ticket.reference_code}",
            resource_type="image",
        )
        ticket.barcode_image = result["public_id"]
        return True
    except Exception:
        logger.exception(
            "Barcode generation failed for reference %s — ticket will be saved without barcode",
            ticket.reference_code,
        )
        return False


def retry_barcode(ticket):
    """Attempt to generate and upload a barcode for an already-saved ticket that is missing one.

    Writes to the DB on success via update_fields to avoid a full save.
    """
    if ticket.barcode_image:
        return True

    try:
        buffer = _build_barcode_buffer(ticket.reference_code)
        result = cloudinary.uploader.upload(
            buffer,
            public_id=f"barcodes/{ticket.reference_code}",
            resource_type="image",
        )
        ticket.barcode_image = result["public_id"]
        ticket.save(update_fields=["barcode_image"])
        return True
    except Exception:
        logger.exception("Barcode retry failed for ticket %s", ticket.reference_code)
        return False


def send_confirmation(ticket, dashboard_url, download_url):
    """Send the ticket confirmation email with a PDF attachment.

    Returns True on success, False on failure. Failure is logged but never raises
    so a broken email config does not prevent the ticket from being returned to the buyer.
    """
    try:
        send_ticket_confirmation_email(
            ticket=ticket,
            dashboard_url=dashboard_url,
            download_url=download_url,
        )
        return True
    except Exception:
        logger.exception("Confirmation email failed for ticket %s", ticket.reference_code)
        return False

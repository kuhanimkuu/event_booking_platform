from reportlab.pdfgen import canvas
import os
from django.conf import settings

def generate_receipt_pdf(booking):
    filename = f"receipt_{booking.id}.pdf"
    receipt_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
    os.makedirs(receipt_dir, exist_ok=True)

    receipt_path = os.path.join(receipt_dir, filename)

    c = canvas.Canvas(receipt_path)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Event Booking Receipt")
    c.setFont("Helvetica", 12)
    c.drawString(100, 770, f"Booking ID: {booking.id}")
    c.drawString(100, 750, f"User: {booking.user.username}")
    c.drawString(100, 730, f"Event: {booking.ticket.event.title}")
    c.drawString(100, 710, f"Venue: {booking.ticket.event.venue.name}")
    c.drawString(100, 690, f"Date: {booking.ticket.event.date}")
    c.drawString(100, 670, f"Quantity: {booking.quantity}")
    c.drawString(100, 650, f"Payment Status: {booking.payment_status}")
    c.showPage()
    c.save()

    return f"receipts/{filename}" 

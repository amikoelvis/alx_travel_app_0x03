from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking, Payment
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_booking_confirmation_email(booking_id):
    """Send an email to the user after a booking is created."""
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user

        if not user.email:
            logger.warning(f"Booking {booking.id}: User {user.id} has no email. Skipping.")
            return "No recipient email found."

        send_mail(
            subject="Booking Confirmation",
            message=(
                f"Hello {user.username},\n\n"
                f"Your booking (ID: {booking.id}) was successfully created.\n\n"
                f"Destination: {booking.destination}\n"
                f"Date: {booking.date}\n\n"
                "Thank you for booking with us!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Booking confirmation email sent to {user.email} for booking {booking.id}"

    except Booking.DoesNotExist:
        logger.error(f"Booking with id {booking_id} does not exist.")
        return f"Booking {booking_id} not found."


@shared_task
def send_payment_confirmation_email(payment_id):
    """Send an email to the user after a successful payment."""
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        user = booking.user

        if not user.email:
            logger.warning(f"Payment {payment.id}: User {user.id} has no email. Skipping.")
            return "No recipient email found."

        send_mail(
            subject="Booking Payment Confirmation",
            message=(
                f"Hello {user.username},\n\n"
                f"Your payment for booking (ID: {booking.id}) was successful.\n\n"
                "Thank you for choosing our service!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Payment confirmation email sent to {user.email} for payment {payment.id}"

    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} does not exist.")
        return f"Payment {payment_id} not found."

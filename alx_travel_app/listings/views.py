import uuid
import requests
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer

CHAPA_INIT_URL = "https://api.chapa.co/v1/transaction/initialize"
CHAPA_VERIFY_URL = "https://api.chapa.co/v1/transaction/verify"
CHAPA_SECRET_KEY = settings.CHAPA_SECRET_KEY


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        """
        Triggered when a new booking is created.
        Saves booking and sends confirmation email asynchronously via Celery.
        """
        booking = serializer.save()

        # Import inside function to avoid circular imports
        from .tasks import send_booking_confirmation_email
        send_booking_confirmation_email.delay(booking.id)

    @action(detail=True, methods=["post"])
    def initiate_payment(self, request, pk=None):
        """
        Initiate a payment for a booking by calling Chapa API.
        Stores transaction ID and sets status to 'Pending'.
        """
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate unique transaction reference
        tx_ref = str(uuid.uuid4())

        payload = {
            "amount": str(booking.total_price),
            "currency": "ETB",
            "tx_ref": tx_ref,
            "return_url": "http://localhost:8000/api/bookings/payment/callback/",
            "customization[title]": "Booking Payment",
            "customization[description]": f"Payment for booking {booking.id}",
        }

        headers = {"Authorization": f"Bearer {CHAPA_SECRET_KEY}"}
        response = requests.post(CHAPA_INIT_URL, data=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Create Payment with pending status
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                transaction_reference=tx_ref,
                chapa_tx_ref=data["data"]["tx_ref"],
                status="pending",
            )
            serializer = PaymentSerializer(payment)
            return Response(
                {"payment": serializer.data, "checkout_url": data["data"]["checkout_url"]},
                status=status.HTTP_201_CREATED,
            )
        return Response(response.json(), status=response.status_code)

    @action(detail=True, methods=["get"])
    def verify_payment(self, request, pk=None):
        """
        Verify payment status with Chapa and update Payment model.
        """
        try:
            booking = Booking.objects.get(pk=pk)
            payment = Payment.objects.filter(booking=booking).latest("created_at")
        except (Booking.DoesNotExist, Payment.DoesNotExist):
            return Response({"error": "Booking or Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        url = f"{CHAPA_VERIFY_URL}/{payment.transaction_reference}"
        headers = {"Authorization": f"Bearer {CHAPA_SECRET_KEY}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            status_from_chapa = data["data"]["status"]

            if status_from_chapa == "success":
                payment.status = "completed"
                # Send payment confirmation email via Celery
                from .tasks import send_payment_confirmation_email
                send_payment_confirmation_email.delay(payment.id)
            else:
                payment.status = "failed"

            payment.save()
            return Response({"payment_status": payment.status}, status=status.HTTP_200_OK)

        return Response(response.json(), status=response.status_code)


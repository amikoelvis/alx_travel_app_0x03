import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class Listing(models.Model):
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
        db_column='host_id'
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['host']),
        ]

    def __str__(self):
        return self.name


class Booking(models.Model):
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='bookings',
        db_column='property_id'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        db_column='user_id'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELED = 'canceled', 'Canceled'

    status = models.CharField(max_length=10, choices=BookingStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['property']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(end_date__gt=models.F('start_date')), name='check_end_date_gt_start'),
            models.CheckConstraint(check=models.Q(total_price__gte=0), name='check_total_price_positive'),
        ]

    def __str__(self):
        return f"{self.user} - {self.property} ({self.status})"


class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='reviews',
        db_column='property_id'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        db_column='user_id'
    )
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['property']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(rating__gte=1, rating__lte=5), name='check_rating_between_1_and_5')
        ]

    def __str__(self):
        return f"Review by {self.user} on {self.property} - Rating: {self.rating}"


# 🚀 New Payment model for Chapa Integration
class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    tx_ref = models.CharField(max_length=255, unique=True)  # unique reference you generate
    chapa_tx_id = models.CharField(max_length=255, blank=True, null=True)  # Chapa transaction ID
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.tx_ref} for Booking {self.booking.booking_id} - {self.status}"

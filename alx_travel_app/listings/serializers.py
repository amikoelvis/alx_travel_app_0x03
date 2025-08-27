from rest_framework import serializers
from .models import Listing, Booking

class ListingSerializer(serializers.ModelSerializer):
    property_id = serializers.CharField(read_only=True)
    host_id = serializers.CharField(source='host_id', read_only=True)  # UUID of host
    total_bookings = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'property_id',
            'host_id',
            'name',
            'description',
            'location',
            'price_per_night',
            'created_at',
            'updated_at',
            'total_bookings',  # Computed field
        ]
        read_only_fields = ['property_id', 'created_at', 'updated_at']

    def get_total_bookings(self, obj):
        return obj.bookings.count()


class BookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(read_only=True)
    property_id = serializers.CharField(source='property.property_id', read_only=True)
    user_id = serializers.CharField(source='user.id', read_only=True)
    property_name = serializers.SerializerMethodField()
    host_id = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'booking_id',
            'property_id',
            'property_name',     # Nested/computed field
            'host_id',           # Nested/computed field
            'user_id',
            'start_date',
            'end_date',
            'total_price',
            'status',
            'created_at',
        ]
        read_only_fields = ['booking_id', 'created_at']

    def get_property_name(self, obj):
        return obj.property.name

    def get_host_id(self, obj):
        return str(obj.property.host_id)

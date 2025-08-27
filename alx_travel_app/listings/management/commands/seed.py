import uuid
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing

User = get_user_model()

SAMPLE_LOCATIONS = ['Kampala', 'Nairobi', 'Accra', 'Lagos', 'Dar es Salaam']
SAMPLE_TITLES = ['Beach House', 'Mountain Cabin', 'City Apartment', 'Luxury Villa', 'Budget Room']

class Command(BaseCommand):
    help = 'Seed the database with sample Listing data'

    def handle(self, *args, **kwargs):
        users = User.objects.all()

        if not users.exists():
            self.stdout.write(self.style.ERROR('❌ No users found. Please create users first.'))
            return

        for _ in range(10):  # create 10 listings
            host = random.choice(users)
            listing = Listing.objects.create(
                property_id=uuid.uuid4(),
                host=host,
                name=f"{random.choice(SAMPLE_TITLES)} #{random.randint(100, 999)}",
                description="A beautiful place to stay. Includes all amenities.",
                location=random.choice(SAMPLE_LOCATIONS),
                price_per_night=round(random.uniform(25.0, 200.0), 2),
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created Listing: {listing.name} for Host ID {host.id}'))

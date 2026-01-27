from django.core.management.base import BaseCommand
import random
from accounts.models import User
from product.models import ProductVariant
from wishlist.models import Wishlist, WishlistItem


class Command(BaseCommand):
    help = 'Creates sample wishlist items for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=30,
            help='Number of wishlist items to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing wishlist data before creating sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing wishlist data...'))
            WishlistItem.objects.all().delete()
            Wishlist.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ All wishlist data cleared'))
        
        count = options['count']
        self.stdout.write(f'Creating {count} sample wishlist items...')

        users = list(User.objects.filter(is_active=True))
        variants = list(ProductVariant.objects.filter(is_active=True))

        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return

        if not variants:
            self.stdout.write(self.style.ERROR('No product variants found. Please create products first.'))
            return

        items_created = 0
        wishlists_created = 0

        for i in range(count):
            user = random.choice(users)
            variant = random.choice(variants)

            # Get or create wishlist for user
            wishlist, created = Wishlist.objects.get_or_create(user=user)
            if created:
                wishlists_created += 1

            # Check if item already in wishlist
            if WishlistItem.objects.filter(wishlist=wishlist, product_variant=variant).exists():
                continue

            # Create wishlist item
            WishlistItem.objects.create(
                wishlist=wishlist,
                product_variant=variant,
                price_when_added=variant.price,
                notify_on_price_drop=random.choice([True, False]),
                notify_on_stock=True,
                notes=random.choice([
                    '',
                    'Waiting for sale',
                    'Birthday gift',
                    'Save for later',
                    '',
                    '',
                ])
            )
            items_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Successfully created {items_created} wishlist items'))
        self.stdout.write(self.style.SUCCESS(f'  Created {wishlists_created} new wishlists'))
        self.stdout.write(self.style.SUCCESS(f'  Total wishlists: {Wishlist.objects.count()}'))

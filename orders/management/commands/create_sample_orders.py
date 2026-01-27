from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from accounts.models import User
from orders.models import Order, OrderItem
from product.models import ProductVariant


class Command(BaseCommand):
    help = 'Creates sample orders for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of orders to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing orders before creating sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing orders...'))
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ All orders cleared'))
        
        count = options['count']
        self.stdout.write(f'Creating {count} sample orders...')

        # Get all users
        users = list(User.objects.filter(is_active=True))
        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return

        # Get all active product variants
        variants = list(ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0))
        if not variants:
            self.stdout.write(self.style.ERROR('No product variants found. Please create products first.'))
            return

        # Order statuses with realistic distribution
        status_choices = [
            ('delivered', 40),  # 40% delivered
            ('shipped', 15),    # 15% shipped
            ('processing', 15), # 15% processing
            ('confirmed', 10),  # 10% confirmed
            ('pending', 10),    # 10% pending
            ('cancelled', 8),   # 8% cancelled
            ('refunded', 2),    # 2% refunded
        ]

        payment_status_mapping = {
            'delivered': 'paid',
            'shipped': 'paid',
            'processing': 'paid',
            'confirmed': 'paid',
            'pending': random.choice(['pending', 'paid']),
            'cancelled': random.choice(['pending', 'failed']),
            'refunded': 'refunded',
        }

        # Sample customer data
        cities = [
            ('New York', 'NY', '10001', 'USA'),
            ('Los Angeles', 'CA', '90001', 'USA'),
            ('Chicago', 'IL', '60601', 'USA'),
            ('Houston', 'TX', '77001', 'USA'),
            ('Phoenix', 'AZ', '85001', 'USA'),
            ('Philadelphia', 'PA', '19101', 'USA'),
            ('San Antonio', 'TX', '78201', 'USA'),
            ('San Diego', 'CA', '92101', 'USA'),
            ('Dallas', 'TX', '75201', 'USA'),
            ('San Jose', 'CA', '95101', 'USA'),
        ]

        addresses = [
            '123 Main Street',
            '456 Oak Avenue',
            '789 Pine Road',
            '321 Elm Boulevard',
            '654 Maple Drive',
            '987 Cedar Lane',
            '147 Birch Court',
            '258 Spruce Way',
            '369 Willow Place',
            '741 Cherry Circle',
        ]

        orders_created = 0
        items_created = 0

        # Create orders spread across the last 90 days
        for i in range(count):
            # Random date within last 90 days
            days_ago = random.randint(0, 90)
            order_date = timezone.now() - timedelta(days=days_ago)

            # Select random user
            user = random.choice(users)

            # Select random status based on distribution
            status = random.choices(
                [s[0] for s in status_choices],
                weights=[s[1] for s in status_choices]
            )[0]

            payment_status = payment_status_mapping[status]
            if status == 'pending':
                payment_status = random.choice(['pending', 'paid'])

            # Random shipping info
            city_info = random.choice(cities)
            shipping_address = random.choice(addresses)
            
            # Generate customer name
            shipping_name = f"{user.first_name} {user.last_name}"
            
            # Random number of items in order (1-5)
            num_items = random.randint(1, 5)
            selected_variants = random.sample(variants, min(num_items, len(variants)))

            # Calculate order totals
            subtotal = Decimal('0.00')
            order_items = []

            for variant in selected_variants:
                quantity = random.randint(1, 3)
                price = variant.price
                item_subtotal = price * quantity
                subtotal += item_subtotal

                order_items.append({
                    'variant': variant,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': item_subtotal,
                })

            # Calculate tax and shipping
            tax = subtotal * Decimal('0.08')  # 8% tax
            shipping_cost = Decimal('10.00') if subtotal < 100 else Decimal('0.00')  # Free shipping over $100
            discount = Decimal('0.00')
            
            # Random discount for some orders
            if random.random() < 0.2:  # 20% of orders have discount
                discount = subtotal * Decimal(str(random.uniform(0.05, 0.15)))  # 5-15% discount

            total = subtotal + tax + shipping_cost - discount

            # Create order
            order = Order.objects.create(
                user=user,
                status=status,
                payment_status=payment_status,
                subtotal=subtotal,
                tax=tax,
                shipping_cost=shipping_cost,
                discount=discount,
                total=total,
                shipping_name=shipping_name,
                shipping_email=user.email,
                shipping_phone=f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                shipping_address=shipping_address,
                shipping_city=city_info[0],
                shipping_state=city_info[1],
                shipping_zip=city_info[2],
                shipping_country=city_info[3],
                billing_name=shipping_name,
                billing_address=shipping_address,
                billing_city=city_info[0],
                billing_state=city_info[1],
                billing_zip=city_info[2],
                billing_country=city_info[3],
                notes=random.choice([
                    '', 
                    'Please leave at door', 
                    'Ring doorbell', 
                    'Call upon arrival',
                    'Fragile - Handle with care',
                    '',
                    '',
                ]),
                tracking_number=f"TRK{random.randint(100000000, 999999999)}" if status in ['shipped', 'delivered'] else None,
            )
            
            # Set the created_at to the random date
            Order.objects.filter(pk=order.pk).update(created_at=order_date)

            # Create order items
            for item_data in order_items:
                variant = item_data['variant']
                
                # Get variant attribute names
                variant_attrs = variant.variant_attributes.all()
                variant_name = ', '.join([f"{attr.attribute.name}: {attr.value}" for attr in variant_attrs]) if variant_attrs.exists() else "Standard"

                OrderItem.objects.create(
                    order=order,
                    product_variant=variant,
                    product_name=variant.product.name,
                    variant_name=variant_name,
                    sku=f"SKU-{variant.id}",
                    quantity=item_data['quantity'],
                    price=item_data['price'],
                    subtotal=item_data['subtotal'],
                )
                items_created += 1

            orders_created += 1

            if (i + 1) % 10 == 0:
                self.stdout.write(f'  Created {i + 1}/{count} orders...')

        self.stdout.write(self.style.SUCCESS(f'✓ Successfully created {orders_created} orders with {items_created} items'))
        
        # Summary statistics
        total_revenue = Order.objects.filter(payment_status='paid').aggregate(
            total=models.Sum('total')
        )['total'] or Decimal('0')
        
        self.stdout.write(self.style.SUCCESS(f'  Total revenue: ${total_revenue:,.2f}'))
        self.stdout.write(self.style.SUCCESS(f'  Average order value: ${total_revenue / orders_created if orders_created > 0 else 0:,.2f}'))


from django.db import models

"""
Django Shell Script to Set Up Sample Promotion Data
Run with: python manage.py shell < setup_promotion_data.py
"""

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from product.models import Product, Promotion, Category, Brand
from website.models import SiteSettings

# Get or create SiteSettings
site_settings, created = SiteSettings.objects.get_or_create(
    id=1,
    defaults={
        'site_name': 'MobilePoint',
        'shipping_cost': Decimal('10.00'),
        'tax': Decimal('10.00'),  # 10% tax
    }
)
print(f"✓ SiteSettings: Shipping Cost=${site_settings.shipping_cost}, Tax={site_settings.tax}%")

# Get some products to link with promotions
try:
    products = Product.objects.filter(is_active=True)[:5]
    
    if not products.exists():
        print("❌ No active products found. Please create some products first.")
    else:
        print(f"✓ Found {products.count()} products to link with promotions")

        # ===== CREATE FREE SHIPPING PROMOTION =====
        now = timezone.now()
        free_shipping_promo = Promotion.objects.create(
            promotion_type='free_shipping',
            title='Free Shipping on Orders Over $50',
            description='Get free shipping when you spend $50 or more. Valid for all smartphones and gadgets.',
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True
        )
        print(f"\n✓ Created Promotion: {free_shipping_promo.title}")
        print(f"  - ID: {free_shipping_promo.id}")
        print(f"  - Type: {free_shipping_promo.get_promotion_type_display()}")
        print(f"  - Start: {free_shipping_promo.start_date}")
        print(f"  - End: {free_shipping_promo.end_date}")

        # Link first 3 products to free shipping promotion
        for product in products[:3]:
            free_shipping_promo.products.add(product)
        print(f"  - Linked {min(3, products.count())} products")

        # ===== CREATE FREE GIFT PROMOTION =====
        free_gift_promo = Promotion.objects.create(
            promotion_type='free_gift',
            title='Free Gift with Premium Phones',
            description='Buy any premium smartphone and get a free premium case worth $30.',
            start_date=now,
            end_date=now + timedelta(days=15),
            is_active=True
        )
        print(f"\n✓ Created Promotion: {free_gift_promo.title}")
        print(f"  - ID: {free_gift_promo.id}")
        print(f"  - Type: {free_gift_promo.get_promotion_type_display()}")
        print(f"  - Start: {free_gift_promo.start_date}")
        print(f"  - End: {free_gift_promo.end_date}")

        # Link last 2 products to free gift promotion
        for product in products[2:4]:
            free_gift_promo.products.add(product)
        print(f"  - Linked {min(2, products.count())} products")

        # ===== CREATE UPCOMING PROMOTION =====
        upcoming_promo = Promotion.objects.create(
            promotion_type='free_shipping',
            title='Coming Soon - Free Shipping Festival',
            description='Big free shipping festival coming next month. Stay tuned!',
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=37),
            is_active=True
        )
        print(f"\n✓ Created Upcoming Promotion: {upcoming_promo.title}")
        print(f"  - ID: {upcoming_promo.id}")
        print(f"  - Starts in 7 days")

        # ===== CREATE EXPIRED PROMOTION =====
        expired_promo = Promotion.objects.create(
            promotion_type='free_gift',
            title='Expired - Spring Sale Gift',
            description='This promotion has expired.',
            start_date=now - timedelta(days=30),
            end_date=now - timedelta(days=1),
            is_active=True
        )
        print(f"\n✓ Created Expired Promotion: {expired_promo.title}")
        print(f"  - ID: {expired_promo.id}")
        print(f"  - Expired 1 day ago")

        # Summary
        print("\n" + "="*60)
        print("PROMOTION SETUP COMPLETE")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   - Active Promotions: {Promotion.active().count()}")
        print(f"   - Total Promotions: {Promotion.objects.count()}")
        print(f"   - Free Shipping: {Promotion.objects.filter(promotion_type='free_shipping').count()}")
        print(f"   - Free Gift: {Promotion.objects.filter(promotion_type='free_gift').count()}")

        print(f"\n🔗 API Endpoints to Test:")
        print(f"   GET /api/promotions/                    # List all promotions")
        print(f"   GET /api/promotions/1/                  # Get promotion details")
        print(f"   GET /api/promotions/active/             # Get active promotions")
        print(f"   GET /api/promotions/by-type/?type=free_shipping")
        print(f"   GET /api/promotions/upcoming/           # Upcoming promos")
        print(f"   GET /api/promotions/expired/            # Expired promos")
        print(f"   GET /api/promotions/summary/            # Stats")
        print(f"   GET /api/promotions/1/products/         # Products in promo")

        print(f"\n🛍️  Create Order with Promotion:")
        print(f"   POST /api/orders/")
        print(f"   Body: {{")
        print(f"     'items': [")
        print(f"       {{'product': 1, 'quantity': 1}}")
        print(f"     ],")
        print(f"     'shipping_name': 'John Doe',")
        print(f"     'shipping_email': 'john@example.com',")
        print(f"     'shipping_phone': '+1234567890',")
        print(f"     'shipping_address': '123 Main St',")
        print(f"     'shipping_city': 'New York',")
        print(f"     'shipping_state': 'NY',")
        print(f"     'shipping_zip': '10001',")
        print(f"     'shipping_country': 'USA',")
        print(f"     'billing_name': 'John Doe',")
        print(f"     'billing_address': '123 Main St',")
        print(f"     'billing_city': 'New York',")
        print(f"     'billing_state': 'NY',")
        print(f"     'billing_zip': '10001',")
        print(f"     'billing_country': 'USA'")
        print(f"   }}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n✓ Script completed!")

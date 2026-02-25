# Setup Guide: Promotion Data

## Quick Start

Run the setup script to populate sample data:

```bash
python manage.py shell < setup_promotion_data.py
```

This will create:
- ✅ 4 Promotions (2 active, 1 upcoming, 1 expired)
- ✅ Free Shipping promotion linked to 3 products
- ✅ Free Gift promotion linked to 2 products
- ✅ Site Settings with 10% tax and $10 shipping cost

---

## Manual Setup (Alternative)

### 1. Update SiteSettings (Tax & Shipping)

```python
python manage.py shell
>>> from website.models import SiteSettings
>>> from decimal import Decimal
>>> 
>>> settings = SiteSettings.objects.get_or_create(id=1)[0]
>>> settings.tax = Decimal('10.00')  # 10% tax
>>> settings.shipping_cost = Decimal('10.00')  # $10 shipping
>>> settings.save()
>>> print("✓ Settings updated!")
```

### 2. Create Free Shipping Promotion

```python
from django.utils import timezone
from datetime import timedelta
from product.models import Promotion, Product
from decimal import Decimal

now = timezone.now()

# Create promotion
free_shipping = Promotion.objects.create(
    promotion_type='free_shipping',
    title='Free Shipping on Orders Over $50',
    description='Get free shipping when you spend $50 or more',
    start_date=now,
    end_date=now + timedelta(days=30),
    is_active=True
)

# Link products
products = Product.objects.filter(is_active=True)[:3]
for product in products:
    free_shipping.products.add(product)

print(f"✓ Created: {free_shipping.title}")
print(f"  ID: {free_shipping.id}")
print(f"  Products linked: {free_shipping.products.count()}")
```

### 3. Create Free Gift Promotion

```python
from product.models import Promotion, Product
from django.utils import timezone
from datetime import timedelta

now = timezone.now()

# Create promotion
free_gift = Promotion.objects.create(
    promotion_type='free_gift',
    title='Free Gift with Premium Phones',
    description='Buy any premium smartphone and get a free premium case',
    start_date=now,
    end_date=now + timedelta(days=15),
    is_active=True
)

# Link products
products = Product.objects.filter(is_active=True)[2:4]
for product in products:
    free_gift.products.add(product)

print(f"✓ Created: {free_gift.title}")
print(f"  ID: {free_gift.id}")
print(f"  Products linked: {free_gift.products.count()}")
```

### 4. View All Promotions

```python
from product.models import Promotion

# All promotions
all_promos = Promotion.objects.all()
print(f"Total: {all_promos.count()}")
for promo in all_promos:
    print(f"  - {promo.title} ({promo.get_promotion_type_display()})")

# Active only
active = Promotion.active()
print(f"\nActive: {active.count()}")
for promo in active:
    print(f"  - {promo.title}")

# By type
free_shipping = Promotion.objects.filter(promotion_type='free_shipping')
print(f"\nFree Shipping: {free_shipping.count()}")

free_gift = Promotion.objects.filter(promotion_type='free_gift')
print(f"Free Gift: {free_gift.count()}")
```

---

## Test Promotions via API

### 1. List All Promotions
```bash
curl http://127.0.0.1:8000/api/promotions/
```

### 2. Get Active Promotions
```bash
curl http://127.0.0.1:8000/api/promotions/active/
```

### 3. Get Free Shipping Promotions
```bash
curl "http://127.0.0.1:8000/api/promotions/by-type/?type=free_shipping"
```

### 4. Get Free Gift Promotions
```bash
curl "http://127.0.0.1:8000/api/promotions/by-type/?type=free_gift"
```

### 5. Get Promotion Details
```bash
curl http://127.0.0.1:8000/api/promotions/1/
```

### 6. Get Products in Promotion
```bash
curl http://127.0.0.1:8000/api/promotions/1/products/
```

### 7. Get Promotion Statistics
```bash
curl http://127.0.0.1:8000/api/promotions/summary/
```

### 8. Get Upcoming Promotions
```bash
curl http://127.0.0.1:8000/api/promotions/upcoming/
```

### 9. Create an Order (with automatic promotion detection)
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "items": [
      {
        "product": 1,
        "quantity": 2
      }
    ],
    "payment_method": "cod",
    "shipping_name": "John Doe",
    "shipping_email": "john@example.com",
    "shipping_phone": "+1234567890",
    "shipping_address": "123 Main Street",
    "shipping_city": "New York",
    "shipping_state": "NY",
    "shipping_zip": "10001",
    "shipping_country": "USA",
    "billing_name": "John Doe",
    "billing_address": "123 Main Street",
    "billing_city": "New York",
    "billing_state": "NY",
    "billing_zip": "10001",
    "billing_country": "USA"
  }'
```

**Response will show:**
- ✅ Free shipping applied (shipping_cost = $0)
- ✅ Free gift details in order items
- ✅ Promotion linked to order

### 10. Get Order with Promotion Details
```bash
curl http://127.0.0.1:8000/api/orders/1/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response includes:**
```json
{
  "id": 1,
  "order_number": "ORD-ABC123DEF456",
  "subtotal": 100.00,
  "tax": 10.00,
  "shipping_cost": 0.00,
  "total": 110.00,
  "free_shipping_applied": true,
  "free_shipping_promotion": 1,
  "free_shipping_promotion_title": "Free Shipping on Orders Over $50",
  "items": [
    {
      "id": 1,
      "product_name": "iPhone 15 Pro",
      "quantity": 1,
      "price": 100.00,
      "promotion": 2,
      "promotion_type": "free_gift",
      "promotion_title": "Free Gift with Premium Phones",
      "free_gift_detail": "Free premium case worth $30"
    }
  ]
}
```

---

## Admin Interface

After setup, visit Django Admin:

```
http://127.0.0.1:8000/admin/product/promotion/
```

You can:
- ✅ View all promotions
- ✅ Filter by type (Free Shipping / Free Gift)
- ✅ Edit promotion dates and products
- ✅ Activate/deactivate promotions

### View Orders with Promotions

```
http://127.0.0.1:8000/admin/orders/order/
```

Each order will show:
- ✅ Free Shipping Applied: ✓ (green if applied)
- ✅ Promotion Details
- ✅ Order Items with linked promotions
- ✅ Free Gift Details

---

## Key Features

### Automatic Promotion Detection
When creating an order:
1. System checks all products in the order
2. Finds active promotions for those products
3. Applies free shipping (deducts shipping cost)
4. Records free gift details in order items

### Promotion States
- **Active**: Showing right now (start_date ≤ now ≤ end_date)
- **Upcoming**: Will start soon (start_date > now)
- **Expired**: Already ended (end_date < now)
- **Inactive**: Disabled by admin

### Promotion Types
- **Free Shipping**: Removes $10 shipping cost
- **Free Gift**: Shows gift details in order items

---

## Database Schema

### Promotion Table
```
- id (Primary Key)
- promotion_type (free_shipping / free_gift)
- title (varchar 150)
- description (text)
- start_date (datetime)
- end_date (datetime)
- is_active (boolean)
- products (Many-to-Many with Product)
- created_at (datetime)
- updated_at (datetime)
```

### Order Updates
```
- free_shipping_applied (boolean)
- free_shipping_promotion (ForeignKey to Promotion)
```

### OrderItem Updates
```
- promotion (ForeignKey to Promotion)
- free_gift_detail (varchar 300)
```

---

## Troubleshooting

### Promotion Not Applying?
1. Check if promotion is active: `is_active = True`
2. Check dates: `start_date ≤ now ≤ end_date`
3. Check products are linked to promotion
4. Check product is active: `is_active = True`

### Free Shipping Not Working?
1. Ensure `free_shipping_applied = True`
2. Check `shipping_cost = 0.00` in order
3. Verify product has free_shipping promotion

### Free Gift Not Showing?
1. Check `free_gift_detail` field in order item
2. Ensure `promotion` is linked to order item
3. Verify `promotion.promotion_type = 'free_gift'`

---

## Next Steps

1. ✅ Run setup script: `python manage.py shell < setup_promotion_data.py`
2. ✅ Test API endpoints
3. ✅ Create orders and verify promotions apply
4. ✅ Check Django admin for promotion details
5. ✅ Monitor OrdersAnalytics for promotion impact

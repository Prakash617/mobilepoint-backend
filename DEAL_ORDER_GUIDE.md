# Deal & Order Integration Guide

## Overview

When a customer purchases a product with an active deal, the system:
1. ✅ Automatically applies the deal discount to the price
2. ✅ Tracks which deal was used in the order
3. ✅ Increments the deal's sold quantity when order is confirmed
4. ✅ Updates deal statistics (purchases)

---

## Data Structure

### OrderItem Model

Each item in an order now includes:

```python
OrderItem:
  - deal (ForeignKey) → Links to the Deal used
  - original_price → Base price before discount
  - discount_percent → Discount % from the deal
  - price → Final price paid (original_price * (1 - discount_percent/100))
  - subtotal → price * quantity
```

### Example Data Flow

```
Product: "Smartphone"
  - base_price: Rs. 50,000

Deal: "Flash Sale"
  - discount_percent: 35%
  - remaining_quantity: 50

Customer Order:
  - original_price: Rs. 50,000
  - discount_percent: 35%
  - price: Rs. 32,500 (calculated)
  - quantity: 2
  - subtotal: Rs. 65,000
  - deal: "Flash Sale"
```

---

## API Usage Examples

### 1. Create Order Item with Deal

**Request:**
```json
POST /api/orders/
{
  "items": [
    {
      "product": 1,
      "deal": 5,
      "quantity": 2
    }
  ],
  "shipping_name": "John Doe",
  "shipping_address": "123 Main St",
  ...
}
```

**Response:**
```json
{
  "id": 10,
  "items": [
    {
      "id": 45,
      "product": 1,
      "product_name": "Smartphone",
      "original_price": "50000.00",
      "discount_percent": 35,
      "price": "32500.00",
      "deal": 5,
      "deal_title": "Flash Sale",
      "deal_type": "flash",
      "quantity": 2,
      "subtotal": "65000.00"
    }
  ],
  "subtotal": "65000.00",
  "discount": "17500.00",
  "total": "65000.00",
  ...
}
```

### 2. Check Deal Availability Before Adding to Cart

**Request:**
```python
from orders.services import OrderService

deal = Deal.objects.get(id=5)
is_valid, error = OrderService.can_use_deal(deal, quantity=2)

if is_valid:
    print("Deal available!")
else:
    print(f"Cannot use deal: {error}")
```

### 3. Calculate Final Price

**Request:**
```python
from orders.services import OrderService
from product.models import Product, Deal

product = Product.objects.get(id=1)
deal = Deal.objects.get(id=5)

pricing = OrderService.calculate_item_price(product, product_variant=None, deal=deal)

print(f"Original Price: Rs. {pricing['original_price']}")
print(f"Final Price: Rs. {pricing['final_price']}")
print(f"Discount: {pricing['discount_percent']}%")
```

**Response:**
```
Original Price: Rs. 50000
Final Price: Rs. 32500
Discount: 35%
```

### 4. Create Order Item Using Service

**Request:**
```python
from orders.services import OrderService
from product.models import Product, Deal
from orders.models import Order

order = Order.objects.get(id=10)
product = Product.objects.get(id=1)
deal = Deal.objects.get(id=5)

try:
    item = OrderService.create_order_item(
        order=order,
        product=product,
        quantity=2,
        deal=deal
    )
    print(f"Order item created: {item}")
except ValueError as e:
    print(f"Error: {e}")
```

### 5. Finalize Order (Mark as Confirmed)

When an order is confirmed/paid, call this to increment deal stats:

**Request:**
```python
from orders.services import OrderService
from orders.models import Order

order = Order.objects.get(id=10)

# Update order status
order.status = 'confirmed'
order.payment_status = 'paid'
order.save()

# Finalize deals
OrderService.finalize_order_deals(order)
```

**What happens:**
- Deal.sold_quantity incremented by 2
- Deal.remaining_quantity decremented by 2
- DealStat.purchases incremented by 2
- Deal.progress_percentage updated

---

## Frontend Implementation

### Show Deal Badge on Product

```javascript
// When displaying product detail
if (product.deals.length > 0) {
  const deal = product.deals[0];
  const discountedPrice = product.base_price * (1 - deal.discount_percent / 100);
  
  showDealBadge(deal.title, deal.discount_percent);
  showPrice(product.base_price, discountedPrice);
  showProgressBar(deal.sold_quantity, deal.total_quantity);
}
```

### Add to Cart with Deal

```javascript
// When adding to cart
const addToCart = async (product, deal, quantity) => {
  // Check deal availability
  const response = await fetch(`/api/deals/${deal.id}/`, {
    method: 'GET'
  });
  
  const updatedDeal = await response.json();
  
  if (updatedDeal.remaining_quantity < quantity) {
    alert(`Only ${updatedDeal.remaining_quantity} items available`);
    return;
  }
  
  // Add to cart with deal
  cart.add({
    product: product.id,
    deal: deal.id,
    quantity: quantity,
    price: product.base_price * (1 - deal.discount_percent / 100)
  });
};
```

### Order Confirmation

```javascript
// Display saved deal info on order confirmation
order.items.forEach(item => {
  if (item.deal) {
    console.log(`
      ${item.product_name} x ${item.quantity}
      Original: Rs. ${item.original_price}
      Discount: ${item.discount_percent}%
      Paid: Rs. ${item.price}
      Deal: ${item.deal_title}
    `);
  }
});
```

---

## Admin Features

### View Deal Usage in Orders

In Django Admin:
1. Go to **Orders > Order Items**
2. See which deals were used for each purchase
3. Track inventory depletion via **Products > Deals > Inventory** column

### Deal Analytics

```python
from product.models import Deal
from orders.models import OrderItem

deal = Deal.objects.get(id=5)

# Total revenue from this deal
total_revenue = OrderItem.objects.filter(deal=deal).aggregate(
    total=models.Sum(models.F('price') * models.F('quantity'))
)['total']

# Conversion rate
stat = deal.dealstat
conversion_rate = (stat.purchases / stat.views) * 100 if stat.views else 0

print(f"Deal: {deal.title}")
print(f"Revenue: Rs. {total_revenue}")
print(f"Views: {stat.views}")
print(f"Conversions: {stat.purchases}")
print(f"Conversion Rate: {conversion_rate}%")
```

---

## Validation Rules

### Deal Cannot Be Used If:
- ❌ Deal is inactive (`is_active=False`)
- ❌ Deal time window expired (current_time > end_at)
- ❌ Deal time window not started (current_time < start_at)
- ❌ No inventory remaining (`remaining_quantity < quantity`)
- ❌ Deal product doesn't match order product

### Price Calculation
```
final_price = original_price × (1 - discount_percent / 100)
subtotal = final_price × quantity
```

---

## Key Methods

### OrderService.calculate_item_price()
Calculates final price with deal discount applied

### OrderService.create_order_item()
Creates order item with full validation and pricing

### OrderService.finalize_order_deals()
Called when order is confirmed - increments deal stats

### OrderService.can_use_deal()
Quick validation check before adding to cart

---

## Database Relationships

```
Order
  ├── OrderItem (many)
  │   ├── product (FK to Product)
  │   ├── product_variant (FK to ProductVariant)
  │   ├── deal (FK to Deal)
  │   └── pricing fields: original_price, price, discount_percent

Deal
  ├── product (FK to Product)
  ├── dealstat (OneToOne) → views, purchases
  ├── dealextra (OneToOne) → free_shipping, free_gift_text
  └── order_items (reverse FK) → all orders using this deal
```

---

## Testing

```python
from django.test import TestCase
from orders.services import OrderService
from product.models import Product, Deal
from orders.models import Order

class DealOrderTests(TestCase):
    def test_create_order_with_deal(self):
        product = Product.objects.create(name="Test", base_price=1000)
        deal = Deal.objects.create(
            product=product,
            title="Test Deal",
            deal_type="flash",
            discount_percent=25,
            total_quantity=100,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(hours=1),
            is_active=True
        )
        
        order = Order.objects.create(user=self.user, total=750)
        item = OrderService.create_order_item(order, product, quantity=1, deal=deal)
        
        self.assertEqual(item.original_price, 1000)
        self.assertEqual(item.discount_percent, 25)
        self.assertEqual(item.price, 750)
```

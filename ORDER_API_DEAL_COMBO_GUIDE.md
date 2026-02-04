# Order API - Deal & Combo Integration

## Summary

The Order API has been **updated** to fully support creating orders with:
- ✅ **Deals** (Flash sales, daily deals, seasonal sales)
- ✅ **Product Combos** (Bundle packages)
- ✅ **Mixed Orders** (Both deals and combos in the same order)

## What Changed

### 1. OrderItemCreateSerializer
**File:** `orders/serializers.py`

**New Fields:**
- Added `combo` field to support product bundles

**Enhanced Validation:**
- Validates combo is active
- Prevents mixing combos with deals
- Ensures either product/variant OR combo is provided (not both)
- Validates deal availability, timing, and inventory

### 2. OrderCreateSerializer
**File:** `orders/serializers.py`

**Updated `create()` Method:**
- Now uses `OrderService.calculate_item_price()` for deal pricing
- Uses `ComboService.create_combo_order_items()` for combo bundles
- Properly calculates discounts from deals and combos
- Tracks `discount` field in Order model
- Stores `original_price` and `discount_percent` in OrderItem

**Key Features:**
- Automatic discount calculation
- Deal inventory validation
- Combo parent-child relationship creation
- Total discount tracking

## API Endpoints

### Create Order
**Endpoint:** `POST /api/orders/`

**Authentication:** Required

## Request Examples

### 1. Regular Product Order (No Deal)
```json
{
  "items": [
    {
      "product": 1,
      "quantity": 2
    }
  ],
  "shipping_name": "John Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+1234567890",
  "shipping_address": "123 Main St",
  "shipping_city": "New York",
  "shipping_state": "NY",
  "shipping_zip": "10001",
  "shipping_country": "USA",
  "billing_name": "John Doe",
  "billing_address": "123 Main St",
  "billing_city": "New York",
  "billing_state": "NY",
  "billing_zip": "10001",
  "billing_country": "USA",
  "notes": "Optional notes"
}
```

### 2. Order with Deal
```json
{
  "items": [
    {
      "product": 1,
      "deal": 1,
      "quantity": 2
    }
  ],
  "shipping_name": "Jane Smith",
  "shipping_email": "jane@example.com",
  "shipping_phone": "+1234567890",
  "shipping_address": "456 Deal St",
  "shipping_city": "Discount City",
  "shipping_state": "DC",
  "shipping_zip": "20001",
  "shipping_country": "USA",
  "billing_name": "Jane Smith",
  "billing_address": "456 Deal St",
  "billing_city": "Discount City",
  "billing_state": "DC",
  "billing_zip": "20001",
  "billing_country": "USA"
}
```

### 3. Order with Combo
```json
{
  "items": [
    {
      "combo": 1,
      "quantity": 1
    }
  ],
  "shipping_name": "Bob Johnson",
  "shipping_email": "bob@example.com",
  "shipping_phone": "+1234567890",
  "shipping_address": "789 Bundle Ave",
  "shipping_city": "Combo City",
  "shipping_state": "CC",
  "shipping_zip": "30001",
  "shipping_country": "USA",
  "billing_name": "Bob Johnson",
  "billing_address": "789 Bundle Ave",
  "billing_city": "Combo City",
  "billing_state": "CC",
  "billing_zip": "30001",
  "billing_country": "USA"
}
```

### 4. Mixed Order (Deal + Combo)
```json
{
  "items": [
    {
      "product": 1,
      "deal": 1,
      "quantity": 1
    },
    {
      "combo": 1,
      "quantity": 1
    }
  ],
  "shipping_name": "Alice Williams",
  "shipping_email": "alice@example.com",
  "shipping_phone": "+1234567890",
  "shipping_address": "321 Mixed Blvd",
  "shipping_city": "Hybrid City",
  "shipping_state": "HC",
  "shipping_zip": "40001",
  "shipping_country": "USA",
  "billing_name": "Alice Williams",
  "billing_address": "321 Mixed Blvd",
  "billing_city": "Hybrid City",
  "billing_state": "HC",
  "billing_zip": "40001",
  "billing_country": "USA"
}
```

## Response Structure

### Deal Order Response
```json
{
  "id": 1,
  "order_number": "ORD-5CDF7089E023",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "first_name": "Test",
    "last_name": "User"
  },
  "status": "pending",
  "payment_status": "pending",
  "subtotal": "65000.00",
  "tax": "6500.00",
  "shipping_cost": "10.00",
  "discount": "35000.00",
  "total": "71510.00",
  "items": [
    {
      "id": 1,
      "product": 1,
      "product_name": "Test Smartphone",
      "quantity": 2,
      "original_price": "50000.00",
      "price": "32500.00",
      "discount_percent": 35,
      "deal": 1,
      "deal_title": "Flash Sale - Smartphone",
      "deal_type": "flash",
      "subtotal": "65000.00",
      "combo": null,
      "is_combo_parent": false
    }
  ],
  "shipping_name": "Jane Smith",
  "shipping_email": "jane@example.com",
  "created_at": "2026-02-02T12:00:00Z",
  "updated_at": "2026-02-02T12:00:00Z"
}
```

### Combo Order Response
```json
{
  "id": 2,
  "order_number": "ORD-152141B659C0",
  "status": "pending",
  "payment_status": "pending",
  "subtotal": "6800.00",
  "tax": "680.00",
  "shipping_cost": "10.00",
  "discount": "1700.00",
  "total": "7490.00",
  "items": [
    {
      "id": 2,
      "product": 2,
      "product_name": "Gaming Bundle",
      "quantity": 1,
      "original_price": "8500.00",
      "price": "6800.00",
      "discount_percent": 20,
      "deal": null,
      "combo": 1,
      "combo_name": "Gaming Bundle",
      "is_combo_parent": true,
      "combo_items": [
        {
          "id": 3,
          "product_name": "Gaming Keyboard",
          "quantity": 1,
          "price": "5000.00",
          "subtotal": "5000.00"
        },
        {
          "id": 4,
          "product_name": "Gaming Mouse",
          "quantity": 2,
          "price": "1500.00",
          "subtotal": "3000.00"
        },
        {
          "id": 5,
          "product_name": "Gaming Mouse Pad",
          "quantity": 1,
          "price": "500.00",
          "subtotal": "500.00"
        }
      ]
    }
  ]
}
```

## Validation Rules

### Deals
1. ✅ Deal must be active (`is_active=True`)
2. ✅ Deal must be within valid time window (`start_at <= now <= end_at`)
3. ✅ Deal must match the product being ordered
4. ✅ Sufficient inventory must be available (`remaining_quantity >= quantity`)
5. ✅ Cannot combine deals with combos

### Combos
1. ✅ Combo must be active (`is_active=True`)
2. ✅ Cannot specify product/variant when ordering combo
3. ✅ Cannot apply deals to combo items

### General
1. ✅ Must provide either `product`, `product_variant`, or `combo` (not multiple)
2. ✅ Quantity must be at least 1

## Backend Services

### OrderService
**Location:** `orders/services.py`

**Key Methods:**
- `calculate_item_price(product, product_variant, deal)` - Calculates final price with deal discount
- `create_order_item(...)` - Creates order items with deal tracking

### ComboService
**Location:** `orders/services.py`

**Key Methods:**
- `get_combo_discount(combo)` - Calculates combo discount information
- `create_combo_order_items(order, combo, quantity)` - Creates parent + child order items

## Order Finalization

When an order is confirmed (`status='confirmed'`), calling `order.finalize()`:
- ✅ Increments deal `sold_quantity`
- ✅ Updates deal statistics (`DealStat.purchases`)
- ✅ Reduces available inventory

## Testing

### Unit Tests Created
1. **test_deal_combo_order.py** - Direct model/service testing
   - Creates orders with deals
   - Creates orders with combos
   - Creates mixed orders
   - Tests deal inventory tracking

2. **test_order_api.py** - API endpoint examples
   - Shows proper request format
   - Displays actual product/deal/combo IDs
   - Provides CURL commands

### Run Tests
```bash
# Direct testing (bypasses API)
python test_deal_combo_order.py

# View API examples
python test_order_api.py
```

## Database Schema

### OrderItem Model Fields
```python
class OrderItem(models.Model):
    # Core fields
    product = ForeignKey(Product)
    product_variant = ForeignKey(ProductVariant)
    quantity = PositiveIntegerField()
    
    # Pricing with deal support
    original_price = DecimalField()  # Price before discount
    price = DecimalField()           # Final price paid
    discount_percent = IntegerField() # Discount %
    subtotal = DecimalField()        # price * quantity
    
    # Deal tracking
    deal = ForeignKey(Deal, null=True)
    
    # Combo tracking
    combo = ForeignKey(ProductCombo, null=True)
    combo_parent = ForeignKey('self', null=True)
    is_combo_parent = BooleanField(default=False)
```

## Current Test Data

### Products
- ID: 1 - Test Smartphone (Rs. 50,000)
- ID: 2 - Gaming Keyboard (Rs. 5,000)
- ID: 3 - Gaming Mouse (Rs. 1,500)
- ID: 4 - Gaming Mouse Pad (Rs. 500)

### Deals
- ID: 1 - Flash Sale - Smartphone (35% off, 48/50 remaining)

### Combos
- ID: 1 - Gaming Bundle (Rs. 6,800, saves Rs. 1,700)
  - 1x Gaming Keyboard
  - 2x Gaming Mouse
  - 1x Gaming Mouse Pad

## CURL Examples

### Create Deal Order
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "items": [{"product": 1, "deal": 1, "quantity": 2}],
    "shipping_name": "Jane Smith",
    "shipping_email": "jane@example.com",
    "shipping_phone": "+1234567890",
    "shipping_address": "456 Deal St",
    "shipping_city": "Discount City",
    "shipping_state": "DC",
    "shipping_zip": "20001",
    "shipping_country": "USA",
    "billing_name": "Jane Smith",
    "billing_address": "456 Deal St",
    "billing_city": "Discount City",
    "billing_state": "DC",
    "billing_zip": "20001",
    "billing_country": "USA"
  }'
```

### Create Combo Order
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "items": [{"combo": 1, "quantity": 1}],
    "shipping_name": "Bob Johnson",
    "shipping_email": "bob@example.com",
    "shipping_phone": "+1234567890",
    "shipping_address": "789 Bundle Ave",
    "shipping_city": "Combo City",
    "shipping_state": "CC",
    "shipping_zip": "30001",
    "shipping_country": "USA",
    "billing_name": "Bob Johnson",
    "billing_address": "789 Bundle Ave",
    "billing_city": "Combo City",
    "billing_state": "CC",
    "billing_zip": "30001",
    "billing_country": "USA"
  }'
```

## Notes

1. **Authentication Required**: All order creation endpoints require authentication
2. **Auto-Calculations**: Tax (10%) and shipping (Rs. 10) are automatically calculated
3. **Inventory Tracking**: Deal inventory is only decremented when order is confirmed
4. **Nested Structure**: Combo orders create parent item + child items for proper tracking
5. **Discount Tracking**: Both deal and combo discounts are tracked in the `discount` field

## Future Enhancements

Potential improvements:
- Support variant-level deals
- Multiple deals per order
- Coupon code integration
- Dynamic shipping cost calculation
- Tax calculation by region
- Inventory reservation during checkout

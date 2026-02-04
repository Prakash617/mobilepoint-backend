# ProductCombo & Order Integration Guide

## Overview

When a customer purchases a ProductCombo, the system:
1. ✅ Creates a parent order item representing the combo bundle
2. ✅ Creates child order items for each product in the combo
3. ✅ Applies combo discount (combo_selling_price vs individual items)
4. ✅ Manages inventory for each combo item
5. ✅ Tracks which combo was purchased

---

## Data Structure

### ProductCombo Model

```python
ProductCombo:
  - name → Combo bundle name
  - main_product → Primary product (for catalog)
  - combo_regular_price → Total regular price (auto-calculated)
  - combo_selling_price → Discounted bundle price
  - items → ProductComboItem instances
```

### ProductComboItem Model

```python
ProductComboItem:
  - combo → FK to ProductCombo
  - product → FK to Product
  - quantity → How many of this product in the combo
```

### OrderItem Changes

New fields for combo support:
```python
OrderItem:
  - combo → Links to ProductCombo used
  - combo_parent → Self-referential FK (for nested items)
  - is_combo_parent → Boolean flag (True = combo bundle header, False = individual item)
  - combo_items → Related manager (reverse of combo_parent)
```

---

## How It Works

### Example Combo

```
ProductCombo: "Gaming Bundle"
  Items:
    1. Gaming Keyboard x1 (Rs. 5,000)
    2. Gaming Mouse x2 (Rs. 1,500 each = Rs. 3,000)
    3. Mouse Pad x1 (Rs. 500)
  
  Regular Price (Individual): Rs. 8,500
  Combo Price: Rs. 6,800
  Savings: Rs. 1,700 (20%)
```

### Order Structure

```
Order:
  Items:
    1. OrderItem (combo_parent=True, is_combo_parent=True)
       - product: "Gaming Bundle" (main_product)
       - combo: ProductCombo instance
       - original_price: Rs. 8,500
       - price: Rs. 6,800
       - quantity: 1
       - subtotal: Rs. 6,800
       - combo_items: [item2, item3, item4]
    
    2. OrderItem (combo_parent=item1, is_combo_parent=False)
       - product: "Gaming Keyboard"
       - combo: ProductCombo instance
       - quantity: 1
       - price: Rs. 5,000
       - subtotal: Rs. 5,000
    
    3. OrderItem (combo_parent=item1, is_combo_parent=False)
       - product: "Gaming Mouse"
       - combo: ProductCombo instance
       - quantity: 2
       - price: Rs. 1,500
       - subtotal: Rs. 3,000
    
    4. OrderItem (combo_parent=item1, is_combo_parent=False)
       - product: "Mouse Pad"
       - combo: ProductCombo instance
       - quantity: 1
       - price: Rs. 500
       - subtotal: Rs. 500
```

---

## API Usage

### 1. Get Combo Information

**Request:**
```
GET /api/product-combos/1/
```

**Response:**
```json
{
  "id": 1,
  "name": "Gaming Bundle",
  "main_product": 5,
  "combo_regular_price": "8500.00",
  "combo_selling_price": "6800.00",
  "items": [
    {
      "product": 10,
      "product_name": "Gaming Keyboard",
      "quantity": 1,
      "base_price": "5000.00"
    },
    {
      "product": 11,
      "product_name": "Gaming Mouse",
      "quantity": 2,
      "base_price": "1500.00"
    },
    {
      "product": 12,
      "product_name": "Mouse Pad",
      "quantity": 1,
      "base_price": "500.00"
    }
  ]
}
```

### 2. Get Combo Pricing

**Request (Python):**
```python
from orders.services import ComboService
from product.models import ProductCombo

combo = ProductCombo.objects.get(id=1)
pricing = ComboService.get_combo_discount(combo)

print(f"Regular Price: {pricing['regular_price']}")
print(f"Selling Price: {pricing['selling_price']}")
print(f"Discount: {pricing['discount_amount']} ({pricing['discount_percent']}%)")
```

**Output:**
```
Regular Price: 8500
Selling Price: 6800
Discount: 1700 (20%)
```

### 3. Create Order with Combo

**Request (Python):**
```python
from orders.models import Order
from orders.services import ComboService
from product.models import ProductCombo

combo = ProductCombo.objects.get(id=1)
order = Order.objects.create(
    user=user,
    status='pending',
    subtotal=6800,
    total=6800
)

# Create combo items
result = ComboService.create_combo_order_items(
    order=order,
    combo=combo,
    quantity=1
)

print(f"Combo Parent Item: {result['combo_parent']}")
print(f"Child Items: {result['items']}")
print(f"Total Price: {result['total_price']}")
```

**Response:**
```
Combo Parent Item: OrderItem #45
Child Items: [OrderItem #46, OrderItem #47, OrderItem #48]
Total Price: 6800
```

### 4. Get Order with Combo Details

**Request:**
```
GET /api/orders/ORD-ABC123/
```

**Response:**
```json
{
  "id": 100,
  "order_number": "ORD-ABC123",
  "items": [
    {
      "id": 45,
      "product_name": "Gaming Bundle",
      "combo_name": "Gaming Bundle",
      "is_combo_parent": true,
      "original_price": "8500.00",
      "price": "6800.00",
      "discount_percent": 20,
      "quantity": 1,
      "subtotal": "6800.00",
      "combo_items": [
        {
          "id": 46,
          "product_name": "Gaming Keyboard",
          "quantity": 1,
          "price": "5000.00",
          "subtotal": "5000.00"
        },
        {
          "id": 47,
          "product_name": "Gaming Mouse",
          "quantity": 2,
          "price": "1500.00",
          "subtotal": "3000.00"
        },
        {
          "id": 48,
          "product_name": "Mouse Pad",
          "quantity": 1,
          "price": "500.00",
          "subtotal": "500.00"
        }
      ]
    }
  ],
  "subtotal": "6800.00",
  "total": "6800.00"
}
```

### 5. Finalize Order (Handle Inventory)

**Request (Python):**
```python
from orders.models import Order
from orders.services import OrderService, ComboService

order = Order.objects.get(order_number='ORD-ABC123')

# Update order status
order.status = 'confirmed'
order.payment_status = 'paid'
order.save()

# Finalize deals if any
OrderService.finalize_order_deals(order)

# Finalize combos (decrement inventory)
ComboService.finalize_order_combos(order)
```

**What happens:**
- Each combo item's product variant stock is decremented
- Product variant sold_quantity is incremented
- Inventory is properly tracked across all combo items

---

## Frontend Implementation

### Display Combo Information

```javascript
const displayCombo = (combo) => {
  const discount = ComputeDiscount(combo.combo_regular_price, combo.combo_selling_price);
  
  return {
    name: combo.name,
    items: combo.items.map(item => ({
      product: item.product_name,
      quantity: item.quantity,
      unitPrice: item.base_price
    })),
    regularPrice: combo.combo_regular_price,
    discountedPrice: combo.combo_selling_price,
    savingsPercent: discount.percent,
    savingsAmount: discount.amount
  };
};
```

### Add Combo to Cart

```javascript
const addComboToCart = async (combo, quantity = 1) => {
  try {
    const response = await fetch('/api/orders/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        combo: combo.id,
        quantity: quantity
      })
    });
    
    const result = await response.json();
    
    // result contains:
    // - combo_parent (the bundle item)
    // - combo_items (all products in bundle)
    // - total_price
    
    updateCart(result);
  } catch (error) {
    console.error('Failed to add combo:', error);
  }
};
```

### Display Combo in Cart

```javascript
const displayCartCombo = (comboItem) => {
  return `
    <div class="combo-item">
      <h3>${comboItem.combo_name}</h3>
      <div class="price">
        <span class="regular">Rs. ${comboItem.original_price}</span>
        <span class="final">Rs. ${comboItem.price}</span>
        <span class="badge">SAVE ${comboItem.discount_percent}%</span>
      </div>
      
      <div class="combo-contents">
        ${comboItem.combo_items.map(item => `
          <div class="item">
            - ${item.product_name} x${item.quantity}: Rs. ${item.subtotal}
          </div>
        `).join('')}
      </div>
      
      <div class="subtotal">Bundle Total: Rs. ${comboItem.subtotal}</div>
    </div>
  `;
};
```

---

## Admin Features

### View Combo Usage in Orders

In Django Admin:
1. Go to **Orders > Order Items**
2. Filter by `is_combo_parent=True` to see combo orders
3. Click on a combo parent to see all child items

### Manage Combos

In Django Admin:
1. Go to **Products > Product Combos**
2. Add/edit combos
3. Manage combo items and pricing

---

## Key Methods

### ComboService.get_combo_total_price()
Calculates sum of all item prices in combo

### ComboService.get_combo_discount()
Calculates savings vs buying items separately

### ComboService.create_combo_order_items()
Creates complete combo structure in order (parent + children)

### ComboService.finalize_order_combos()
Updates inventory after order confirmation

---

## Validation Rules

### Combo Order Cannot Be Created If:
- ❌ Combo is inactive (`is_active=False`)
- ❌ Combo has no items
- ❌ Products in combo are inactive

### Inventory Management:
- ✅ Each product variant stock is checked
- ✅ Stock is decremented only on order finalization
- ✅ Supports multiple quantities of same product in combo

---

## Database Relationships

```
ProductCombo
  ├── main_product (FK to Product)
  ├── items (ProductComboItem)
  │   ├── product (FK)
  │   └── quantity
  └── order_items (reverse FK from OrderItem)

Order
  └── items (OrderItem)
      ├── combo (FK to ProductCombo)
      ├── combo_parent (Self-referential)
      └── combo_items (reverse of combo_parent)
```

---

## Combining Deals + Combos

A combo can also have a deal applied:

```python
# Create combo
combo = ProductCombo.objects.get(id=1)

# Create deal for the combo
deal = Deal.objects.create(
    product=combo.main_product,
    title="Gaming Bundle Deal",
    deal_type="flash",
    discount_percent=15,
    total_quantity=50,
    start_at=timezone.now(),
    end_at=timezone.now() + timedelta(days=1),
    is_active=True
)

# When ordering combo with deal:
# - Original: Rs. 6,800 (combo price)
# - With 15% deal: Rs. 5,780 (additional discount)
```

---

## Testing

```python
from django.test import TestCase
from orders.services import ComboService
from product.models import Product, ProductCombo, ProductComboItem
from orders.models import Order

class ComboOrderTests(TestCase):
    def test_create_combo_order(self):
        # Setup
        product1 = Product.objects.create(name="Keyboard", base_price=5000)
        product2 = Product.objects.create(name="Mouse", base_price=1500)
        
        combo = ProductCombo.objects.create(
            name="Gaming Bundle",
            main_product=product1,
            combo_regular_price=6500,
            combo_selling_price=5500,
            is_active=True
        )
        
        ProductComboItem.objects.create(combo=combo, product=product1, quantity=1)
        ProductComboItem.objects.create(combo=combo, product=product2, quantity=1)
        
        # Create order
        order = Order.objects.create(user=self.user, total=5500)
        
        # Create combo items
        result = ComboService.create_combo_order_items(order, combo)
        
        # Assert
        self.assertIsNotNone(result['combo_parent'])
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['total_price'], 5500)
```

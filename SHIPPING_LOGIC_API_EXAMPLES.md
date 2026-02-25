# Order API Shipping Logic Examples

This document provides working API examples for the three shipping charge scenarios.

## Configuration
- **Shipping Cost**: Rs. 100.00
- **Tax Rate**: 10%
- **Free Shipping Promotion (ID: 1)** applied to: Products 2 (Gaming Keyboard), 3 (Gaming Mouse), 4 (Gaming Mouse Pad)
- **Combo (ID: 1)**: Gaming Bundle (NO free shipping)

---

## Scenario 1: ✅ Both items with free shipping → Shipping = Rs. 0

**Logic**: Both products (3 and 4) have free shipping promotion applied
- Item 1: Product 3 (Gaming Mouse) - HAS free shipping ✓
- Item 2: Product 4 (Gaming Mouse Pad) - HAS free shipping ✓
- Result: ALL items have free shipping → **Shipping = Rs. 0**

### Request
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "items_input": [
    {
      "product": 3,
      "quantity": 1
    },
    {
      "product": 4,
      "quantity": 2
    }
  ],
  "payment_method": "cod",
  "shipping_name": "John Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+9779841234567",
  "shipping_address": "123 Main Street, Apartment 4B",
  "shipping_city": "Kathmandu",
  "shipping_state": "Bagmati",
  "shipping_zip": "44600",
  "shipping_country": "Nepal",
  "billing_name": "John Doe",
  "billing_address": "123 Main Street, Apartment 4B",
  "billing_city": "Kathmandu",
  "billing_state": "Bagmati",
  "billing_zip": "44600",
  "billing_country": "Nepal"
}'
```

### Response
```json
{
  "id": 1,
  "order_number": "ORD-ABC123DEF456",
  "status": "pending",
  "payment_status": "pending",
  "payment_method": "cod",
  "payment_method_display": "Cash on Delivery",
  "subtotal": "150.00",
  "tax": "15.00",
  "shipping_cost": "0.00",
  "discount": "0.00",
  "total": "165.00",
  "items": [
    {
      "id": 1,
      "product": 3,
      "product_name": "Gaming Mouse",
      "quantity": 1,
      "price": "500.00",
      "original_price": "500.00",
      "discount_percent": 0,
      "subtotal": "500.00",
      "promotions": [
        {
          "id": 1,
          "title": "new promotion",
          "type": "free_shipping",
          "type_display": "Free Shipping"
        },
        {
          "id": 2,
          "title": "new gift for product",
          "type": "free_gift",
          "type_display": "Free Gift"
        }
      ]
    },
    {
      "id": 2,
      "product": 4,
      "product_name": "Gaming Mouse Pad",
      "quantity": 2,
      "price": "250.00",
      "original_price": "250.00",
      "discount_percent": 0,
      "subtotal": "500.00",
      "promotions": [
        {
          "id": 1,
          "title": "new promotion",
          "type": "free_shipping",
          "type_display": "Free Shipping"
        },
        {
          "id": 2,
          "title": "new gift for product",
          "type": "free_gift",
          "type_display": "Free Gift"
        }
      ]
    }
  ],
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:30:00Z"
}
```

💡 **Key Point**: Shipping = **Rs. 0.00** because BOTH items have free shipping

---

## Scenario 2: ✅ One item with free shipping, one without → Shipping = Rs. 100

**Logic**: Product 2 has free shipping, but Product 1 doesn't
- Item 1: Product 2 (Gaming Keyboard) - HAS free shipping ✓
- Item 2: Product 1 (Test Smartphone) - NO free shipping ✗
- Result: NOT ALL items have free shipping → **Shipping = Rs. 100**

### Request
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "items_input": [
    {
      "product": 2,
      "quantity": 1
    },
    {
      "product": 1,
      "quantity": 1
    }
  ],
  "payment_method": "khalti",
  "payment_transaction_id": "KH12345678901234567890",
  "shipping_name": "Jane Smith",
  "shipping_email": "jane@example.com",
  "shipping_phone": "+9779849876543",
  "shipping_address": "456 Second Avenue",
  "shipping_city": "Pokhara",
  "shipping_state": "Gandaki",
  "shipping_zip": "33700",
  "shipping_country": "Nepal",
  "billing_name": "Jane Smith",
  "billing_address": "456 Second Avenue",
  "billing_city": "Pokhara",
  "billing_state": "Gandaki",
  "billing_zip": "33700",
  "billing_country": "Nepal"
}'
```

### Response (Key Changes)
```json
{
  "id": 2,
  "order_number": "ORD-XYZ789GHI012",
  "status": "pending",
  "payment_status": "pending",
  "payment_method": "khalti",
  "payment_method_display": "Khalti",
  "subtotal": "900.00",
  "tax": "90.00",
  "shipping_cost": "100.00",
  "discount": "0.00",
  "total": "1090.00",
  "items": [
    {
      "id": 3,
      "product": 2,
      "product_name": "Gaming Keyboard",
      "quantity": 1,
      "price": "700.00",
      "promotions": [
        {
          "id": 1,
          "title": "new promotion",
          "type": "free_shipping",
          "type_display": "Free Shipping"
        },
        {
          "id": 2,
          "title": "new gift for product",
          "type": "free_gift",
          "type_display": "Free Gift"
        }
      ]
    },
    {
      "id": 4,
      "product": 1,
      "product_name": "Test Smartphone",
      "quantity": 1,
      "price": "200.00",
      "promotions": [
        {
          "id": 2,
          "title": "new gift for product",
          "type": "free_gift",
          "type_display": "Free Gift"
        }
      ]
    }
  ],
  "created_at": "2026-02-25T11:00:00Z",
  "updated_at": "2026-02-25T11:00:00Z"
}
```

💡 **Key Point**: Shipping = **Rs. 100.00** because Product 1 (Test Smartphone) doesn't have free shipping

---

## Scenario 3: ✅ Combo + Item with free shipping → Shipping = Rs. 100

**Logic**: Combo doesn't have free shipping, even if the other item does
- Item 1: Combo 1 (Gaming Bundle) - NO free shipping ✗
- Item 2: Product 4 (Gaming Mouse Pad) - HAS free shipping ✓
- Result: Combo doesn't have free shipping → **Shipping = Rs. 100**

### Request
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "items_input": [
    {
      "combo": 1,
      "quantity": 1
    },
    {
      "product": 4,
      "quantity": 1
    }
  ],
  "payment_method": "esewa",
  "payment_transaction_id": "ES123456789012",
  "shipping_name": "Ram Kumar",
  "shipping_email": "ram@example.com",
  "shipping_phone": "+9779840000000",
  "shipping_address": "789 Third Road",
  "shipping_city": "Lalitpur",
  "shipping_state": "Bagmati",
  "shipping_zip": "44700",
  "shipping_country": "Nepal",
  "billing_name": "Ram Kumar",
  "billing_address": "789 Third Road",
  "billing_city": "Lalitpur",
  "billing_state": "Bagmati",
  "billing_zip": "44700",
  "billing_country": "Nepal"
}'
```

### Response (Key Changes)
```json
{
  "id": 3,
  "order_number": "ORD-JKL345MNO678",
  "status": "pending",
  "payment_status": "pending",
  "payment_method": "esewa",
  "payment_method_display": "eSewa",
  "subtotal": "1250.00",
  "tax": "125.00",
  "shipping_cost": "100.00",
  "discount": "0.00",
  "total": "1475.00",
  "items": [
    {
      "id": 5,
      "product": null,
      "product_name": "Gaming Bundle",
      "quantity": 1,
      "combo": 1,
      "combo_name": "Gaming Bundle",
      "is_combo_parent": true,
      "price": "1000.00",
      "promotions": []
    },
    {
      "id": 6,
      "product": 4,
      "product_name": "Gaming Mouse Pad",
      "quantity": 1,
      "price": "250.00",
      "promotions": [
        {
          "id": 1,
          "title": "new promotion",
          "type": "free_shipping",
          "type_display": "Free Shipping"
        },
        {
          "id": 2,
          "title": "new gift for product",
          "type": "free_gift",
          "type_display": "Free Gift"
        }
      ]
    }
  ],
  "created_at": "2026-02-25T11:30:00Z",
  "updated_at": "2026-02-25T11:30:00Z"
}
```

💡 **Key Point**: Shipping = **Rs. 100.00** because the Combo doesn't have free shipping (even though Product 4 does)

---

## Summary Table

| Scenario | Item 1 | Item 2 | Promotions | Shipping Cost |
|----------|--------|--------|-----------|---------------|
| 1 | Product 3 (free shipping) | Product 4 (free shipping) | Both have free shipping | **Rs. 0.00** ✓ |
| 2 | Product 2 (free shipping) | Product 1 (no free shipping) | Only one has free shipping | **Rs. 100.00** ✓ |
| 3 | Combo (no free shipping) | Product 4 (free shipping) | One doesn't have free shipping | **Rs. 100.00** ✓ |

---

## Header Requirements

For authenticated requests, include:
```
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

Or use session authentication if using Django's token-based auth.

## Notes

- Free shipping is automatically detected from active promotions on each product
- The logic is: **Shipping is waived ONLY if ALL items have free shipping**
- If ANY item (including combos) lacks free shipping, the full shipping cost is applied
- Tax is calculated on the subtotal (before shipping): `tax = subtotal × 0.10`
- Total = subtotal + tax + shipping_cost

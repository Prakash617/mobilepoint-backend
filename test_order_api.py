"""
Test Order API with Deals and Combos
This script tests the REST API endpoints for creating orders with deals and combos
"""
import requests
import json

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/orders/"

# Authentication - You'll need to get a token or use session auth
# For testing, we'll assume you have authentication set up
# Replace these with actual credentials
AUTH_EMAIL = "testuser@example.com"
AUTH_PASSWORD = "testpass123"


def get_auth_token():
    """Get authentication token"""
    # This depends on your authentication setup
    # Example for token-based auth:
    # response = requests.post(f"{BASE_URL}/api/auth/login/", {
    #     "email": AUTH_EMAIL,
    #     "password": AUTH_PASSWORD
    # })
    # return response.json()['token']
    
    # For session-based auth, use requests.Session()
    return None


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_response(response):
    """Print formatted API response"""
    print(f"\nStatus Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_regular_order():
    """Test creating a regular product order"""
    print_section("TEST 1: Regular Product Order (No Deal)")
    
    # Get product IDs from database first
    print("\nNote: You need to know the product IDs from your database")
    print("Example payload:")
    
    payload = {
        "items": [
            {
                "product": 1,  # Replace with actual product ID
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
        "notes": "Regular order test"
    }
    
    print(json.dumps(payload, indent=2))
    print("\nCURL Command:")
    print(f"curl -X POST {API_URL} \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -d '{json.dumps(payload)}'")


def test_deal_order():
    """Test creating an order with a deal"""
    print_section("TEST 2: Order with Deal")
    
    print("\nNote: You need to know the product ID and deal ID from your database")
    print("Example payload:")
    
    payload = {
        "items": [
            {
                "product": 1,      # Replace with actual product ID
                "deal": 1,         # Replace with actual deal ID
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
        "billing_country": "USA",
        "notes": "Deal order test - expecting discount"
    }
    
    print(json.dumps(payload, indent=2))
    print("\nCURL Command:")
    print(f"curl -X POST {API_URL} \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -d '{json.dumps(payload)}'")


def test_combo_order():
    """Test creating an order with a combo"""
    print_section("TEST 3: Order with Combo")
    
    print("\nNote: You need to know the combo ID from your database")
    print("Example payload:")
    
    payload = {
        "items": [
            {
                "combo": 1,    # Replace with actual combo ID
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
        "billing_country": "USA",
        "notes": "Combo order test"
    }
    
    print(json.dumps(payload, indent=2))
    print("\nCURL Command:")
    print(f"curl -X POST {API_URL} \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -d '{json.dumps(payload)}'")


def test_mixed_order():
    """Test creating an order with both deal and combo"""
    print_section("TEST 4: Mixed Order (Deal + Combo)")
    
    print("\nNote: You need to know the product, deal, and combo IDs from your database")
    print("Example payload:")
    
    payload = {
        "items": [
            {
                "product": 1,      # Product with deal
                "deal": 1,         # Deal ID
                "quantity": 1
            },
            {
                "combo": 1,        # Combo ID
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
        "billing_country": "USA",
        "notes": "Mixed order test - deal item + combo"
    }
    
    print(json.dumps(payload, indent=2))
    print("\nCURL Command:")
    print(f"curl -X POST {API_URL} \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"  -d '{json.dumps(payload)}'")


def get_actual_ids():
    """Helper to get actual IDs from the database"""
    print_section("GETTING ACTUAL IDS FROM DATABASE")
    
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilepoint.settings')
    django.setup()
    
    from product.models import Product, Deal, ProductCombo
    
    print("\n📦 Available Products:")
    for product in Product.objects.filter(is_active=True)[:5]:
        print(f"  ID: {product.id} - {product.name} (Rs. {product.base_price})")
    
    print("\n🔥 Available Deals:")
    for deal in Deal.objects.filter(is_active=True)[:5]:
        print(f"  ID: {deal.id} - {deal.title} (Product: {deal.product.name}, {deal.discount_percent}% off)")
    
    print("\n📦 Available Combos:")
    for combo in ProductCombo.objects.filter(is_active=True)[:5]:
        print(f"  ID: {combo.id} - {combo.name} (Rs. {combo.combo_selling_price})")
    
    return True


def main():
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "ORDER API TESTING" + " " * 35 + "║")
    print("╚" + "═" * 78 + "╝")
    
    print("\nThis script provides example API requests for testing order creation")
    print("with deals and combos via the REST API.")
    print("\nFirst, let's get the actual IDs from your database...")
    
    try:
        get_actual_ids()
    except Exception as e:
        print(f"\n⚠️  Could not fetch IDs: {e}")
        print("Make sure Django is properly configured.")
    
    # Show example requests
    test_regular_order()
    test_deal_order()
    test_combo_order()
    test_mixed_order()
    
    print("\n" + "=" * 80)
    print("USAGE INSTRUCTIONS")
    print("=" * 80)
    print("""
1. Make sure your Django server is running:
   python manage.py runserver

2. Get an authentication token or use session authentication

3. Use the CURL commands above or use a tool like Postman/Insomnia

4. For session auth, you can use the browsable API:
   Navigate to http://127.0.0.1:8000/api/orders/
   Login with your credentials
   Use the form to create orders

5. The response will include:
   - Order number
   - Total price with discounts applied
   - Order items with deal/combo information
   - Shipping and billing details

Expected Response Structure:
{
  "id": 1,
  "order_number": "ORD-XXXXXXXXXXXX",
  "status": "pending",
  "payment_status": "pending",
  "subtotal": "65000.00",
  "discount": "35000.00",
  "tax": "6500.00",
  "shipping_cost": "10.00",
  "total": "71510.00",
  "items": [
    {
      "id": 1,
      "product_name": "Test Smartphone",
      "quantity": 2,
      "original_price": "50000.00",
      "price": "32500.00",
      "discount_percent": 35,
      "deal": 1,
      "deal_title": "Flash Sale - Smartphone",
      "subtotal": "65000.00"
    }
  ],
  ...
}
    """)
    print("=" * 80)


if __name__ == '__main__':
    main()

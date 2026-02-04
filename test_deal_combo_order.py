"""
Test script for creating orders with Deals and Combos
This script demonstrates creating orders with both deal discounts and product combos
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilepoint.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from product.models import Product, Category, Brand, Deal, ProductCombo, ProductComboItem
from orders.models import Order, OrderItem
from orders.services import OrderService, ComboService
from django.db import transaction


def create_test_data():
    """Create test products, deals, and combos"""
    print("=" * 80)
    print("CREATING TEST DATA")
    print("=" * 80)
    
    # Get or create category and brand
    category, _ = Category.objects.get_or_create(
        name="Electronics",
        defaults={
            'slug': 'electronics',
            'description': 'Electronic items'
        }
    )
    
    brand, created = Brand.objects.get_or_create(
        name="TestBrand",
        defaults={
            'slug': 'testbrand',
            'description': 'Test brand for demo'
        }
    )
    
    # Link brand to category
    if category not in brand.category.all():
        brand.category.add(category)
    
    # Create test products
    products = {}
    
    # Product 1: Smartphone
    products['smartphone'], created = Product.objects.get_or_create(
        slug='test-smartphone',
        defaults={
            'name': 'Test Smartphone',
            'description': 'A test smartphone for deal testing',
            'category': category,
            'brand': brand,
            'base_price': Decimal('50000.00'),
            'is_active': True
        }
    )
    if created:
        print(f"✓ Created product: {products['smartphone'].name} - Rs. {products['smartphone'].base_price}")
    
    # Product 2: Gaming Keyboard
    products['keyboard'], created = Product.objects.get_or_create(
        slug='test-gaming-keyboard',
        defaults={
            'name': 'Gaming Keyboard',
            'description': 'RGB gaming keyboard',
            'category': category,
            'brand': brand,
            'base_price': Decimal('5000.00'),
            'is_active': True
        }
    )
    if created:
        print(f"✓ Created product: {products['keyboard'].name} - Rs. {products['keyboard'].base_price}")
    
    # Product 3: Gaming Mouse
    products['mouse'], created = Product.objects.get_or_create(
        slug='test-gaming-mouse',
        defaults={
            'name': 'Gaming Mouse',
            'description': 'High DPI gaming mouse',
            'category': category,
            'brand': brand,
            'base_price': Decimal('1500.00'),
            'is_active': True
        }
    )
    if created:
        print(f"✓ Created product: {products['mouse'].name} - Rs. {products['mouse'].base_price}")
    
    # Product 4: Mouse Pad
    products['mousepad'], created = Product.objects.get_or_create(
        slug='test-mousepad',
        defaults={
            'name': 'Gaming Mouse Pad',
            'description': 'Large gaming mouse pad',
            'category': category,
            'brand': brand,
            'base_price': Decimal('500.00'),
            'is_active': True
        }
    )
    if created:
        print(f"✓ Created product: {products['mousepad'].name} - Rs. {products['mousepad'].base_price}")
    
    # Create a Deal for the smartphone
    now = timezone.now()
    deal, created = Deal.objects.get_or_create(
        title='Flash Sale - Smartphone',
        product=products['smartphone'],
        defaults={
            'deal_type': 'flash',
            'discount_percent': 35,
            'total_quantity': 50,
            'sold_quantity': 0,
            'start_at': now - timedelta(hours=1),
            'end_at': now + timedelta(days=7),
            'is_active': True,
            'is_featured': True
        }
    )
    if created:
        print(f"\n✓ Created Deal: {deal.title}")
        print(f"  - Discount: {deal.discount_percent}%")
        print(f"  - Total Quantity: {deal.total_quantity}")
        print(f"  - Remaining: {deal.remaining_quantity}")
    
    # Create a ProductCombo (Gaming Bundle)
    combo, created = ProductCombo.objects.get_or_create(
        slug='test-gaming-bundle',
        defaults={
            'name': 'Gaming Bundle',
            'main_product': products['keyboard'],
            'description': 'Complete gaming setup',
            'combo_regular_price': Decimal('8500.00'),  # 5000 + 1500*2 + 500
            'combo_selling_price': Decimal('6800.00'),  # 20% discount
            'is_active': True,
            'is_featured': True
        }
    )
    
    if created:
        # Add items to the combo
        ProductComboItem.objects.create(combo=combo, product=products['keyboard'], quantity=1)
        ProductComboItem.objects.create(combo=combo, product=products['mouse'], quantity=2)
        ProductComboItem.objects.create(combo=combo, product=products['mousepad'], quantity=1)
        
        print(f"\n✓ Created Combo: {combo.name}")
        print(f"  - Regular Price: Rs. {combo.combo_regular_price}")
        print(f"  - Selling Price: Rs. {combo.combo_selling_price}")
        print(f"  - Savings: Rs. {combo.combo_regular_price - combo.combo_selling_price}")
        print(f"  - Items:")
        for item in combo.items.all():
            print(f"    • {item.product.name} x{item.quantity}")
    
    return products, deal, combo


def test_deal_order(user, deal, product):
    """Test creating an order with a deal"""
    print("\n" + "=" * 80)
    print("TEST 1: CREATING ORDER WITH DEAL")
    print("=" * 80)
    
    with transaction.atomic():
        # Calculate pricing
        pricing = OrderService.calculate_item_price(product, None, deal)
        
        print(f"\nProduct: {product.name}")
        print(f"Original Price: Rs. {pricing['original_price']}")
        print(f"Discount: {pricing['discount_percent']}%")
        print(f"Final Price: Rs. {pricing['final_price']}")
        
        quantity = 2
        print(f"Quantity: {quantity}")
        
        # Calculate totals
        subtotal = pricing['final_price'] * quantity
        tax = subtotal * Decimal('0.10')
        shipping = Decimal('10.00')
        total = subtotal + tax + shipping
        discount_amount = (pricing['original_price'] - pricing['final_price']) * quantity
        
        print(f"\nOrder Calculation:")
        print(f"Subtotal: Rs. {subtotal}")
        print(f"Discount Saved: Rs. {discount_amount}")
        print(f"Tax (10%): Rs. {tax}")
        print(f"Shipping: Rs. {shipping}")
        print(f"Total: Rs. {total}")
        
        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping,
            discount=discount_amount,
            total=total,
            shipping_name="Test Customer",
            shipping_email="test@example.com",
            shipping_phone="+1234567890",
            shipping_address="123 Test Street",
            shipping_city="Test City",
            shipping_state="Test State",
            shipping_zip="12345",
            shipping_country="Pakistan",
            billing_name="Test Customer",
            billing_address="123 Test Street",
            billing_city="Test City",
            billing_state="Test State",
            billing_zip="12345",
            billing_country="Pakistan",
            status='pending',
            payment_status='pending'
        )
        
        # Create order item with deal
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            deal=deal,
            quantity=quantity,
            original_price=pricing['original_price'],
            price=pricing['final_price'],
            discount_percent=pricing['discount_percent']
        )
        
        print(f"\n✅ ORDER CREATED: {order.order_number}")
        print(f"\nOrder Items:")
        for item in order.items.all():
            print(f"  • {item.product_name} x{item.quantity}")
            print(f"    Original: Rs. {item.original_price}")
            print(f"    Discount: {item.discount_percent}%")
            print(f"    Price: Rs. {item.price}")
            print(f"    Subtotal: Rs. {item.subtotal}")
            if item.deal:
                print(f"    Deal: {item.deal.title}")
        
        print(f"\nOrder Status: {order.status}")
        print(f"Payment Status: {order.payment_status}")
        
        # Confirm order (this increments deal sold quantity)
        print(f"\nDeal inventory before confirmation: {deal.remaining_quantity}")
        order.status = 'confirmed'
        order.save()
        order.finalize()
        
        # Reload deal to see updated quantity
        deal.refresh_from_db()
        print(f"Deal inventory after confirmation: {deal.remaining_quantity}")
        print(f"Deal sold quantity: {deal.sold_quantity}")
        
        return order


def test_combo_order(user, combo):
    """Test creating an order with a combo"""
    print("\n" + "=" * 80)
    print("TEST 2: CREATING ORDER WITH COMBO")
    print("=" * 80)
    
    with transaction.atomic():
        # Calculate combo pricing
        combo_pricing = ComboService.get_combo_discount(combo)
        
        print(f"\nCombo: {combo.name}")
        print(f"Items in combo:")
        for item in combo.items.all():
            print(f"  • {item.product.name} x{item.quantity} = Rs. {item.product.base_price * item.quantity}")
        
        print(f"\nRegular Price: Rs. {combo_pricing['regular_price']}")
        print(f"Selling Price: Rs. {combo_pricing['selling_price']}")
        print(f"Discount: {combo_pricing['discount_percent']}%")
        print(f"You Save: Rs. {combo_pricing['discount_amount']}")
        
        quantity = 1
        print(f"\nOrdering {quantity} combo(s)")
        
        # Calculate totals
        subtotal = combo_pricing['selling_price'] * quantity
        tax = subtotal * Decimal('0.10')
        shipping = Decimal('10.00')
        total = subtotal + tax + shipping
        discount_amount = combo_pricing['discount_amount'] * quantity
        
        print(f"\nOrder Calculation:")
        print(f"Subtotal: Rs. {subtotal}")
        print(f"Discount Saved: Rs. {discount_amount}")
        print(f"Tax (10%): Rs. {tax}")
        print(f"Shipping: Rs. {shipping}")
        print(f"Total: Rs. {total}")
        
        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping,
            discount=discount_amount,
            total=total,
            shipping_name="Test Customer 2",
            shipping_email="test2@example.com",
            shipping_phone="+1234567890",
            shipping_address="456 Combo Street",
            shipping_city="Bundle City",
            shipping_state="Combo State",
            shipping_zip="54321",
            shipping_country="Pakistan",
            billing_name="Test Customer 2",
            billing_address="456 Combo Street",
            billing_city="Bundle City",
            billing_state="Combo State",
            billing_zip="54321",
            billing_country="Pakistan",
            status='pending',
            payment_status='pending'
        )
        
        # Create combo order items using service
        result = ComboService.create_combo_order_items(order, combo, quantity)
        
        print(f"\n✅ ORDER CREATED: {order.order_number}")
        print(f"\nOrder Items:")
        
        # Show parent item
        parent = result['combo_parent']
        print(f"\n  [COMBO PARENT]")
        print(f"  • {parent.product_name} x{parent.quantity}")
        print(f"    Original: Rs. {parent.original_price}")
        print(f"    Price: Rs. {parent.price}")
        print(f"    Discount: {parent.discount_percent}%")
        print(f"    Subtotal: Rs. {parent.subtotal}")
        
        # Show child items
        print(f"\n  [COMBO ITEMS]")
        for item in result['items']:
            print(f"  • {item.product_name} x{item.quantity}")
            print(f"    Price: Rs. {item.price}")
            print(f"    Subtotal: Rs. {item.subtotal}")
        
        print(f"\nOrder Status: {order.status}")
        print(f"Payment Status: {order.payment_status}")
        
        return order


def test_mixed_order(user, deal, product, combo):
    """Test creating an order with both deal items and combo items"""
    print("\n" + "=" * 80)
    print("TEST 3: CREATING ORDER WITH BOTH DEAL AND COMBO")
    print("=" * 80)
    
    with transaction.atomic():
        print("\nThis order will contain:")
        print("1. Smartphone with 35% deal discount (x1)")
        print("2. Gaming Bundle combo (x1)")
        
        # Calculate deal item pricing
        deal_pricing = OrderService.calculate_item_price(product, None, deal)
        deal_subtotal = deal_pricing['final_price'] * 1
        
        # Calculate combo pricing
        combo_pricing = ComboService.get_combo_discount(combo)
        combo_subtotal = combo_pricing['selling_price'] * 1
        
        # Calculate order totals
        subtotal = deal_subtotal + combo_subtotal
        discount_amount = ((deal_pricing['original_price'] - deal_pricing['final_price']) * 1 + 
                          combo_pricing['discount_amount'] * 1)
        tax = subtotal * Decimal('0.10')
        shipping = Decimal('10.00')
        total = subtotal + tax + shipping
        
        print(f"\nOrder Calculation:")
        print(f"Deal Item Subtotal: Rs. {deal_subtotal}")
        print(f"Combo Subtotal: Rs. {combo_subtotal}")
        print(f"Total Subtotal: Rs. {subtotal}")
        print(f"Total Discount Saved: Rs. {discount_amount}")
        print(f"Tax (10%): Rs. {tax}")
        print(f"Shipping: Rs. {shipping}")
        print(f"Grand Total: Rs. {total}")
        
        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping,
            discount=discount_amount,
            total=total,
            shipping_name="Test Customer 3",
            shipping_email="test3@example.com",
            shipping_phone="+1234567890",
            shipping_address="789 Mixed Street",
            shipping_city="Hybrid City",
            shipping_state="Mixed State",
            shipping_zip="98765",
            shipping_country="Pakistan",
            billing_name="Test Customer 3",
            billing_address="789 Mixed Street",
            billing_city="Hybrid City",
            billing_state="Mixed State",
            billing_zip="98765",
            billing_country="Pakistan",
            status='pending',
            payment_status='pending'
        )
        
        # Create deal order item
        deal_item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            deal=deal,
            quantity=1,
            original_price=deal_pricing['original_price'],
            price=deal_pricing['final_price'],
            discount_percent=deal_pricing['discount_percent']
        )
        
        # Create combo order items
        combo_result = ComboService.create_combo_order_items(order, combo, 1)
        
        print(f"\n✅ ORDER CREATED: {order.order_number}")
        print(f"\nOrder Items:")
        
        # Show all items
        for item in order.items.filter(combo_parent__isnull=True):
            if item.is_combo_parent:
                print(f"\n  [COMBO PARENT]")
                print(f"  • {item.product_name} x{item.quantity}")
                print(f"    Original: Rs. {item.original_price}")
                print(f"    Price: Rs. {item.price}")
                print(f"    Discount: {item.discount_percent}%")
                print(f"    Subtotal: Rs. {item.subtotal}")
                
                # Show child items
                if item.combo_items.exists():
                    print(f"\n    [ITEMS IN COMBO]")
                    for child in item.combo_items.all():
                        print(f"    • {child.product_name} x{child.quantity}")
            elif item.deal:
                print(f"\n  [DEAL ITEM]")
                print(f"  • {item.product_name} x{item.quantity}")
                print(f"    Original: Rs. {item.original_price}")
                print(f"    Discount: {item.discount_percent}%")
                print(f"    Price: Rs. {item.price}")
                print(f"    Subtotal: Rs. {item.subtotal}")
                print(f"    Deal: {item.deal.title}")
        
        print(f"\nOrder Status: {order.status}")
        print(f"Payment Status: {order.payment_status}")
        
        # Confirm order
        order.status = 'confirmed'
        order.save()
        order.finalize()
        
        print(f"\n✅ Order confirmed and finalized!")
        
        return order


def main():
    """Main test function"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "DEAL & COMBO ORDER TESTING" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='testuser@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"\n✓ Created test user: {user.email}")
    else:
        print(f"\n✓ Using existing user: {user.email}")
    
    # Create test data
    products, deal, combo = create_test_data()
    
    # Test 1: Order with Deal
    order1 = test_deal_order(user, deal, products['smartphone'])
    
    # Test 2: Order with Combo
    order2 = test_combo_order(user, combo)
    
    # Test 3: Order with both Deal and Combo
    order3 = test_mixed_order(user, deal, products['smartphone'], combo)
    
    # Summary
    print("\n" + "=" * 80)
    print("TESTING COMPLETE - SUMMARY")
    print("=" * 80)
    print(f"\n✅ Successfully created 3 test orders:")
    print(f"   1. {order1.order_number} - Deal Order (Rs. {order1.total})")
    print(f"   2. {order2.order_number} - Combo Order (Rs. {order2.total})")
    print(f"   3. {order3.order_number} - Mixed Order (Rs. {order3.total})")
    
    print(f"\n✅ All tests passed successfully!")
    print(f"\nYou can now check these orders in the Django admin panel.")
    print("=" * 80)


if __name__ == '__main__':
    main()

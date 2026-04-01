from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from accounts.models import User
from website.models import SiteSettings

class OrderUserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user information within orders.
    
    Fields:
    - id: User ID
    - username: User's username
    - email: User's email address
    - first_name: User's first name
    - last_name: User's last name
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for displaying order items with product/variant/combo details and promotions"""
    deal_title = serializers.CharField(source='deal.title', read_only=True, allow_null=True)
    deal_type = serializers.CharField(source='deal.deal_type', read_only=True, allow_null=True)
    combo_name = serializers.CharField(source='combo.name', read_only=True, allow_null=True)
    promotions = serializers.SerializerMethodField()
    combo_items = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_variant', 'product_name', 'variant_name', 
            'quantity', 'original_price', 'price', 'discount_percent', 
            'deal', 'deal_title', 'deal_type',
            'promotions', 'free_gift_detail',
            'combo', 'combo_name', 'combo_parent', 'combo_items', 'is_combo_parent',
            'subtotal', 'created_at'
        ]
        
        read_only_fields = ['subtotal', 'product_name', 'variant_name', 'created_at', 'original_price', 'discount_percent', 'promotions', 'free_gift_detail']
    
    def get_promotions(self, obj) -> list[dict]:
        """Get all promotions applied to this order item"""
        promotions = obj.promotions.all()
        return [{
            'id': p.id,
            'title': p.title,
            'type': p.promotion_type,
            'type_display': p.get_promotion_type_display()
        } for p in promotions]
    
    def get_combo_items(self, obj) -> list[dict] | None:
        """Get child items if this is a combo parent"""
        if obj.is_combo_parent:
            child_items = obj.combo_items.all()
            return OrderItemSerializer(child_items, many=True, context=self.context).data
        return None


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items. Supports both products and variants with optional deals and combos."""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'product_variant', 'deal', 'combo', 'quantity']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set combo queryset to only active combos
        from product.models import ProductCombo
        self.fields['combo'].queryset = ProductCombo.objects.filter(is_active=True)
    
    def validate(self, data):
        """Validate that either product/variant OR combo is provided, and validate deal/combo constraints"""
        product = data.get('product')
        product_variant = data.get('product_variant')
        deal = data.get('deal')
        combo = data.get('combo')
        
        # Check for combo vs product/variant
        if combo:
            if product or product_variant:
                raise serializers.ValidationError(
                    "When ordering a combo, do not provide 'product' or 'product_variant'."
                )
            if deal:
                raise serializers.ValidationError(
                    "Combos cannot be combined with deals."
                )
            
            # Validate combo is active
            if not combo.is_active:
                raise serializers.ValidationError({
                    'combo': 'Selected combo is not active.'
                })
        else:
            # Regular product/variant order
            if not product and not product_variant:
                raise serializers.ValidationError(
                    "Either 'product', 'product_variant', or 'combo' must be provided."
                )
            
            if product and product_variant:
                raise serializers.ValidationError(
                    "Provide either 'product' or 'product_variant', not both."
                )
            
            # Validate deal if provided
            if deal:
                from django.utils import timezone
                now = timezone.now()
                
                # Check if deal is active
                if not deal.is_active:
                    raise serializers.ValidationError({
                        'deal': 'Selected deal is not active.'
                    })
                
                # Check if deal is in valid time window
                if not (deal.start_at <= now <= deal.end_at):
                    raise serializers.ValidationError({
                        'deal': 'Selected deal is not currently available.'
                    })
                
                # Check if deal product matches
                if deal.product != product and (not product_variant or deal.product != product_variant.product):
                    raise serializers.ValidationError({
                        'deal': 'Selected deal does not apply to this product.'
                    })
                
                # Check inventory
                quantity = data.get('quantity', 1)
                if deal.remaining_quantity < quantity:
                    raise serializers.ValidationError({
                        'deal': f'Insufficient deal inventory. Only {deal.remaining_quantity} items remaining.'
                    })
        
        return data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history tracking changes"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'notes', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing orders with summary information"""
    user = OrderUserSerializer(read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'order_status', 'payment_status', 'payment_method', 'payment_method_display',
            'total', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed order information including items, status history, and promotions"""
    user = OrderUserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'order_status', 'payment_status', 'payment_method', 'payment_method_display', 
            'payment_transaction_id',
            'subtotal', 'tax', 'shipping_cost', 'discount', 'total',
            'shipping_name', 'shipping_email', 'shipping_phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_zip', 'shipping_country',
            'billing_name', 'billing_address', 'billing_city',
            'billing_state', 'billing_zip', 'billing_country',
            'notes', 'tracking_number',
            'items', 'status_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'user', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new orders.
    
    This serializer handles the creation of orders with items including:
    - Regular products with optional deals
    - Product variants with optional deals
    - Product combos (bundles)
    - Multiple payment methods (COD, Khalti, eSewa, Bank Transfer)
    
    It automatically:
    - Calculates subtotal from items
    - Applies deal discounts when specified
    - Applies combo discounts
    - Calculates 10% tax
    - Adds flat $10 shipping cost
    - Creates initial order status history
    - Associates order with authenticated user
    
    Request Examples:
    
    1. Regular product order with COD:
    {
        "items": [
            {
                "product": 1,
                "quantity": 2
            }
        ],
        "payment_method": "cod",
        "shipping_name": "John Doe",
        ...
    }
    
    2. Order with deal and Khalti payment:
    {
        "items": [
            {
                "product": 1,
                "deal": 5,
                "quantity": 2
            }
        ],
        "payment_method": "khalti",
        "payment_transaction_id": "KH123456789",
        "shipping_name": "John Doe",
        ...
    }
    
    3. Order with combo and eSewa payment:
    {
        "items": [
            {
                "combo": 3,
                "quantity": 1
            }
        ],
        "shipping_name": "John Doe",
        ...
    }
    
    4. Mixed order (deal + combo):
    {
        "items": [
            {
                "product": 1,
                "deal": 5,
                "quantity": 1
            },
            {
                "combo": 3,
                "quantity": 1
            }
        ],
        "payment_method": "esewa",
        "payment_transaction_id": "ES987654321",
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
        "notes": "Please deliver after 5pm"
    }
    
    Payment Methods:
    - cod: Cash on Delivery (default)
    - khalti: Khalti Payment Gateway
    - esewa: eSewa Payment Gateway
    - bank_transfer: Bank Transfer
    """
    items_input = OrderItemCreateSerializer(many=True, write_only=True, source='items')
    items = OrderItemSerializer(many=True, read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            # Request fields (write_only handled by items_input)
            'items_input', 'payment_method', 'payment_transaction_id',
            'shipping_name', 'shipping_email', 'shipping_phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_zip', 'shipping_country',
            'billing_name', 'billing_address', 'billing_city',
            'billing_state', 'billing_zip', 'billing_country', 'notes',
            # Response fields (read_only)
            'id', 'order_number', 'user', 'order_status', 'payment_status', 'payment_method_display',
            'subtotal', 'tax', 'shipping_cost', 'discount', 'total',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_number', 'user', 'order_status', 'subtotal', 'tax', 'shipping_cost', 'discount', 'total', 'items', 'created_at', 'updated_at']
    
    def validate_payment_method(self, value):
        """Validate payment method"""
        valid_methods = ['cod', 'khalti', 'esewa', 'bank_transfer']
        if value not in valid_methods:
            raise serializers.ValidationError(f"Invalid payment method. Choose from: {', '.join(valid_methods)}")
        return value
    
    def validate(self, data):
        """Additional validation for payment methods"""
        payment_method = data.get('payment_method', 'cod')
        payment_transaction_id = data.get('payment_transaction_id')
        
        # For online payment methods, transaction ID might be required
        if payment_method in ['khalti', 'esewa'] and not payment_transaction_id:
            # Transaction ID can be added later after payment confirmation
            pass
        
        return data
    
    def create(self, validated_data):
        from decimal import Decimal
        from django.db import transaction
        from django.utils import timezone
        from orders.services import OrderService, ComboService
        from product.models import Promotion
        
        items_data = validated_data.pop('items')
        user = self.context.get('request').user if 'request' in self.context else validated_data.get('user')

        with transaction.atomic():
            # Calculate totals
            subtotal = Decimal('0.00')
            total_discount = Decimal('0.00')
            order_items_to_create = []
            items_with_free_shipping = []  # Track which items have free shipping
            
            # Get current time for promotion checks
            now = timezone.now()
            
            for item_data in items_data:
                combo = item_data.get('combo')
                has_free_shipping = False  # Track if this item has free shipping
                
                if combo:
                    # Handle combo item
                    quantity = item_data['quantity']
                    combo_pricing = ComboService.get_combo_discount(combo)
                    
                    item_subtotal = combo_pricing['selling_price'] * quantity
                    item_discount = combo_pricing['discount_amount'] * quantity
                    
                    subtotal += item_subtotal
                    total_discount += item_discount
                    
                    order_items_to_create.append({
                        'type': 'combo',
                        'combo': combo,
                        'quantity': quantity,
                        'pricing': combo_pricing,
                        'product': combo.main_product,
                        'promotion_data': None,
                        'has_free_shipping': False
                    })
                else:
                    # Handle regular product/variant with optional deal
                    product = item_data.get('product')
                    variant = item_data.get('product_variant')
                    deal = item_data.get('deal')
                    quantity = item_data['quantity']
                    
                    # Calculate pricing with deal if provided
                    pricing = OrderService.calculate_item_price(
                        product=product or (variant.product if variant else None),
                        product_variant=variant,
                        deal=deal
                    )
                    
                    item_subtotal = pricing['final_price'] * quantity
                    item_discount = (pricing['original_price'] - pricing['final_price']) * quantity
                    
                    subtotal += item_subtotal
                    total_discount += item_discount
                    
                    # Check for active promotions on this product
                    product_obj = variant.product if variant else product
                    promotion_data = {
                        'free_shipping_promo': None,
                        'free_gift_promo': None,
                        'free_gift_detail': None
                    }
                    
                    active_promotions = product_obj.promotions.filter(
                        is_active=True,
                        start_date__lte=now,
                        end_date__gte=now
                    )
                    
                    for promo in active_promotions:
                        if promo.promotion_type == 'free_shipping':
                            promotion_data['free_shipping_promo'] = promo
                            has_free_shipping = True  # Mark that this item has free shipping
                        elif promo.promotion_type == 'free_gift':
                            promotion_data['free_gift_promo'] = promo
                            promotion_data['free_gift_detail'] = promo.title
                    
                    order_items_to_create.append({
                        'type': 'regular',
                        'product': product,
                        'variant': variant,
                        'deal': deal,
                        'quantity': quantity,
                        'pricing': pricing,
                        'promotion_data': promotion_data,
                        'has_free_shipping': has_free_shipping
                    })
            
            # Calculate tax and total
            site_settings = SiteSettings.objects.get(id=1)
            tax = subtotal * Decimal(str(site_settings.tax / 100))  # Tax from SiteSettings
            shipping_cost = site_settings.shipping_cost  # Shipping cost from SiteSettings
            
            # Only apply free shipping if ALL items in the order have free shipping promotion
            # If ANY item doesn't have free shipping, add shipping charge
            all_items_have_free_shipping = all(item['has_free_shipping'] for item in order_items_to_create)
            
            if not all_items_have_free_shipping:
                # At least one item doesn't have free shipping - add shipping cost
                shipping_cost = site_settings.shipping_cost
            else:
                # All items have free shipping - waive shipping cost
                shipping_cost = Decimal('0.00')
            
            total = subtotal + tax + shipping_cost
            
            # Create order
            order = Order.objects.create(
                subtotal=subtotal,
                tax=tax,
                shipping_cost=shipping_cost,
                discount=total_discount,
                total=total,
                **validated_data
            )
            
            # Create order items
            for item_info in order_items_to_create:
                if item_info['type'] == 'combo':
                    # Create combo items (parent + children)
                    ComboService.create_combo_order_items(
                        order=order,
                        combo=item_info['combo'],
                        quantity=item_info['quantity']
                    )
                else:
                    # Create regular order item
                    product = item_info['product']
                    variant = item_info['variant']
                    deal = item_info.get('deal')
                    pricing = item_info['pricing']
                    quantity = item_info['quantity']
                    promotion_data = item_info.get('promotion_data', {})
                    
                    product_obj = variant.product if variant else product
                    
                    order_item_kwargs = {
                        'order': order,
                        'product_name': product_obj.name,
                        'quantity': quantity,
                        'original_price': pricing['original_price'],
                        'price': pricing['final_price'],
                        'discount_percent': pricing['discount_percent']
                    }
                    
                    if variant:
                        order_item_kwargs['product_variant'] = variant
                        order_item_kwargs['variant_name'] = str(variant)
                    else:
                        order_item_kwargs['product'] = product
                    
                    if deal:
                        order_item_kwargs['deal'] = deal
                    
                    # Create order item first
                    order_item = OrderItem.objects.create(**order_item_kwargs)
                    
                    # Add promotion data if applicable (using many-to-many)
                    promotions_to_add = []
                    if promotion_data:
                        if promotion_data.get('free_gift_promo'):
                            promotions_to_add.append(promotion_data['free_gift_promo'])
                            order_item.free_gift_detail = promotion_data['free_gift_detail']
                        if promotion_data.get('free_shipping_promo'):
                            promotions_to_add.append(promotion_data['free_shipping_promo'])
                        
                        if promotions_to_add:
                            order_item.promotions.set(promotions_to_add)
                            order_item.save()
            
            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes='Order created',
                created_by=user
            )
            
            return order

from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from accounts.models import User

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
    """Serializer for displaying order items with product/variant details"""
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_variant', 'product_name', 'variant_name', 
            'quantity', 'price', 'subtotal', 'created_at'
        ]
        
        read_only_fields = ['subtotal', 'product_name', 'variant_name', 'created_at']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items. Supports both products and variants."""
    class Meta:
        model = OrderItem
        fields = ['product', 'product_variant', 'quantity']
    
    def validate(self, data):
        """Validate that either product or product_variant is provided, not both"""
        product = data.get('product')
        product_variant = data.get('product_variant')
        
        if not product and not product_variant:
            raise serializers.ValidationError(
                "Either 'product' or 'product_variant' must be provided."
            )
        
        if product and product_variant:
            raise serializers.ValidationError(
                "Provide either 'product' or 'product_variant', not both."
            )
        
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
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
            'total', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed order information including items and status history"""
    user = OrderUserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
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
    
    This serializer handles the creation of orders with items.
    It automatically:
    - Calculates subtotal from items
    - Applies 10% tax
    - Adds flat $10 shipping cost
    - Creates initial order status history
    - Associates order with authenticated user
    
    Request Example:
    {
        "items": [
            {
                "product": 1,
                "quantity": 2
            },
            {
                "product_variant": 5,
                "quantity": 1
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
        "notes": "Please deliver after 5pm"
    }
    """
    items = OrderItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'items', 'shipping_name', 'shipping_email', 'shipping_phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_zip', 'shipping_country',
            'billing_name', 'billing_address', 'billing_city',
            'billing_state', 'billing_zip', 'billing_country', 'notes'
        ]
    
    def create(self, validated_data):
        from decimal import Decimal
        from django.db import transaction
        
        items_data = validated_data.pop('items')
        user = validated_data.get('user')

        with transaction.atomic():
            # Calculate totals
            subtotal = Decimal('0.00')
            order_items = []
            
            for item_data in items_data:
                product = item_data.get('product')
                variant = item_data.get('product_variant')
                quantity = item_data['quantity']
                
                # Determine price based on product or variant
                if variant:
                    price = variant.price
                    product_obj = variant.product
                else:
                    price = product.base_price
                    product_obj = product
                
                item_subtotal = price * quantity
                subtotal += item_subtotal
                
                order_items.append({
                    'product': product,
                    'variant': variant,
                    'product_obj': product_obj,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': item_subtotal
                })
            
            # Calculate tax and total
            tax = subtotal * Decimal('0.10')  # 10% tax
            shipping_cost = Decimal('10.00')  # Flat shipping
            total = subtotal + tax + shipping_cost
            
            # Create order
            order = Order.objects.create(
                subtotal=subtotal,
                tax=tax,
                shipping_cost=shipping_cost,
                total=total,
                **validated_data
            )
            
            # Create order items
            for item in order_items:
                order_item_kwargs = {
                    'order': order,
                    'product_name': item['product_obj'].name,
                    'quantity': item['quantity'],
                    'price': item['price']
                }
                
                if item['variant']:
                    order_item_kwargs['product_variant'] = item['variant']
                    order_item_kwargs['variant_name'] = item['variant'].__str__()  # Use variant's __str__ method
                else:
                    order_item_kwargs['product'] = item['product']
                
                OrderItem.objects.create(**order_item_kwargs)
            
            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes='Order created',
                created_by=user
            )
            
            return order

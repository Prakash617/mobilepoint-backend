from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_variant', 'product_name', 'variant_name', 
            'sku', 'quantity', 'price', 'subtotal', 'created_at'
        ]
        read_only_fields = ['subtotal', 'product_name', 'variant_name', 'sku', 'created_at']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_variant', 'quantity']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'notes', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
            'total', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
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
                variant = item_data['product_variant']
                quantity = item_data['quantity']
                price = variant.price
                item_subtotal = price * quantity
                subtotal += item_subtotal
                
                order_items.append({
                    'variant': variant,
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
                OrderItem.objects.create(
                    order=order,
                    product_variant=item['variant'],
                    product_name=item['variant'].product.name,
                    variant_name=item['variant'].name,
                    sku=item['variant'].sku,
                    quantity=item['quantity'],
                    price=item['price']
                )
            
            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes='Order created',
                created_by=user
            )
            
            return order

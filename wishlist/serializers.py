from rest_framework import serializers
from .models import Wishlist, WishlistItem
from django.contrib.auth.models import User


class ProductVariantMinimalSerializer(serializers.Serializer):
    """Minimal serializer for product variant in wishlist"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    sku = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField()
    product_name = serializers.CharField(source='product.name')
    product_id = serializers.IntegerField(source='product.id')
    image = serializers.SerializerMethodField()
    
    def get_image(self, obj):
        # Assuming your ProductVariant has an image field or related images
        if hasattr(obj, 'image') and obj.image:
            return obj.image.url
        elif hasattr(obj, 'images') and obj.images.exists():
            return obj.images.first().image.url
        return None


class WishlistItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantMinimalSerializer(read_only=True)
    price_difference = serializers.SerializerMethodField()
    is_price_dropped = serializers.BooleanField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    current_price = serializers.DecimalField(
        source='product_variant.price', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = WishlistItem
        fields = [
            'id', 'product_variant', 'added_at', 'notes',
            'price_when_added', 'current_price', 'price_difference',
            'is_price_dropped', 'is_in_stock',
            'notify_on_price_drop', 'notify_on_stock'
        ]
        read_only_fields = ['added_at', 'price_when_added']
    
    def get_price_difference(self, obj):
        return float(obj.get_price_difference())


class WishlistItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['product_variant', 'notes', 'notify_on_price_drop', 'notify_on_stock']


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'items', 'items_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

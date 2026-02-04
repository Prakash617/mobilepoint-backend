from rest_framework import serializers
from django.utils import timezone
from .models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant,
    ProductImage, Deal, RecentlyViewedProduct,
    ProductCombo,
    ProductComboItem
)


class CategorySerializer(serializers.ModelSerializer):
    total_products = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    # picture = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
                'id',
                'name',
                'slug',
                'is_featured',
                'image',
                # 'picture',
               
                'description',
                'parent',
                'children',
                'is_active',
                'total_products',
            ]   
        

    
    def get_total_products(self, obj):
        """
        Count active products in this category and child categories
        """
        from django.db.models import Q
        
        return Product.objects.filter(
            is_active=True
        ).filter(
            Q(category=obj) | Q(category__parent=obj)
        ).filter(
            category__is_active=True
        ).distinct().count()
        
    def get_children(self, obj):
        # This returns the subcategories (Speaker, DSLR, etc.)
        children = obj.children.filter(is_active=True)[:4] # Limit to 4 for UI consistency
        return CategorySerializer(children, many=True, context=self.context).data

    # def get_picture(self, obj):
    #     if not obj.image:
    #         return None
    #     request = self.context.get('request')
    #     try:
    #         url = obj.image.url
    #     except ValueError:
    #         return None
    #     if request:
    #         return request.build_absolute_uri(url)
    #     return url

class BrandSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'is_featured', 'logo', 'description', 'is_active']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']
        
    

class VariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_display_name = serializers.CharField(source='attribute.display_name', read_only=True)
    
    class Meta:
        model = VariantAttributeValue
        fields = ['id', 'attribute_name', 'attribute_display_name', 'value', 'color_code', 'image']


# class ProductVariantAttributeValueSerializer(serializers.ModelSerializer):
#     attribute = serializers.CharField(source='attribute_value.attribute.name', read_only=True)
#     value = serializers.CharField(source='attribute_value.value', read_only=True)
#     color_code = serializers.CharField(source='attribute_value.color_code', read_only=True)
    
#     class Meta:
#         model = ProductVariantAttributeValue
#         fields = ['attribute', 'value', 'color_code']


class ProductVariantListSerializer(serializers.ModelSerializer):
    """Simplified variant serializer for product list"""
    variant_attributes = VariantAttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'price', 
            'stock_quantity','sold_quantity',  'is_in_stock', 'is_low_stock',
            'is_default', 'variant_attributes', 'images'
        ]


class ProductVariantDetailSerializer(serializers.ModelSerializer):
    """Detailed variant serializer"""
    variant_attributes = VariantAttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product_name', 'price',
            'stock_quantity','sold_quantity', 'low_stock_threshold', 'is_in_stock', 'is_low_stock',
            'is_active', 'is_default', 'variant_attributes', 'images', 
            'created_at', 'updated_at'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified product serializer for list view"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    default_variant = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    free_shipping = serializers.SerializerMethodField()
    free_gift = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    available_attributes = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug','short_description', 'description', 'category', 'brand',
            'base_price', 'is_active', 'is_featured', 
            'primary_image', 'default_variant', 'price_range',
            'free_shipping', 'free_gift', 'is_new', 'discount','available_attributes',
        ]
    
    def get_is_new(self, obj):
        return obj.is_new
    
    def get_available_attributes(self, obj):
        """
        Returns a dictionary of available attributes and their values
        for a given product.
        Example:
        {
            "Color": ["Red", "Blue"],
            "Storage": ["128GB", "256GB"]
        }
        """
        attributes = {}
        for variant in obj.variants.filter(is_active=True):
            for attr_val in variant.variant_attributes.all():
                attr_name = attr_val.attribute.name
                if attr_name not in attributes:
                    attributes[attr_name] = set()
                attributes[attr_name].add(attr_val.value)
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in attributes.items()}
    
    def get_discount(self, obj):
        """
        Returns discount info for the product:
        - Compare variant price with product base_price
        - Returns dict: {'amount': ..., 'percentage': ...} or None
        """
        variant = obj.variants.filter(is_default=True, is_active=True).first()
        if variant and obj.base_price and variant.price < obj.base_price:
            discount_amount = obj.base_price - variant.price
            discount_percentage = (discount_amount / obj.base_price) * 100
            return {
                'amount': float(discount_amount),
                'percentage': round(discount_percentage, 2)
            }
        return None
    
    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None
    
    def get_default_variant(self, obj):
        default = obj.variants.filter(is_default=True).first()
        if default:
            return ProductVariantListSerializer(default, context=self.context).data
        return None
    
    def get_price_range(self, obj):
        variants = obj.variants.filter(is_active=True)
        if variants.exists():
            prices = variants.values_list('price', flat=True)
            min_price = min(prices)
            max_price = max(prices)
            if min_price == max_price:
                return {'min': float(min_price), 'max': float(max_price), 'same': True}
            return {'min': float(min_price), 'max': float(max_price), 'same': False}
        return None
    
    def get_free_shipping(self, obj):
        now = timezone.now()
        return obj.promotions.filter(
            promotion_type='free_shipping',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).exists()
    
    def get_free_gift(self, obj):
        now = timezone.now()
        return obj.promotions.filter(
            promotion_type='free_gift',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).exists()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed product serializer"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantListSerializer(many=True, read_only=True)
    available_attributes = serializers.SerializerMethodField()
    free_shipping = serializers.SerializerMethodField()
    free_gift = serializers.SerializerMethodField()
    promotions = serializers.SerializerMethodField()  # <-- This is a method field
    deals = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug','short_description', 'description', 'category', 'brand',
            'base_price', 'specifications', 'meta_title', 'meta_description',
            'is_active', 'is_featured', 'images', 'variants', 
            'available_attributes', 'created_at', 'updated_at','free_shipping', 'free_gift','promotions',
            'deals'
        ]
    
    def get_available_attributes(self, obj):
        """Get all unique attributes available for this product's variants"""
        attributes = {}
        
        for variant in obj.variants.filter(is_active=True):
            for attr_value in variant.variant_attributes.all():
                attr_name = attr_value.attribute.name
                
                if attr_name not in attributes:
                    attributes[attr_name] = {
                        'name': attr_name,
                        'display_name': attr_value.attribute.display_name,
                        'values': []
                    }
                
                value_data = {
                    'id': attr_value.id,
                    'value': attr_value.value,
                    'color_code': attr_value.color_code,
                }
                
                # Add image URL if available
                if attr_value.image:
                    request = self.context.get('request')
                    if request:
                        value_data['image'] = request.build_absolute_uri(attr_value.image.url)
                    else:
                        value_data['image'] = attr_value.image.url
                
                # Avoid duplicates
                if value_data not in attributes[attr_name]['values']:
                    attributes[attr_name]['values'].append(value_data)
        
        return list(attributes.values())

    def get_free_shipping(self, obj):
        now = timezone.now()
        return obj.promotions.filter(
            promotion_type='free_shipping',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).exists()
    
    def get_free_gift(self, obj):
        now = timezone.now()
        return obj.promotions.filter(
            promotion_type='free_gift',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).exists()
    
    def get_deals(self, obj):
        """Get active deals for this product"""
        now = timezone.now()
        deals = obj.deals.filter(
            is_active=True,
            start_at__lte=now,
            end_at__gte=now
        )
        return DealListSerializer(deals, many=True, context=self.context).data
        
    def _get_promotion_info(self, obj, promotion_type):
        from django.utils.timezone import now
        from django.utils.timesince import timesince

        current_time = now()
        promo = (
            obj.promotions
            .filter(
                promotion_type=promotion_type,
                is_active=True,
                start_date__lte=current_time,
                end_date__gte=current_time
            )
            .order_by("end_date")
            .first()
        )
        if not promo:
            return None
        return {
            "title": promo.title,
            "description": promo.description,
            "expires_at": promo.end_date.strftime("%I:%M %p, %d/%m/%Y"),
        }

    # SerializerMethodField
    def get_promotions(self, obj):
        return {
            "free_shipping": self._get_promotion_info(obj, "free_shipping"),
            "free_gift": self._get_promotion_info(obj, "free_gift"),
        }
        

# ===== DEAL SERIALIZERS =====

class DealListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for deal lists"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    brand_name = serializers.CharField(source='product.brand.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    remaining_quantity = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'deal_type', 'product_name', 'product_slug',
            'brand_name', 'discount_percent', 'start_at', 'end_at',
            'is_active', 'is_featured', 'display_order', 'primary_image',
            'total_quantity', 'sold_quantity', 'remaining_quantity', 'progress_percentage'
        ]
    
    def get_primary_image(self, obj):
        image = obj.product.images.filter(is_primary=True).first()
        
        if image:
            return ProductImageSerializer(image, context=self.context).data
        return None


class DealDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single deal"""
    product = ProductDetailSerializer(read_only=True)
    remaining_quantity = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'deal_type', 'product',
            'discount_percent', 'start_at', 'end_at', 'is_active',
            'is_featured', 'display_order', 'views', 'purchases', 'free_shipping', 'free_gift_text',
            'total_quantity', 'sold_quantity', 'remaining_quantity', 'progress_percentage',
            'created_at', 'updated_at'
        ]


class DealCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating deals"""
    
    class Meta:
        model = Deal
        fields = [
            'product', 'title', 'deal_type',
            'discount_percent', 'total_quantity', 'sold_quantity',
            'start_at', 'end_at',
            'is_active', 'is_featured', 'display_order'
        ]
    
    def validate(self, data):
        if data.get('start_at') and data.get('end_at'):
            if data['start_at'] >= data['end_at']:
                raise serializers.ValidationError({
                    'end_at': 'End time must be after start time.'
                })
        
        if data.get('discount_percent'):
            if not (1 <= data['discount_percent'] <= 90):
                raise serializers.ValidationError({
                    'discount_percent': 'Discount must be between 1 and 90 percent.'
                })
        
        if data.get('sold_quantity') and data.get('total_quantity'):
            if data['sold_quantity'] > data['total_quantity']:
                raise serializers.ValidationError({
                    'sold_quantity': 'Sold quantity cannot exceed total quantity.'
                })
        
        return data


class RecentlyViewedProductSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = RecentlyViewedProduct
        fields = ['id', 'product', 'viewed_at']


# ===== PRODUCT COMBO SERIALIZERS =====

class ProductComboItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProductComboItem
        fields = ['id', 'product', 'product_id', 'quantity']


class ProductComboListSerializer(serializers.ModelSerializer):
    main_product = ProductListSerializer(read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCombo
        fields = [
            'id', 'name', 'slug', 'main_product', 'combo_regular_price', 'combo_selling_price',
            'is_active', 'is_featured', 'item_count'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()


class ProductComboDetailSerializer(serializers.ModelSerializer):
    main_product = ProductListSerializer(read_only=True)
    items = ProductComboItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductCombo
        fields = [
            'id', 'name', 'slug', 'main_product', 'description', 'combo_regular_price',
            'combo_selling_price', 'is_active', 'is_featured', 'items',
            'created_at', 'updated_at'
        ]


class ProductComboCreateUpdateSerializer(serializers.ModelSerializer):
    items = ProductComboItemSerializer(many=True, write_only=True, required=False)
    main_product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProductCombo
        fields = [
            'name', 'main_product_id', 'slug', 'description', 'combo_regular_price',
            'combo_selling_price', 'is_active', 'is_featured', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        combo = ProductCombo.objects.create(**validated_data)
        
        for item_data in items_data:
            ProductComboItem.objects.create(combo=combo, **item_data)
        
        return combo
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update combo fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                ProductComboItem.objects.create(combo=instance, **item_data)
        
        return instance
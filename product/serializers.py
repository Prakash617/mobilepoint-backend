from rest_framework import serializers
from django.utils import timezone
from .models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant, ProductVariantAttributeValue, ProductImage, Deal,RecentlyViewedProduct
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


class ProductVariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(source='attribute_value.attribute.name', read_only=True)
    value = serializers.CharField(source='attribute_value.value', read_only=True)
    color_code = serializers.CharField(source='attribute_value.color_code', read_only=True)
    
    class Meta:
        model = ProductVariantAttributeValue
        fields = ['attribute', 'value', 'color_code']


class ProductVariantListSerializer(serializers.ModelSerializer):
    """Simplified variant serializer for product list"""
    attributes = ProductVariantAttributeValueSerializer(source='attribute_values', many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'compare_at_price', 
            'stock_quantity','sold_quantity',  'is_in_stock', 'is_low_stock',
            'is_default', 'attributes', 'images'
        ]


class ProductVariantDetailSerializer(serializers.ModelSerializer):
    """Detailed variant serializer"""
    attributes = ProductVariantAttributeValueSerializer(source='attribute_values', many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product_name', 'sku', 'price', 'compare_at_price', 'cost_price',
            'stock_quantity','sold_quantity', 'low_stock_threshold', 'is_in_stock', 'is_low_stock',
            'is_active', 'is_default', 'attributes', 'images', 
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
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug','short_description', 'description', 'category', 'brand',
            'base_price', 'is_active', 'is_featured', 
            'primary_image', 'default_variant', 'price_range',
            'free_shipping', 'free_gift', 'is_new', 'discount'
        ]
    
    def get_is_new(self, obj):
        return obj.is_new
    
    def get_discount(self, obj):
        """
        Returns discount info for the product:
        - If default_variant.compare_at_price exists and is greater than price,
          calculate discount percentage and amount.
        - Returns dict: {'amount': ..., 'percentage': ...} or None
        """
        variant = obj.variants.filter(is_default=True, is_active=True).first()
        if variant and variant.compare_at_price and variant.compare_at_price > variant.price:
            discount_amount = variant.compare_at_price - variant.price
            discount_percentage = (discount_amount / variant.compare_at_price) * 100
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

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug','short_description', 'description', 'category', 'brand',
            'base_price', 'specifications', 'meta_title', 'meta_description',
            'is_active', 'is_featured', 'images', 'variants', 
            'available_attributes', 'created_at', 'updated_at','free_shipping', 'free_gift','promotions'
        ]
    
    def get_available_attributes(self, obj):
        """Get all unique attributes available for this product's variants"""
        attributes = {}
        
        for variant in obj.variants.filter(is_active=True):
            for attr_value in variant.attribute_values.all():
                attr_name = attr_value.attribute_value.attribute.name
                
                if attr_name not in attributes:
                    attributes[attr_name] = {
                        'name': attr_name,
                        'display_name': attr_value.attribute_value.attribute.display_name,
                        'values': []
                    }
                
                value_data = {
                    'id': attr_value.attribute_value.id,
                    'value': attr_value.attribute_value.value,
                    'color_code': attr_value.attribute_value.color_code,
                }
                
                # Add image URL if available
                if attr_value.attribute_value.image:
                    request = self.context.get('request')
                    if request:
                        value_data['image'] = request.build_absolute_uri(attr_value.attribute_value.image.url)
                    else:
                        value_data['image'] = attr_value.attribute_value.image.url
                
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
            "icon": promo.icon,
            "expires_at": promo.end_date,
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
    variant_info = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    all_images = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    specification = serializers.SerializerMethodField()
    time_remaining_hms = serializers.ReadOnlyField()  # no source needed

    
    
    class Meta:
        model = Deal
        fields = [
            'id', 'slug', 'title', 'deal_type', 'product_name', 
            'product_slug', 'brand_name', 'variant_info','specification',
            'original_price', 'discounted_price', 'discount_percentage',
            'remaining_quantity', 'progress_percentage', 'total_quantity',
            'free_shipping','free_gift', 'shipping_message', 'badge_text', 'badge_color',
            'primary_image','all_images', 'time_remaining', 'status',
            'is_featured', 'start_date', 'end_date','time_remaining_hms'
        ]
    
    def get_variant_info(self, obj):
        if obj.variant:
            attributes = obj.variant.attribute_values.all()
            return {
                'sku': obj.variant.sku,
                'attributes': [
                    {
                        'name': attr.attribute_value.attribute.name,
                        'value': attr.attribute_value.value
                    }
                    for attr in attributes
                ]
            }
        return None
    
    
    def get_specification(self, obj):
        return obj.product.specifications
    
    def get_primary_image(self, obj):
        # Get variant image if specific variant, otherwise product image
        if obj.variant:
            image = obj.variant.images.filter(is_primary=True).first()
        else:
            image = obj.product.images.filter(is_primary=True).first()
        
        if image:
            return ProductImageSerializer(image, context=self.context).data
        return None
    
    def get_all_images(self, obj):
        """
        Returns all images for the product or variant,
        placing the primary image first.
        """
        # Select the source: variant images if variant exists, else product images
        images_qs = obj.variant.images.all() if obj.variant else obj.product.images.all()

        # Order images: primary first
        images = sorted(
            images_qs,
            key=lambda x: not x.is_primary  # primary=True comes first
        )

        # Serialize all images
        return ProductImageSerializer(images, many=True, context=self.context).data
    
    def get_time_remaining(self, obj):
        return obj.time_remaining()
    
    def get_status(self, obj):
        if obj.is_sold_out:
            return 'sold_out'
        elif obj.is_expired:
            return 'expired'
        elif obj.is_upcoming:
            return 'upcoming'
        elif obj.is_live:
            return 'live'
        return 'inactive'


class DealDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single deal"""
    product = ProductDetailSerializer(read_only=True)
    variant = ProductVariantDetailSerializer(read_only=True)
    time_remaining = serializers.SerializerMethodField()
    time_until_start = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    all_images = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    available_variants = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'id', 'slug', 'title', 'deal_type', 'description',
            'terms_and_conditions', 'product', 'variant',
            'original_price', 'discounted_price', 'discount_percentage',
            'start_date', 'end_date', 'total_quantity', 'sold_quantity',
            'remaining_quantity', 'progress_percentage', 'max_quantity_per_order',
            'free_shipping', 'shipping_message', 'badge_text', 'badge_color',
            'highlight_features', 'display_order', 'is_active', 'is_featured',
            'view_count', 'click_count', 'time_remaining', 'time_until_start',
            'status', 'is_sold_out', 'is_live', 'is_expired', 'is_upcoming',
            'all_images', 'conversion_rate', 'available_variants',
            'created_at', 'updated_at'
        ]
    
    def get_time_remaining(self, obj):
        return obj.time_remaining()
    
    def get_time_until_start(self, obj):
        return obj.time_until_start()
    
    def get_status(self, obj):
        if obj.is_sold_out:
            return 'sold_out'
        elif obj.is_expired:
            return 'expired'
        elif obj.is_upcoming:
            return 'upcoming'
        elif obj.is_live:
            return 'live'
        return 'inactive'
    
    def get_all_images(self, obj):
        # Get all images for the deal (variant or product images)
        if obj.variant:
            images = obj.variant.images.all()
            if not images.exists():
                images = obj.product.images.all()
        else:
            images = obj.product.images.all()
        
        return ProductImageSerializer(images, many=True, context=self.context).data
    
    def get_conversion_rate(self, obj):
        return obj.get_conversion_rate()
    
    def get_available_variants(self, obj):
        """Get all variants this deal applies to"""
        variants = obj.get_applicable_variants()
        return ProductVariantSerializer(variants, many=True).data


class DealCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating deals"""
    
    class Meta:
        model = Deal
        fields = [
            'product', 'variant', 'title', 'deal_type', 'slug',
            'original_price', 'discounted_price', 'start_date', 'end_date',
            'total_quantity', 'max_quantity_per_order', 'free_shipping',
            'shipping_message', 'badge_text', 'badge_color',
            'highlight_features', 'description', 'terms_and_conditions',
            'display_order', 'is_active', 'is_featured'
        ]
    
    def validate(self, data):
        # Validate dates
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        
        # Validate prices
        if data.get('original_price') and data.get('discounted_price'):
            if data['discounted_price'] >= data['original_price']:
                raise serializers.ValidationError({
                    'discounted_price': 'Discounted price must be less than original price.'
                })
        
        # Validate quantity
        variant = data.get('variant')
        total_quantity = data.get('total_quantity')
        if variant and total_quantity:
            if total_quantity > variant.stock_quantity:
                raise serializers.ValidationError({
                    'total_quantity': f'Cannot exceed variant stock quantity ({variant.stock_quantity}).'
                })
        
        return data


class RecentlyViewedProductSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = RecentlyViewedProduct
        fields = ['id', 'product', 'viewed_at']

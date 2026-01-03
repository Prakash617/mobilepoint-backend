from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from django.utils import timezone
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import random
import string
from django.db.models import Avg, Count
from django.core.exceptions import ValidationError



class Category(models.Model):
    """Product categories like Smartphones, Laptops, etc."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = HTMLField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Category"
        ordering = ['name']

    def __str__(self):
        
        return self.name


class Brand(models.Model):
    """Electronics brands like Apple, Samsung, etc."""
    category = models.ManyToManyField(
        Category,
        related_name='brands',
        blank=True
    )    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = HTMLField(blank=True)
    is_featured = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brand"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Base product without variants"""
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = HTMLField()
    short_description = HTMLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # Base price (optional, can be overridden by variants)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Product specifications
    specifications = HTMLField(blank=True, null=True)  # e.g., {"processor": "Snapdragon 888", "screen": "6.5 inch"}
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    

    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.0
    )
    review_count = models.PositiveIntegerField(default=0)

    def update_rating(self):
        agg = self.reviews.filter(is_approved=True).aggregate(
            average=Avg('rating'),
            count=Count('id')
        )
        self.average_rating = agg['average'] or 0.0
        self.review_count = agg['count'] or 0
        self.save(update_fields=['average_rating', 'review_count'])

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Product"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    @property
    def is_new(self):
        """Returns True if the product was created within the last 3 days"""
        return timezone.now() <= self.created_at + timedelta(days=14)


class VariantAttribute(models.Model):
    """Variant attribute types like Color, Memory, Storage, etc."""
    name = models.CharField(max_length=100, unique=True)  # e.g., "Color", "Memory", "Storage"
    display_name = models.CharField(max_length=100)  # e.g., "Choose Color"
    
    class Meta:
        verbose_name = "Variant "
        verbose_name_plural = "Variant"
        ordering = ['name']

    def __str__(self):
        return self.name


class VariantAttributeValue(models.Model):
    TYPE_CHOICES = [
        ("text", "Text"),
        ("color", "Color"),
        ("image", "Image"),
    ]
    """Values for variant attributes like Red, Blue, 8GB, 16GB, etc."""
    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, related_name='values')
    types = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="text"
    )
    value = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Red", "8GB", "256GB"
    
    # Optional: for color swatches or icons
    color_code = models.CharField(
        max_length=7, 
        blank=True, 
        null=True,
        help_text="Enter color code in hex format (e.g., #FF0000)"
    )  # e.g., "#FF0000" for red
    image = models.ImageField(upload_to='variant_images/', blank=True, null=True)
    
    class Meta:
        verbose_name = " Attribute"
        verbose_name_plural = " Attribute"
        unique_together = ('attribute', 'value')
        ordering = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value or self.color_code or self.image}"

    def clean(self):
        super().clean()
        if self.types == 'text':
            if not self.value:
                raise ValidationError({'value': 'This field is required when type is "Text".'})
            self.color_code = None
            self.image = None
        elif self.types == 'color':
            if not self.color_code:
                raise ValidationError({'color_code': 'This field is required when type is "Color".'})
            self.value = None
            self.image = None
        elif self.types == 'image':
            if not self.image:
                raise ValidationError({'image': 'This field is required when type is "Image".'})
            self.value = None
            self.color_code = None

class ProductVariant(models.Model):
    """Actual product variants with specific attribute combinations"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True , blank=True)
    
    # Pricing
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Original price for discounts
    # cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    sold_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    
    # Variant specific fields
    # weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # in kg
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # Default variant to show
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variant"
        ordering = ['product', '-is_default', 'selling_price']

    def __str__(self):
        attributes = ", ".join([f"{va.attribute.name}: {va.value}" for va in self.attribute_values.all()])
        return f"{self.product.name} - {attributes}"

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    def generate_sku(self):
        """
        Generate a unique SKU.
        If variant attributes are available, it creates a descriptive SKU.
        e.g., 'BRAND-PRODUCT-ATTR1-ATTR2'
        Otherwise, it falls back to a random SKU.
        """
        # --- Descriptive SKU part ---
        # This part works if the variant has been saved and has attributes.
        if self.pk and self.attribute_values.exists():
            parts = []
            if self.product.brand:
                # Use a short, uppercase code for the brand
                brand_part = slugify(self.product.brand.name).upper().replace('-', '')[:4]
                parts.append(brand_part)

            # Use a short, uppercase code for the product name
            product_part = slugify(self.product.name).upper().replace('-', '')[:10]
            parts.append(product_part)

            # Add attribute values, ordered by attribute name for consistency
            attributes = self.attribute_values.order_by('attribute_value__attribute__name')
            attr_parts = [slugify(attr.attribute_value.value).upper() for attr in attributes]
            parts.extend(attr_parts)

            base_sku = "-".join(parts)
            sku = base_sku

            # Ensure SKU is unique by appending a counter if needed
            counter = 1
            while ProductVariant.objects.filter(sku=sku).exclude(pk=self.pk).exists():
                sku = f"{base_sku}-{counter}"
                counter += 1
            return sku

        # --- Fallback to random SKU ---
        # This is used if attributes are not yet set (e.g. on initial creation).
        base = slugify(self.product.name)[:10]
        while True:
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            sku = f"{base}-{random_suffix}"
            if not ProductVariant.objects.filter(sku=sku).exists():
                return sku

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided or to update based on attributes
        self.sku = self.generate_sku()
        # Ensure only one default variant per product
        if self.is_default:
            ProductVariant.objects.filter(product=self.product, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ProductVariantAttributeValue(models.Model):
    """Links variants to their attribute values (Many-to-Many relationship)"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='attribute_values')
    attribute_value = models.ForeignKey(VariantAttributeValue, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Variant Attribute Mapping"
        verbose_name_plural = "Variant Attribute Mapping"
        unique_together = ('variant', 'attribute_value')

    def __str__(self):
        return f"{self.variant.sku} - {self.attribute_value}"

    @property
    def attribute(self):
        return self.attribute_value.attribute

    @property
    def value(self):
        return self.attribute_value.value


class ProductImage(models.Model):
    """Product images - can be linked to specific variants or to the product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Image"
        ordering = ['order', 'created_at']

    def __str__(self):
        if self.product:
            return f"Image for {self.product.name}"
        return "Image (no product)"

    def save(self, *args, **kwargs):
        # If the image is associated with a variant,
        # ensure the product field is also set.
        # This prevents errors in the admin when an image is added to a variant
        # but the product is not explicitly set.
        if self.variant:
            self.product = self.variant.product

        # Only one primary per product
        if self.is_primary and self.product:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)
        
        
class ProductPromotion(models.Model):
    """Promotions like Free Shipping, Free Gift, etc."""
    PROMOTION_TYPE = [
        ('free_shipping', 'Free Shipping'),
        ('free_gift', 'Free Gift'),
        # ('discount', 'Discount'),
        # ('cashback', 'Cashback'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='promotions')
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPE)
    title = models.CharField(max_length=100)
    description = HTMLField(blank=True)
    # icon = models.CharField(max_length=50, blank=True)  # Icon class or emoji
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.title}"
    
    class Meta:
        verbose_name = "Product Promotion"
        verbose_name_plural = "Product Promotions"
    
    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
class FrequentlyBoughtTogether(models.Model):
    """Products frequently bought together"""
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bought_together_main')
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bought_together_related')
    display_order = models.PositiveIntegerField(default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Frequently Bought Together"
        verbose_name_plural = "Frequently Bought Together"
        unique_together = ['main_product', 'related_product']
        ordering = ['display_order']

    def __str__(self):
        return f"{self.main_product.name} + {self.related_product.name}"
    
    @property
    def total_price(self):
        """Calculate total price with discount"""
        pass

    
# class ProductComparison(models.Model):
#     """Products added for comparison"""
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comparisons')
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     added_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = "Product Comparison"
#         verbose_name_plural = "Product Comparisons"
#         unique_together = ['user', 'product']
#         ordering = ['added_at']

#     def __str__(self):
#         return f"{self.user.username} - {self.product.name}"
    


class Deal(models.Model):
    """
    Deal/Promotion Model - can be linked to entire product or specific variants
    Supports Deal of the Day, Flash Sales, etc.
    """
    DEAL_TYPE_CHOICES = [
        ('deal_of_day', 'Deal of the Day'),
        ('flash_sale', 'Flash Sale'),
        ('clearance', 'Clearance'),
        ('seasonal', 'Seasonal Sale'),
        ('bundle', 'Bundle Deal'),
        ('limited_time', 'Limited Time Offer'),
    ]

    # Product relationship
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='deals'
    )
    
    # Optional: specific variant (if deal is for specific variant only)
    # If null, deal applies to all variants
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='deals',
        null=True,
        blank=True,
        help_text="Leave blank if deal applies to all variants"
    )
    
    # Deal information
    title = models.CharField(max_length=255)
    deal_type = models.CharField(max_length=50, choices=DEAL_TYPE_CHOICES)
    slug = models.SlugField(max_length=300, unique=True)
    
    # Pricing
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        editable=False
    )
    
    # Deal duration
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Inventory allocation for the deal
    total_quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total units allocated for this deal"
    )
    sold_quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    max_quantity_per_order = models.PositiveIntegerField(
        default=5,
        help_text="Maximum quantity per order"
    )
    
    # Shipping
    free_shipping = models.BooleanField(default=False)
    shipping_message = models.CharField(max_length=100, blank=True)
    
    # fire gift
    free_gift = models.BooleanField(default=False)
    gift_message = models.CharField(max_length=100, blank=True)
    
    # Display settings
    badge_text = models.CharField(max_length=50, blank=True)  # e.g., "HOT DEAL", "80% OFF"
    badge_color = models.CharField(max_length=7, default='#FF0000')  # Hex color
    
    # Highlighted features to display (JSON array)
    highlight_features = models.JSONField(
        default=list, 
        blank=True,
        help_text="Featured specs to display. E.g., [{'label': 'Display', 'value': '6.67 inches'}]"
    )
    
    # Deal description/terms
    description = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # Priority and visibility
    display_order = models.IntegerField(default=0)  # For sorting deals
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # Show on homepage
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0, editable=False)
    click_count = models.PositiveIntegerField(default=0, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Deal"
        verbose_name_plural = "Deal"
        db_table = 'deals'
        ordering = ['-is_featured', 'display_order', '-created_at']
        indexes = [
            models.Index(fields=['deal_type', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['product', 'variant']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        # Auto-calculate discount percentage
        if self.original_price and self.discounted_price:
            discount = ((self.original_price - self.discounted_price) / self.original_price) * 100
            self.discount_percentage = round(discount)
        
        # Auto-populate prices from variant if not set
        if self.variant and not self.original_price:
            self.original_price = self.variant.compare_at_price or self.variant.price
        if self.variant and not self.discounted_price:
            self.discounted_price = self.variant.price
            
        super().save(*args, **kwargs)

    def __str__(self):
        variant_info = f" - {self.variant}" if self.variant else ""
        return f"{self.get_deal_type_display()}: {self.product.name}{variant_info}"

    # Quantity properties
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity"""
        return max(0, self.total_quantity - self.sold_quantity)
    
    @property
    def time_remaining_hms(self):
        """Return time remaining as H:M:S"""
        now = timezone.now()
        if self.end_date <= now:
            return "00:00:00"  # expired
        
        diff = self.end_date - now
        total_seconds = int(diff.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def progress_percentage(self):
        """Calculate sold progress as percentage"""
        if self.total_quantity == 0:
            return 0
        return round((self.sold_quantity / self.total_quantity) * 100, 2)

    @property
    def is_sold_out(self):
        """Check if deal is sold out"""
        return self.sold_quantity >= self.total_quantity

    # Time properties
    @property
    def is_expired(self):
        """Check if deal has expired"""
        return timezone.now() > self.end_date

    @property
    def is_upcoming(self):
        """Check if deal hasn't started yet"""
        return timezone.now() < self.start_date

    @property
    def is_live(self):
        """Check if deal is currently active and available"""
        now = timezone.now()
        return (
            self.start_date <= now <= self.end_date 
            and self.is_active 
            and not self.is_sold_out
        )

    def time_remaining(self):
        """Get time remaining until deal expires"""
        if self.is_expired:
            return {'expired': True, 'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0}
        
        now = timezone.now()
        diff = self.end_date - now
        
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        seconds = diff.seconds % 60
        
        return {
            'expired': False,
            'days': diff.days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds
        }

    def time_until_start(self):
        """Get time until deal starts (for upcoming deals)"""
        if not self.is_upcoming:
            return None
        
        now = timezone.now()
        diff = self.start_date - now
        
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        return {
            'days': diff.days,
            'hours': hours,
            'minutes': minutes
        }

    # Action methods
    def increment_sold(self, quantity=1):
        """
        Increment sold quantity and update variant stock
        Returns True if successful, False if quantity not available
        """
        if self.sold_quantity + quantity > self.total_quantity:
            return False
        
        # Update deal sold quantity
        self.sold_quantity += quantity
        self.save(update_fields=['sold_quantity', 'updated_at'])
        
        # Update variant stock if specific variant
        if self.variant and self.variant.stock_quantity >= quantity:
            self.variant.stock_quantity -= quantity
            self.variant.sold_quantity += quantity
            self.variant.save(update_fields=['stock_quantity', 'updated_at'])
        
        return True

    def increment_view(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_click(self):
        """Increment click count"""
        self.click_count += 1
        self.save(update_fields=['click_count'])

    # Helper methods
    def get_display_specs(self):
        """Get highlighted specifications for display"""
        if self.highlight_features:
            return self.highlight_features
        
        # Default specs from product
        specs = []
        product_specs = self.product.specifications
        
        # Common specs to highlight
        priority_keys = ['display', 'processor', 'ram', 'storage', 'camera', 'battery']
        
        for key in priority_keys:
            if key in product_specs:
                specs.append({
                    'label': key.title(),
                    'value': product_specs[key]
                })
        
        return specs

    def get_applicable_variants(self):
        """Get all variants this deal applies to"""
        if self.variant:
            return [self.variant]
        return self.product.variants.filter(is_active=True)

    def get_conversion_rate(self):
        """Calculate conversion rate (clicks to sales)"""
        if self.click_count == 0:
            return 0
        return round((self.sold_quantity / self.click_count) * 100, 2)
    
    
class RecentlyViewedProduct(models.Model):
    """
    Tracks recently viewed products per user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='viewed_by')
    viewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Recently Viewed Product"
        verbose_name_plural = "Recently Viewed Product"
        ordering = ['-viewed_at']
        unique_together = ('user', 'product')  # ensures one entry per user-product

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"
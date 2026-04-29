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
from filehub.fields import ImagePickerField



class Category(models.Model):
    """Product categories like Smartphones, Laptops, etc."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = HTMLField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    image = ImagePickerField(upload_to='categories/', blank=True, null=True)
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
    
    
from filehub.fields import ImagePickerField

class Brand(models.Model):
    """Electronics brands like Apple, Samsung, etc."""
    category = models.ManyToManyField(
        Category,
        related_name='brands',
        blank=True
    )    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    logo = ImagePickerField(blank=True, null=True)
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
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products',
        default=1  # ID of a valid brand
    )    
    # Base price (optional, can be overridden by variants)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Product specifications
    specifications = HTMLField(blank=True, null=True)  # e.g., {"processor": "Snapdragon 888", "screen": "6.5 inch"}
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    

    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    sold_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    
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
    
    def clean(self):
        if self.brand and self.category:
            if not self.brand.category.filter(id=self.category_id).exists():
                raise ValidationError(
                    {"brand": "Selected brand does not belong to the selected category."}
            )


    def save(self, *args, **kwargs):
        self.full_clean()
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
            self.image = None
        elif self.types == 'image':
            if not self.image:
                raise ValidationError({'image': 'This field is required when type is "Image".'})
            self.color_code = None

class ProductVariant(models.Model):
    """Actual product variants with specific attribute combinations"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    # sku = models.CharField(max_length=100, unique=True , blank=True)
    variant_attributes = models.ManyToManyField(VariantAttributeValue, related_name="product_variants")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Original price for discounts
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
        ordering = ['product', '-is_default', 'price']

    def __str__(self):
        attributes = ", ".join([f"{va.attribute.name}: {va.value}" for va in self.variant_attributes.all()])
        return f"{self.product.name} - {attributes}"

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    # def generate_sku(self):
    #     """
    #     Generate a unique SKU.
    #     If variant attributes are available, it creates a descriptive SKU.
    #     e.g., 'BRAND-PRODUCT-ATTR1-ATTR2'
    #     Otherwise, it falls back to a random SKU.
    #     """
    #     # --- Descriptive SKU part ---
    #     # This part works if the variant has been saved and has attributes.
    #     if self.pk and self.attribute_values.exists():
    #         parts = []
    #         if self.product.brand:
    #             # Use a short, uppercase code for the brand
    #             brand_part = slugify(self.product.brand.name).upper().replace('-', '')[:4]
    #             parts.append(brand_part)

    #         # Use a short, uppercase code for the product name
    #         product_part = slugify(self.product.name).upper().replace('-', '')[:10]
    #         parts.append(product_part)

    #         # Add attribute values, ordered by attribute name for consistency
    #         attributes = self.attribute_values.order_by('attribute_value__attribute__name')
    #         attr_parts = [slugify(attr.attribute_value.value).upper() for attr in attributes]
    #         parts.extend(attr_parts)

    #         base_sku = "-".join(parts)
    #         sku = base_sku

    #         # Ensure SKU is unique by appending a counter if needed
    #         counter = 1
    #         while ProductVariant.objects.filter(sku=sku).exclude(pk=self.pk).exists():
    #             sku = f"{base_sku}-{counter}"
    #             counter += 1
    #         return sku

    #     # --- Fallback to random SKU ---
    #     # This is used if attributes are not yet set (e.g. on initial creation).
    #     base = slugify(self.product.name)[:10]
    #     while True:
    #         random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    #         sku = f"{base}-{random_suffix}"
    #         if not ProductVariant.objects.filter(sku=sku).exists():
    #             return sku

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided or to update based on attributes
        # self.sku = self.generate_sku()
        # Ensure only one default variant per product
        is_new = self.pk is None
        

        # If this is the FIRST variant of the product → make it default
        if is_new and not ProductVariant.objects.filter(product=self.product).exists():
            self.is_default = True

        super().save(*args, **kwargs)
        # Ensure only one default variant per product
        if self.is_default:
            ProductVariant.objects.filter(
                product=self.product,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)



# class ProductVariantAttributeValue(models.Model):
#     """Links variants to their attribute values (Many-to-Many relationship)"""
#     variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='attribute_values')
#     attribute_value = models.ForeignKey(VariantAttributeValue, on_delete=models.CASCADE)

#     class Meta:
#         verbose_name = "Variant Attribute Mapping"
#         verbose_name_plural = "Variant Attribute Mapping"
#         unique_together = ('variant', 'attribute_value')

#     def __str__(self):
#         return f"{self.variant.sku} - {self.attribute_value}"

#     @property
#     def attribute(self):
#         return self.attribute_value.attribute

#     @property
#     def value(self):
#         return self.attribute_value.value


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

        # Ensure there is always one primary image per product.
        if self.product and not self.is_primary:
            has_other_primary = ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).exists()
            if not has_other_primary:
                self.is_primary = True

        # Only one primary per product
        if self.is_primary and self.product:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)
        
        
class Promotion(models.Model):
    """Main promotion model (Free Shipping, Free Gift, etc.)"""

    class PromotionType(models.TextChoices):
        FREE_SHIPPING = "free_shipping", "Free Shipping"
        FREE_GIFT = "free_gift", "Free Gift"

    promotion_type = models.CharField(
        max_length=20,
        choices=PromotionType.choices,
        db_index=True
    )

    title = models.CharField(max_length=150)
    description = HTMLField(
        blank=True, 
        null=True, 
        help_text="Only fill for free_gift promotion type" 
        
    )

    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    products = models.ManyToManyField(
        "Product",
        related_name="promotions",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["is_active", "start_date", "end_date"]),
        ]
        verbose_name = "Promotion"
        verbose_name_plural = "Promotion"
    def __str__(self):
        return self.title

    # ✅ Validation: prevent wrong dates
    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError("End date must be after start date.")

    # ✅ Safe active check
    @property
    def is_currently_active(self):
        now = timezone.now()
        return (
            self.is_active
            and self.start_date <= now
            and self.end_date >= now
        )

    # ✅ Reusable queryset helper
    @classmethod
    def active(cls):
        now = timezone.now()
        return cls.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
    

class ProductCombo(models.Model):
    """Product combo/bundle"""
    
    name = models.CharField(max_length=300)
    main_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="combos",
    )
    slug = models.SlugField(max_length=300, unique=True)
    description = HTMLField(blank=True, null=True)
    combo_regular_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    combo_selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Combo"
        verbose_name_plural = "Product Combo"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductComboItem(models.Model):
    """Items in a product combo"""
    combo = models.ForeignKey(
        ProductCombo,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ["combo", "product"]

    def __str__(self):
        return f"{self.combo.name} → {self.product.name}"


class Deal(models.Model):
    """Deal model combining Deal, DealStat, and DealExtra functionality"""
    DEAL_TYPE_CHOICES = [
        ("flash", "Flash Sale"),
        ("daily", "Deal of the Day"),
        ("seasonal", "Seasonal Sale"),
        # ("clearance", "Clearance"),
    ]

    # ========== Core Deal Fields ==========
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="deals"
    )

    title = models.CharField(max_length=200)
    deal_type = models.CharField(max_length=20, choices=DEAL_TYPE_CHOICES)

    discount_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="Percentage discount"
    )

    total_quantity = models.PositiveIntegerField(default=0, help_text="Total quantity available for this deal")
    sold_quantity = models.PositiveIntegerField(default=0, help_text="Quantity sold so far")

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    display_order = models.PositiveIntegerField(default=0)

    # ========== DealStat Fields (Statistics) ==========
    views = models.PositiveIntegerField(default=0, help_text="Number of views for this deal")
    purchases = models.PositiveIntegerField(default=0, help_text="Number of purchases made")

    # ========== DealExtra Fields (Additional Options) ==========
    free_shipping = models.BooleanField(default=False, help_text="Free shipping for this deal")
    free_gift_text = models.CharField(max_length=100, blank=True, help_text="Free gift description")

    # ========== Timestamps ==========
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Deal"
        verbose_name_plural = "Deal"
        ordering = ['-is_featured', 'display_order', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.product.name}"
    
    @property
    def remaining_quantity(self):
        """Get remaining quantity available for purchase"""
        return max(0, self.total_quantity - self.sold_quantity)
    
    @property
    def progress_percentage(self):
        """Get progress percentage of items sold"""
        if self.total_quantity == 0:
            return 0
        return int((self.sold_quantity / self.total_quantity) * 100)
    
    def increment_sold(self, quantity=1):
        """Increment sold quantity"""
        if self.sold_quantity + quantity <= self.total_quantity:
            self.sold_quantity += quantity
            self.save(update_fields=['sold_quantity'])
            return True
        return False
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def increment_purchases(self, quantity=1):
        """Increment purchase count"""
        self.purchases += quantity
        self.save(update_fields=['purchases'])
    
    
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
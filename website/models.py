# website/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from product.models import Product, Category


class Carousel(models.Model):
    POSITION_CHOICES = [
        ('home_main', 'Home Main Carousel'),
        ('home_secondary', 'Home Secondary Carousel'),
        ('category', 'Category Page Carousel'),
        ('product', 'Product Page Carousel'),
    ]
    
    title = models.CharField(max_length=200)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, default='home_main')
    is_active = models.BooleanField(default=True)
    auto_play = models.BooleanField(default=True)
    auto_play_speed = models.IntegerField(default=3000, help_text='Milliseconds')
    show_indicators = models.BooleanField(default=True)
    show_arrows = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['position', 'is_active']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_position_display()}"


class CarouselSlide(models.Model):
    carousel = models.ForeignKey(Carousel, on_delete=models.CASCADE, related_name='slides')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='carousel/slides/')
    mobile_image = models.ImageField(upload_to='carousel/slides/mobile/', blank=True, null=True)
    
    # Link
    link_url = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, blank=True, null=True)
    open_in_new_tab = models.BooleanField(default=False)
    
    # Product relation (optional)
    product = models.ForeignKey('product.Product', on_delete=models.SET_NULL, blank=True, null=True)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.carousel.title} - {self.title}"


class Advertisement(models.Model):
    AD_TYPE_CHOICES = [
        ('banner', 'Banner'),
        ('photo', 'Photo Ad'),
        ('sidebar', 'Sidebar'),
        ('popup', 'Popup'),
        ('inline', 'Inline Content'),
        ('video', 'Video Ad'),
    ]
    
    POSITION_CHOICES = [
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('sidebar_left', 'Sidebar Left'),
        ('sidebar_right', 'Sidebar Right'),
        ('home_top', 'Home Top'),
        ('home_middle', 'Home Middle'),
        ('home_bottom', 'Home Bottom'),
        ('category_top', 'Category Top'),
        ('product_sidebar', 'Product Sidebar'),
        ('checkout', 'Checkout Page'),
    ]
    
    title = models.CharField(max_length=200)
    ad_type = models.CharField(max_length=20, choices=AD_TYPE_CHOICES, default='banner')
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    
    # Media
    image = models.ImageField(upload_to='ads/', blank=True, null=True)
    mobile_image = models.ImageField(upload_to='ads/mobile/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    html_content = models.TextField(blank=True, null=True, help_text='Custom HTML/JS code')
    
    # Link
    link_url = models.URLField(blank=True, null=True)
    open_in_new_tab = models.BooleanField(default=True)
    
    # Display settings
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    
    # Targeting
    show_on_mobile = models.BooleanField(default=True)
    show_on_desktop = models.BooleanField(default=True)
    max_impressions = models.IntegerField(blank=True, null=True)
    current_impressions = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['position', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_position_display()}"
    
    def is_valid(self):
        """Check if ad should be displayed"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        if self.max_impressions and self.current_impressions >= self.max_impressions:
            return False
        return True
    
    def increment_impression(self):
        self.current_impressions += 1
        self.save(update_fields=['current_impressions'])
    
    def increment_click(self):
        self.click_count += 1
        self.save(update_fields=['click_count'])


class Banner(models.Model):
    BANNER_TYPE_CHOICES = [
        ('promotional', 'Promotional'),
        ('seasonal', 'Seasonal'),
        ('announcement', 'Announcement'),
        ('featured', 'Featured Product'),
    ]
    
    POSITION_CHOICES = [
        ('top', 'Top Banner'),
        ('middle', 'Middle Banner'),
        ('bottom', 'Bottom Banner'),
    ]
    
    title = models.CharField(max_length=200)
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPE_CHOICES, default='promotional')
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='top')
    
    # Content
    heading = models.CharField(max_length=200)
    subheading = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(upload_to='banners/mobile/', blank=True, null=True)
    background_color = models.CharField(max_length=7, default='#ffffff', help_text='Hex color code')
    text_color = models.CharField(max_length=7, default='#000000', help_text='Hex color code')
    
    # CTA Button
    button_text = models.CharField(max_length=100, blank=True, null=True)
    button_link = models.URLField(blank=True, null=True)
    button_color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    
    # Display settings
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True, null=True)
    customer_image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    designation = models.CharField(max_length=200, blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Product relation (optional)
    product = models.ForeignKey('product.Product', on_delete=models.SET_NULL, blank=True, null=True)
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.title}"


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('shipping', 'Shipping'),
        ('payment', 'Payment'),
        ('returns', 'Returns & Refunds'),
        ('products', 'Products'),
        ('account', 'Account'),
        ('technical', 'Technical Support'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
    
    def __str__(self):
        return self.question


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    replied = models.BooleanField(default=False)
    reply_message = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class SiteSettings(models.Model):
    # Company Info
    site_name = models.CharField(max_length=200, default='My Store')
    site_tagline = models.CharField(max_length=300, blank=True, null=True)
    site_description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    
    # Contact Info
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    
    # Settings
    maintenance_mode = models.BooleanField(default=False)
    allow_guest_checkout = models.BooleanField(default=True)
    show_stock_quantity = models.BooleanField(default=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError('Only one SiteSettings instance allowed')
        return super().save(*args, **kwargs)



class CuratedItem(models.Model):
    """Homepage 'Curated For You' section items"""
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    subtitle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Small description under title"
    )

    image = models.ImageField(
        upload_to="curated/",
        help_text="Main card image"
    )

    # badge_text = models.CharField(
    #     max_length=50,
    #     blank=True,
    #     help_text="Example: SALE, 50% OFF"
    # )

    # badge_color = models.CharField(
    #     max_length=20,
    #     default="green",
    #     help_text="CSS color or Tailwind class"
    # )

    button_text = models.CharField(
        max_length=50,
        default="Shop Now"
    )

    link_url = models.CharField(
    max_length=255,
    blank=True,
    help_text="Frontend route (e.g. /products/ipad-mini-6/)"
)

    position = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower comes first)"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created_at"]
        verbose_name = "Curated Item"
        verbose_name_plural = "Curated Items"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.product:
            self.link_url = f"/products/{self.product.slug}/"
        elif self.category:
            self.link_url = f"/category/{self.category.slug}/"
        super().save(*args, **kwargs)
        
    # ------------------------
    # Validation
    # ------------------------
    def clean(self):
        if self.product and self.category:
            raise ValidationError(
                "Select either a Product or a Category, not both."
            )
            
    def get_absolute_url(self):
        return reverse("product:products", kwargs={"slug": self.slug})
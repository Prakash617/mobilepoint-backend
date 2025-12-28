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
        verbose_name = "Carousel"
        verbose_name_plural = "Carousels"

    def __str__(self):
        return f"{self.title} - {self.get_position_display()}"


class CarouselSlide(models.Model):
    carousel = models.ForeignKey(Carousel, on_delete=models.CASCADE, related_name='slides')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='carousel/slides/')
    mobile_image = models.ImageField(upload_to='carousel/slides/mobile/', blank=True, null=True)

    link_url = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, blank=True, null=True)
    open_in_new_tab = models.BooleanField(default=False)

    product = models.ForeignKey('product.Product', on_delete=models.SET_NULL, blank=True, null=True)

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Carousel Slide"
        verbose_name_plural = "Carousel Slides"

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

    image = models.ImageField(upload_to='ads/', blank=True, null=True)
    mobile_image = models.ImageField(upload_to='ads/mobile/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    html_content = models.TextField(blank=True, null=True, help_text='Custom HTML/JS code')

    link_url = models.URLField(blank=True, null=True)
    open_in_new_tab = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)

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
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"

    def __str__(self):
        return f"{self.title} - {self.get_position_display()}"

    def is_valid(self):
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


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

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
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} - {self.subject}"


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default='My Store')
    site_tagline = models.CharField(max_length=300, blank=True, null=True)
    site_description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    maintenance_mode = models.BooleanField(default=False)
    allow_guest_checkout = models.BooleanField(default=True)
    show_stock_quantity = models.BooleanField(default=True)

    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name


class CuratedItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, help_text="Small description under title")
    image = models.ImageField(upload_to="curated/", help_text="Main card image")
    button_text = models.CharField(max_length=50, default="Shop Now")
    link_url = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "-created_at"]
        verbose_name = "Curated Item"
        verbose_name_plural = "Curated Items"

    def __str__(self):
        return self.title

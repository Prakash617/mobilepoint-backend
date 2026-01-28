from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from tinymce.models import HTMLField

class Menu(models.Model):
    """Menu management"""
    MENU_LOCATION_CHOICES = [
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('sidebar', 'Sidebar'),
    ]
    
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=20, choices=MENU_LOCATION_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menus'
        verbose_name = 'Menu'
        verbose_name_plural = 'Menu'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.location})"


class MenuItem(models.Model):
    """Menu items with multi-level support"""
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    label_en = models.CharField(max_length=100)
    label_np = models.CharField(max_length=100, blank=True, null=True)
    page = models.ForeignKey(
        'menu.page',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Select a page OR enter a custom URL"
    )
    url = models.CharField(max_length=255,help_text="Auto fill page url OR enter a custom URL", blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    sub_title = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, null=True)
    is_external = models.BooleanField(
        default=False, 
        help_text="Check if this item is an external link"
    ) #for external links
    open_new_tab = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'menu_items'
        ordering = ['order']
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Item'
        
    def save(self, *args, **kwargs):
        # Auto-fill URL from Page
        if self.page:
            self.url = self.page.get_full_url()
            self.is_external = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label_en



class Page(models.Model):
    """Model for creating dynamic pages in Django"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    # Basic Information
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    # Content
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="SEO meta description"
    )
    content = HTMLField(blank=True, null=True, help_text="Main page content (HTML allowed)")
    excerpt = HTMLField(blank=True, null=True, max_length=300, help_text="Short summary of the page")
    
    featured_image = models.ImageField(upload_to='pages/', blank=True, null=True)
    
    # SEO
    seo_title = models.CharField(
        max_length=70, blank=True, help_text="Custom title for search engines"
    )
    keywords = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated keywords"
    )
    
    # Author and Timestamps
    # author = models.ForeignKey(User, on_delete=models.SET_NULL, 
    #                           null=True, related_name='pages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Page'
        verbose_name_plural = 'Page'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set SEO title to title if not provided
        if not self.seo_title:
            self.seo_title = self.title
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this page"""
        return reverse('page-detail', kwargs={'slug': self.slug})
    
    def get_full_url(self):
        return f"{settings.SITE_URL}{self.get_absolute_url()}"
    
    @property
    def is_published(self):
        """Check if page is published"""
        return self.status == 'published'

from django.contrib import admin
from .models import (
    Carousel, CarouselSlide, Advertisement,
    # Banner,
    # Testimonial, FAQ, 
    NewsletterSubscriber, ContactMessage, SiteSettings,CuratedItem
)
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError



from django.contrib import admin
from django.utils.html import format_html

class CarouselSlideInline(admin.StackedInline):
    model = CarouselSlide
    extra = 1

    fields = (
        'title',
        'subtitle',
        'description',
        ('image', 'image_preview'),
        'link_url',
        ('order', 'is_active'),
    )
    ordering = ('order',)
    # classes = ['collapse']

    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height:120px; border-radius:6px;" />',
                obj.image.url
            )
        return "No image"

    image_preview.short_description = "Preview"


@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'is_active', 'auto_play', 'order', 'created_at', 'action_buttons']
    list_filter = ['position', 'is_active', 'auto_play']
    search_fields = ['title']
    inlines = [CarouselSlideInline]
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:website_carousel_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'ad_type',
        'position',
        'is_active',
        'current_impressions',
        'click_count',
        'ctr_display',
        'action_buttons',
    ]
    list_filter = ['ad_type', 'position', 'is_active', 'start_date']
    search_fields = ['title']
    readonly_fields = ['current_impressions', 'click_count', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'ad_type', 'position','image','link_url', 'order')
        }),
        # ('Media', {
        #     'fields': ('image',)
        # }),
        # ('Link', {
        #     'fields': ('link_url', 'open_in_new_tab')
        # }),
        ('Display Settings', {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ('Analytics', {
            'fields': ('max_impressions', 'current_impressions', 'click_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def ctr_display(self, obj):
        if obj.current_impressions > 0:
            return f"{(obj.click_count / obj.current_impressions) * 100:.2f}%"
        return "0%"
    ctr_display.short_description = "CTR"
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:website_advertisement_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


# @admin.register(Banner)
# class BannerAdmin(admin.ModelAdmin):
#     list_display = ['title', 'banner_type', 'position', 'is_active', 'start_date', 'end_date']
#     list_filter = ['banner_type', 'position', 'is_active']
#     search_fields = ['title', 'heading']


# @admin.register(Testimonial)
# class TestimonialAdmin(admin.ModelAdmin):
#     list_display = ['customer_name', 'rating', 'is_featured', 'is_active', 'created_at']
#     list_filter = ['rating', 'is_featured', 'is_active']
#     search_fields = ['customer_name', 'title', 'content']


# @admin.register(FAQ)
# class FAQAdmin(admin.ModelAdmin):
#     list_display = ['question', 'category', 'is_active', 'view_count', 'helpful_count', 'order']
#     list_filter = ['category', 'is_active']
#     search_fields = ['question', 'answer']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_at', 'action_buttons']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email', 'name']
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:website_newslettersubscriber_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'replied', 'created_at', 'action_buttons']
    list_filter = ['is_read', 'replied', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:website_contactmessage_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Company Information', {
            'fields': ('site_name', 'site_tagline', 'site_description', 'logo', 'favicon')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url')
        }),
        ('Settings', {
            'fields': ('maintenance_mode', 'allow_guest_checkout',
                    #    'show_stock_quantity'
                       )
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
    )
    # ❌ Disable adding more than one object
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    # (optional but recommended)
    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(CuratedItem)
class CuratedItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "linked_to",
        # "badge_text",
        "position",
        "is_active",
        "image_preview",
        "created_at",
        "action_buttons",
    )

    list_editable = ("position", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "subtitle", 
                    #  "badge_text"
                     )

    ordering = ("position", "-created_at")

    fieldsets = (
        ("Link Target", {
            "fields": ("product", "category"),
            "description": "Select either Product OR Category (not both)."
        }),
        ("Content", {
            "fields": (
                "title",
                "subtitle",
                "image",
                # "badge_text",
                # "badge_color",
                "button_text",
                "link_url",
            )
        }),
        ("Settings", {
            "fields": ("position", "is_active")
        }),
    )

    readonly_fields = ("image_preview", "created_at")

    # ---------- Custom Methods ----------

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px; border-radius:6px;" />',
                obj.image.url
            )
        return "—"

    image_preview.short_description = "Preview"

    def linked_to(self, obj):
        if obj.product:
            return f"Product: {obj.product}"
        if obj.category:
            return f"Category: {obj.category}"
        return "Custom Link"

    linked_to.short_description = "Linked To"
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:website_curateditem_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'

    # ---------- Validation ----------

    def save_model(self, request, obj, form, change):
        if obj.product and obj.category:
            raise ValidationError(
                "Please select either a Product or a Category, not both."
            )
        super().save_model(request, obj, form, change)
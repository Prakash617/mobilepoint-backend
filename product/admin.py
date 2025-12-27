from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant, ProductVariantAttributeValue, ProductImage, ProductPromotion,
    FrequentlyBoughtTogether,
    ProductComparison,Deal,RecentlyViewedProduct
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent','logo_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']

    def logo_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.image.url)
        return '-'
    logo_preview.short_description = 'Image'

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_preview', 'is_featured', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.logo.url)
        return '-'
    logo_preview.short_description = 'Logo'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order', 'variant', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'


class ProductVariantAttributeValueInline(admin.TabularInline):
    model = ProductVariantAttributeValue
    extra = 1
    autocomplete_fields = ['attribute_value']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['sku', 'price', 'compare_at_price', 'stock_quantity', 'is_active', 'is_default']
    readonly_fields = []
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'base_price', 'is_active', 'is_new', 'is_featured', 'variant_count', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'created_at']
    search_fields = ['name', 'short_description', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured']
    autocomplete_fields = ['category', 'brand']
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug','short_description', 'description', 'category', 'brand')
        }),
        ('Pricing', {
            'fields': ('base_price',)
        }),
        ('Specifications', {
            'fields': ('specifications',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )
    
    def is_new(self, obj):
        return obj.is_new
    is_new.boolean = True  # Shows a nice True/False icon
    is_new.short_description = "New?"
    
    def variant_count(self, obj):
        count = obj.variants.count()
        return format_html('<span style="color: {};">{}</span>', 
                        'green' if count > 0 else 'red', count)
    variant_count.short_description = 'Variants'


@admin.register(VariantAttribute)
class VariantAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'value_count']
    search_fields = ['name', 'display_name']
    
    def value_count(self, obj):
        return obj.values.count()
    value_count.short_description = 'Values'


@admin.register(VariantAttributeValue)
class VariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'color_preview', 'image_preview']
    list_filter = ['attribute']
    search_fields = ['value', 'attribute__name']
    autocomplete_fields = ['attribute']
    
    def color_preview(self, obj):
        if obj.color_code:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.color_code
            )
        return '-'
    color_preview.short_description = 'Color'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'price', 'stock_quantity', 'sold_quantity', 'stock_status', 'is_active', 'is_default', 'get_attributes']
    list_filter = ['is_active', 'is_default', 'product__category', 'product__brand']
    search_fields = ['sku', 'product__name']
    autocomplete_fields = ['product']
    inlines = [ProductVariantAttributeValueInline, ProductImageInline]
    list_editable = ['is_active', 'stock_quantity','sold_quantity']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'sku')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity','sold_quantity', 'low_stock_threshold')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
    )
    
    def get_attributes(self, obj):
        attrs = obj.attribute_values.select_related('attribute_value__attribute')
        return ', '.join([f"{av.attribute.name}: {av.value}" for av in attrs])
    get_attributes.short_description = 'Attributes'
    
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            color = 'red'
            status = 'Out of Stock'
        elif obj.is_low_stock:
            color = 'orange'
            status = 'Low Stock'
        else:
            color = 'green'
            status = 'In Stock'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
    stock_status.short_description = 'Stock Status'


@admin.register(ProductVariantAttributeValue)
class ProductVariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ['variant', 'attribute_value', 'get_attribute_name', 'get_value']
    list_filter = ['attribute_value__attribute']
    search_fields = ['variant__sku', 'attribute_value__value']
    autocomplete_fields = ['variant', 'attribute_value']
    
    def get_attribute_name(self, obj):
        return obj.attribute_value.attribute.name
    get_attribute_name.short_description = 'Attribute'
    
    def get_value(self, obj):
        return obj.attribute_value.value
    get_value.short_description = 'Value'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant', 'image_preview', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at', 'product']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_primary', 'order']
    autocomplete_fields = ['product', 'variant']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'
    


# -----------------------------------
# Product Promotion Admin
# -----------------------------------
@admin.register(ProductPromotion)
class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "title",
        "promotion_type",
        "is_active",
        "start_date",
        "end_date",
    )
    list_filter = (
        "promotion_type",
        "is_active",
        "start_date",
        "end_date",
    )
    search_fields = (
        "product__name",
        "title",
        "description",
    )
    date_hierarchy = "start_date"
    autocomplete_fields = ["product"]
    ordering = ("-start_date",)

    fieldsets = (
        ("Product", {
            "fields": ("product",)
        }),
        ("Promotion Details", {
            "fields": (
                "promotion_type",
                "title",
                "description",
                "icon",
            )
        }),
        ("Schedule & Status", {
            "fields": (
                "start_date",
                "end_date",
                "is_active",
            )
        }),
    )


# -----------------------------------
# Frequently Bought Together Admin
# -----------------------------------
@admin.register(FrequentlyBoughtTogether)
class FrequentlyBoughtTogetherAdmin(admin.ModelAdmin):
    list_display = (
        "main_product",
        "related_product",
        "discount_percentage",
        "display_order",
        "is_active",
    )
    list_filter = (
        "is_active",
    )
    search_fields = (
        "main_product__name",
        "related_product__name",
    )
    autocomplete_fields = (
        "main_product",
        "related_product",
    )
    ordering = ("display_order",)

    fieldsets = (
        ("Products", {
            "fields": (
                "main_product",
                "related_product",
            )
        }),
        ("Offer Details", {
            "fields": (
                "discount_percentage",
                "display_order",
                "is_active",
            )
        }),
    )


# -----------------------------------
# Product Comparison Admin
# -----------------------------------
@admin.register(ProductComparison)
class ProductComparisonAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product",
        "added_at",
    )
    list_filter = (
        "added_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "product__name",
    )
    autocomplete_fields = (
        "user",
        "product",
    )
    date_hierarchy = "added_at"
    ordering = ("-added_at",)


from django.contrib import admin
from .models import Deal

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    # Columns to display in list view
    list_display = (
        'title',
        'deal_type',
        'product',
        'variant',
        'original_price',
        'discounted_price',
        'discount_percentage',
        'start_date',
        'end_date',
        'is_active',
        'is_featured',
        'remaining_quantity',
        'is_sold_out',
        'free_gift',
        'gift_message',
        'sold_quantity',
    )
    
    # Filters for sidebar
    list_filter = (
        'deal_type',
        'is_active',
        'is_featured',
        'start_date',
        'end_date',
        'product'
    )
    
    # Fields searchable via search box
    search_fields = ('title', 'product__name', 'variant__name')
    
    # Auto-fill slug from title
    prepopulated_fields = {'slug': ('title',)}
    
    # Editable fields directly in list view
    list_editable = ('discounted_price', 'is_active','sold_quantity', 'is_featured')
    
    # Field grouping in admin form
    fieldsets = (
        ('Deal Info', {
            'fields': ('title', 'slug', 'deal_type', 'product', 'variant', 'description', 'terms_and_conditions')
        }),
        ('Pricing', {
            'fields': ('original_price', 'discounted_price', 'discount_percentage')
        }),
        ('Inventory', {
            'fields': ('total_quantity', 'sold_quantity', 'max_quantity_per_order')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Display & Badge', {
            'fields': ('badge_text', 'badge_color', 'highlight_features', 'is_featured', 'display_order')
        }),
        ('Shipping', {
            'fields': ('free_shipping', 'shipping_message','free_gift', 'gift_message')
        }),
        ('Analytics', {
            'fields': ('view_count', 'click_count')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = (
        'discount_percentage',
        # 'sold_quantity',
        'view_count',
        'click_count',
        'remaining_quantity',
        'is_sold_out'
    )
    
    ordering = ('-is_featured', 'display_order', '-created_at')


@admin.register(RecentlyViewedProduct)
class RecentlyViewedProductAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'viewed_at']
    list_filter = ['viewed_at', 'user']
    search_fields = ['user__username', 'product__name']
    ordering = ['-viewed_at']
    readonly_fields = ['viewed_at']  # optional: make viewed_at read-only
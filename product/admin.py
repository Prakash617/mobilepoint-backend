from django.contrib import admin
from django.utils.html import format_html, format_html_join, mark_safe
from .models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant, ProductVariantAttributeValue, ProductImage, ProductPromotion,
    FrequentlyBoughtTogether,
    # ProductComparison,
    Deal,RecentlyViewedProduct
    )
from reviews.models import ProductReview
from django import forms
import nested_admin
from django.urls import reverse

class ColorPickerWidget(forms.TextInput):
    """Custom widget for color picker with HTML5 color input"""
    input_type = 'color'
    
    def __init__(self, attrs=None):
        default_attrs = {'style': 'width: 100px; height: 50px; cursor: pointer; border: 1px solid #ddd; border-radius: 4px;'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

class VariantAttributeValueForm(forms.ModelForm):
    color_code = forms.CharField(
        required=False,
        widget=ColorPickerWidget(),
        help_text='Select a color or enter hex value (e.g., #FF0000)'
    )
    
    class Meta:
        model = VariantAttributeValue
        fields = "__all__"
        widgets = {
            'color_code': ColorPickerWidget(),
        }

    class Media:
        js = ("admin/js/variant_attribute_value.js",)
    
    def clean_color_code(self):
        """Validate and format color code"""
        color_code = self.cleaned_data.get('color_code')
        if color_code:
            # Ensure it starts with # and is valid hex
            if not color_code.startswith('#'):
                color_code = '#' + color_code
            # Remove # and check if valid hex
            hex_value = color_code.lstrip('#')
            if len(hex_value) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in hex_value):
                raise forms.ValidationError('Please enter a valid hex color code (e.g., #FF0000)')
            return color_code.upper()
        return color_code


class VartientAttributeValueInlineForm(VariantAttributeValueForm):
    class Meta:
        model = VariantAttributeValue
        fields = "__all__"
    class Media:
        js = ("admin/js/variant_attribute_inline.js",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'image_preview', 'is_active', 'action_buttons']
    list_display_links = ['name']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:contain;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Image'

    def action_buttons(self, obj):
        edit_url = reverse('admin:product_category_change', args=[obj.id])
        # view_url = reverse('admin:product_category_change', args=[obj.id])  # Django admin does not have a separate "view" page by default
        return format_html(
            '<a class="button" href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
        'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            # '<a class="button" href="{}">View</a>',
            edit_url,
            # view_url
        )
    action_buttons.short_description = 'Actions'
    # action_buttons.allow_tags = True //depricated
    
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_preview', 'is_featured', 'is_active', 'action_buttons']
    list_display_links = ['name']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:contain;" />',
                obj.logo.url
            )
        return '-'
    logo_preview.short_description = 'Logo'

    def action_buttons(self, obj):
        edit_url = reverse('admin:product_brand_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'
    
class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    fk_name = "product"   
    extra = 1

    fields = ['image', 'image_preview', 'alt_text', 'is_primary', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:100px; object-fit:contain;" />',
                obj.image.url
            )
        return "No image"
    
class ProductImageInlineForVariant(nested_admin.NestedTabularInline):
    model = ProductImage
    fk_name = "variant"          # Must point to Variant FK
    extra = 1
    fields = ['image',
              'image_preview', 
              'alt_text', 'is_primary', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:100px; object-fit:contain;" />',
                obj.image.url
            )
        return "No image"
class ProductImageInlineForVariantNoNested(admin.TabularInline):
    model = ProductImage
    fk_name = "variant"          # Must point to Variant FK
    extra = 1
    fields = ['image',
              'image_preview', 
              'alt_text', 'is_primary', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:100px; object-fit:contain;" />',
                obj.image.url
            )
        return "No image"


class ProductVariantAttributeValueInline(nested_admin.NestedStackedInline):
    model = ProductVariantAttributeValue
    extra = 1
    autocomplete_fields = ['attribute_value']
    
class ProductVariantAttributeValueInlineNoNested(admin.TabularInline):
    model = ProductVariantAttributeValue
    extra = 1
    autocomplete_fields = ['attribute_value']


class ProductVariantInline(nested_admin.NestedStackedInline):
    model = ProductVariant
    fk_name = 'product'  # This tells Django which FK to use
    extra = 1  # Show 1 empty form for adding new variant
    fields = [
        'sku',
        'selling_price',
        'regular_price',
        # 'cost_price',
        'stock_quantity',
        'sold_quantity',
        'low_stock_threshold',
        'is_active',
        'is_default',
        # 'created_at',
        # 'updated_at',
    ]
    readonly_fields = ['created_at', 'updated_at']
    # show_change_link = True
    
    inlines = [ProductVariantAttributeValueInline, ProductImageInlineForVariant] 



from django.utils.html import format_html
from django.urls import reverse

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ['name', 'brand', 'category', 'base_price', 'is_active', 'is_new', 'is_featured', 'variant_attributes', 'action_buttons']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'created_at']
    search_fields = ['name', 'short_description', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured']
    autocomplete_fields = ['category', 'brand']
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug','short_description', 'description', 'category', 'brand','base_price')
        }),
        ('Specifications', {
            'fields': ('specifications',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    def is_new(self, obj):
        return obj.is_new
    is_new.boolean = True
    is_new.short_description = "New?"
    
    def variant_attributes(self, obj):
        variants = obj.variants.all()  # all variants for this product
        if not variants.exists():
            return format_html('<span style="color: red;">No variants</span>')

        rows = []
        for variant in variants:
            # Get all attribute values for this variant
            attr_values = variant.attribute_values.select_related('attribute_value__attribute')
            # Combine attribute name and value: Color: Red / Size: M
            value_texts = [
                f"{av.attribute_value.attribute.name}: {av.attribute_value.value}" 
                for av in attr_values
            ]
            row_text = f"{variant.sku}: {' / '.join(value_texts) if value_texts else '-'}"
            rows.append(row_text)

        # Join each variant on a new line with HTML line breaks
        return mark_safe('<br>'.join(rows))

    variant_attributes.short_description = 'Variants'

    def action_buttons(self, obj):
        edit_url = reverse('admin:product_product_change', args=[obj.id])
        # Assuming your Product frontend view is at /products/<slug>/, adjust if different
        # view_url = f'/products/{obj.slug}/'
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            # '<a href="{}" target="_blank" style="padding:4px 10px; background-color:#28A745; color:white; '
            # 'border-radius:5px; text-decoration:none; font-weight:bold;">View</a>',
            edit_url,
            # view_url
        )
    action_buttons.short_description = 'Actions'

class VartientAttributeValueInline(admin.TabularInline):
    model = VariantAttributeValue
    form = VartientAttributeValueInlineForm  # attach the new form
    fields = ('types', 'value', 'color_code', 'image',)
    extra = 0


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'selling_price', 'stock_quantity', 'sold_quantity', 'stock_status', 'is_active', 'is_default', 'get_attributes', 'action_buttons']
    list_filter = ['is_active', 'is_default', 'product__category', 'product__brand']
    search_fields = ['sku', 'product__name']
    autocomplete_fields = ['product']
    inlines = [ProductVariantAttributeValueInlineNoNested, ProductImageInlineForVariantNoNested]
    list_editable = ['is_active', 'stock_quantity','sold_quantity']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'sku')
        }),
        ('Pricing', {
            'fields': ('selling_price', 'regular_price')
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
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_productvariant_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'



@admin.register(VariantAttribute)
class VariantAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'value_names', 'action_buttons']
    search_fields = ['name', 'display_name']
    inlines = [VartientAttributeValueInline]

    def value_names(self, obj):
        items = []
        for v in obj.values.all():
            if v.types == 'text' and v.value:
                items.append(v.value)
            elif v.types == 'color' and v.color_code:
                # Show color swatch
                items.append(
                    f'<div style="display:inline-block; width:24px; height:24px; background-color:{v.color_code}; border:1px solid #ccc; border-radius:3px; margin-right:5px;" title="{v.color_code}"></div>'
                )
            elif v.types == 'image' and v.image:
                # Show small image preview
                items.append(
                    f'<img src="{v.image.url}" width="24" height="24" style="object-fit:contain; margin-right:5px; border:1px solid #ccc; border-radius:3px;" />'
                )
        
        if items:
            return mark_safe(' '.join(items))
        return "-"
    
    value_names.short_description = 'Varient Values'
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_variantattribute_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'




@admin.register(VariantAttributeValue)
class VariantAttributeValueAdmin(admin.ModelAdmin):
    form = VariantAttributeValueForm
    list_display = ['attribute', 'value', 'color_code_display', 'image_preview', 'action_buttons']
    list_filter = ['attribute']
    search_fields = ['value', 'attribute__name']
    autocomplete_fields = ['attribute']
    
    def color_code_display(self, obj):
        """Display color code with actual color preview in list view"""
        if obj.color_code:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="width: 30px; height: 30px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>'
                '<span style="font-family: monospace; font-weight: bold;">{}</span>'
                '</div>',
                obj.color_code,
                obj.color_code
            )
        return '-'
    color_code_display.short_description = 'Color'
    
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
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_variantattributevalue_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'





@admin.register(ProductVariantAttributeValue)
class ProductVariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ['variant', 'attribute_value', 'get_attribute_name', 'get_value', 'action_buttons']
    list_filter = ['attribute_value__attribute']
    search_fields = ['variant__sku', 'attribute_value__value']
    autocomplete_fields = ['variant', 'attribute_value']
    
    def get_attribute_name(self, obj):
        return obj.attribute_value.attribute.name
    get_attribute_name.short_description = 'Attribute'
    
    def get_value(self, obj):
        return obj.attribute_value.value
    get_value.short_description = 'Value'
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_productvariantattributevalue_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant', 'image_preview', 'is_primary', 'order', 'created_at', 'action_buttons']
    list_filter = ['is_primary', 'created_at', 'product']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_primary', 'order']
    autocomplete_fields = ['product', 'variant']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_productimage_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'
    


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
        "action_buttons",
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
            "fields": ("product","promotion_type",
                "title",
                "description",
                # "icon",
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
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_productpromotion_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


# -----------------------------------
# Frequently Bought Together Admin
# -----------------------------------
# @admin.register(FrequentlyBoughtTogether)
# class FrequentlyBoughtTogetherAdmin(admin.ModelAdmin):
#     list_display = (
#         "main_product",
#         "related_product",
#         "discount_percentage",
#         "display_order",
#         "is_active",
#     )
#     list_filter = (
#         "is_active",
#     )
#     search_fields = (
#         "main_product__name",
#         "related_product__name",
#     )
#     autocomplete_fields = (
#         "main_product",
#         "related_product",
#     )
#     ordering = ("-start_date",)

#     fieldsets = (
#         ("Products", {
#             "fields": (
#                 "main_product",
#                 "related_product",
#             )
#         }),
#         ("Offer Details", {
#             "fields": (
#                 "discount_percentage",
#                 "display_order",
#                 "is_active",
#             )
#         }),
#     )


# -----------------------------------
# Product Comparison Admin
# # -----------------------------------
# @admin.register(ProductComparison)
# class ProductComparisonAdmin(admin.ModelAdmin):
#     list_display = (
#         "user",
#         "product",
#         "added_at",
#     )
#     list_filter = (
#         "added_at",
#     )
#     search_fields = (
#         "user__username",
#         "user__email",
#         "product__name",
#     )
    # autocomplete_fields = (
    #     "user",
    #     "product",
    # )
#     date_hierarchy = "added_at"
#     ordering = ("-added_at",)


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
        'action_buttons',
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
        # ('Status', {
        #     'fields': ('is_active',)
        # }),
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
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_deal_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


@admin.register(RecentlyViewedProduct)
class RecentlyViewedProductAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'viewed_at', 'action_buttons']
    list_filter = ['viewed_at', 'user']
    search_fields = ['user__username', 'product__name']
    ordering = ['-viewed_at']
    readonly_fields = ['viewed_at']  # optional: make viewed_at read-only
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_recentlyviewedproduct_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'

# class ProductVariantAutocompleteAdmin(admin.ModelAdmin):
#     search_fields = ['sku', 'product__name'] # Assuming product__name works. If not, maybe product__name.

# admin.site.register(ProductVariant, ProductVariantAutocompleteAdmin)
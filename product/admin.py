from django.contrib import admin
from django.utils.html import format_html, format_html_join, mark_safe
from .models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant,
    # ProductVariantAttributeValue, 
    ProductImage, Promotion,
    ProductCombo,
    ProductComboItem,
    # ProductComparison,
    Deal, RecentlyViewedProduct
    )
from reviews.models import ProductReview
from django import forms
import nested_admin
from django.http import JsonResponse
from django.urls import path
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

    # class Media:
    #     js = ("admin/js/variant_attribute_value.js",)
    
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
    list_display = ['name', 'parent', 'image_preview', 'is_active','is_featured', 'action_buttons']
    list_display_links = ['name']
    list_editable = ['is_active','is_featured',]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    exclude = ['is_active','is_featured',] # this removes it from the form

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:contain;" />',
                obj.image
                
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
    list_display = ['name', 'logo_preview', 'is_active','is_featured', 'action_buttons']
    list_display_links = ['name']
    list_editable = ['is_active','is_featured',]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    # Hide is_featured from the add/edit form
    exclude = ['is_active','is_featured',] # this removes it from the form
    

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:contain;" />',
                obj.logo
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
    
class ProductImageInlineNoNestedProduct(admin.TabularInline):
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


# class ProductVariantAttributeValueInline(nested_admin.NestedStackedInline):
#     model = ProductVariantAttributeValue
#     extra = 1
#     autocomplete_fields = ['attribute_value']
    
# class ProductVariantAttributeValueInlineNoNested(admin.TabularInline):
#     model = ProductVariantAttributeValue
#     extra = 1
#     autocomplete_fields = ['attribute_value']


class ProductVariantInline(nested_admin.NestedStackedInline):
    model = ProductVariant
    fk_name = 'product'
    extra = 0
    fields = [
        # Manage variant attribute values via the ProductVariantAttributeValue inline
        'variant_attributes',
        'price',
        'stock_quantity',
        'sold_quantity',
        'low_stock_threshold',
        # 'is_active',
    ]
    readonly_fields = ['created_at', 'updated_at',"sold_quantity"]
    
    inlines = [
        # ProductVariantAttributeValueInline,
            ProductImageInlineForVariant] 



from django.utils.html import format_html
from django.urls import reverse

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ['name', 'brand', 'category', 'base_price', 'is_active', 
                    'is_featured', 
                    'get_attributes', 
                    'action_buttons']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'created_at']
    search_fields = ['name', 'short_description', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured']
    autocomplete_fields = []
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug','short_description', 'description',  'category','brand','base_price')
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
    
    class Media:
        js = ("admin/js/product_admin.js",)
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "get-brands/",
                self.admin_site.admin_view(self.get_brands),
                name="get_brands",
            ),
        ]
        return custom_urls + urls

    def get_brands(self, request):
        category_id = request.GET.get("category_id")

        brands = Brand.objects.filter(
            category__id=category_id,
            is_active=True
        ).distinct()

        return JsonResponse(
            [{"id": b.id, "name": b.name} for b in brands],
            safe=False
        )

    def get_attributes(self, obj):
        variants = obj.variants.all()

        if not variants.exists():
            return format_html('<span style="color: red;">{}</span>', 'No variants')

        rows = []

        for variant in variants:
            attr_values = variant.variant_attributes.all().select_related('attribute')
            
            value_texts = []
            for av in attr_values:
                display_value = ''
                if av.types == 'color' and av.color_code:
                    display_value = f'<span style="display: inline-block; width: 20px; height: 20px; background-color: {av.color_code}; border: 1px solid #ccc; vertical-align: middle; border-radius: 50%;" title="{av.color_code}"></span>'
                elif av.types == 'image' and av.image:
                    display_value = f'<img src="{av.image.url}" style="width: 40px; height: 40px; object-fit: cover; vertical-align: middle; border-radius: 4px;" title="Image">'
                else:  # text or fallback
                    display_value = av.value or ''

                value_texts.append(f"{av.attribute.name}: {display_value}")

            row_text = f"Rs. {variant.price}: {' / '.join(value_texts) if value_texts else '-'}"
            rows.append(row_text)

        return mark_safe('<br>'.join(rows))

    get_attributes.short_description = "Variants"
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_product_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url,
        )
    action_buttons.short_description = 'Actions'

class VartientAttributeValueInline(admin.TabularInline):
    model = VariantAttributeValue
    form = VartientAttributeValueInlineForm
    fields = ('types', 'value', 'color_code', 'image',)
    extra = 0


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = [ 'product', 'price', 'stock_quantity', 'sold_quantity', 'stock_status', 'is_active', 'is_default', 'get_attributes', 'action_buttons']
    list_filter = ['is_active', 'is_default', 'product__category', 'product__brand']
    search_fields = ['product__name']
    autocomplete_fields = ['product']
    # inlines = [ProductVariantAttributeValueInlineNoNested, ProductImageInlineForVariantNoNested]
    inlines = [ ProductImageInlineForVariantNoNested]
    list_editable = ['is_active', 'stock_quantity','sold_quantity']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product','price' )
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
        
        value_texts = []
        for av in attrs:
            display_value = ''
            attribute_value = av.attribute_value
            if attribute_value.types == 'color' and attribute_value.color_code:
                display_value = f'<span style="display: inline-block; width: 20px; height: 20px; background-color: {attribute_value.color_code}; border: 1px solid #ccc; vertical-align: middle; border-radius: 50%;" title="{attribute_value.color_code}"></span>'
            elif attribute_value.types == 'image' and attribute_value.image:
                display_value = f'<img src="{attribute_value.image.url}" style="width: 40px; height: 40px; object-fit: cover; vertical-align: middle; border-radius: 4px;" title="Image">'
            else:  # text or fallback
                display_value = attribute_value.value or ''

            value_texts.append(f"{av.attribute.name}: {display_value}")
        
        return mark_safe(', '.join(value_texts))
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


class VariantAttributeAdminForm(forms.ModelForm):
    class Meta:
        model = VariantAttribute
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the green + button for related fields
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'can_add_related'):
                field.widget.can_add_related = False

@admin.register(VariantAttribute)
class VariantAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'value_names', 'action_buttons']
    search_fields = ['name', 'display_name']
    inlines = [VartientAttributeValueInline]
    form = VariantAttributeAdminForm

    def value_names(self, obj):
        items = []
        for v in obj.values.all():
            if v.types == 'text' and v.value:
                items.append(v.value)
            elif v.types == 'color' and v.color_code:
                items.append(
                    f'<div style="display:inline-block; width:24px; height:24px; background-color:{v.color_code}; border:1px solid #ccc; border-radius:3px; margin-right:5px;" title="{v.color_code}"></div>'
                )
            elif v.types == 'image' and v.image:
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





# @admin.register(ProductVariantAttributeValue)
# class ProductVariantAttributeValueAdmin(admin.ModelAdmin):
#     list_display = ['variant', 'attribute_value', 'get_attribute_name', 'get_value', 'action_buttons']
#     list_filter = ['attribute_value__attribute']
#     search_fields = ['attribute_value__value']
#     autocomplete_fields = ['variant', 'attribute_value']
    
#     def get_attribute_name(self, obj):
#         return obj.attribute_value.attribute.name
#     get_attribute_name.short_description = 'Attribute'
    
#     def get_value(self, obj):
#         return obj.attribute_value.value
#     get_value.short_description = 'Value'
    
#     def action_buttons(self, obj):
#         edit_url = reverse('admin:product_productvariantattributevalue_change', args=[obj.id])
#         return format_html(
#             '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
#             'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
#             edit_url
#         )
#     action_buttons.short_description = 'Actions'


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
@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
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
        "title",
        "description",
    )
    date_hierarchy = "start_date"
    filter_horizontal = ["products"]
    ordering = ("-start_date",)

    fieldsets = (
        ("Promotion Info", {
            "fields": ("title", "promotion_type", "description")
        }),
        ("Associated Products", {
            "fields": ("products",)
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
        edit_url = reverse('admin:product_promotion_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'
    
    


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'deal_type',
        'product',
        'discount_percent',
        'inventory_progress',
        'stats_display',
        'extras_display',
        'start_at',
        'end_at',
        'is_active',
        'is_featured',
        'display_order',
        'action_buttons',
    )
    
    list_filter = (
        'deal_type',
        'is_active',
        'is_featured',
        'free_shipping',
        'start_at',
        'end_at',
    )
    
    search_fields = ('title', 'product__name')
    
    list_editable = ('is_active', 'is_featured', 'display_order')
    
    fieldsets = (
        ('Deal Info', {
            'fields': ('title', 'deal_type', 'product', 'discount_percent')
        }),
        ('Inventory', {
            'fields': ('total_quantity', 'sold_quantity')
        }),
        ('Statistics', {
            'fields': ('views', 'purchases'),
            'classes': ('collapse',)
        }),
        # ('Extra Benefits', {
        #     'fields': ('free_shipping', 'free_gift_text'),
        #     # 'classes': ('collapse',)
        # }),
        ('Timing', {
            'fields': ('start_at', 'end_at')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'display_order')
        }),
    )
    
    readonly_fields = ('views', 'purchases', 'created_at', 'updated_at')
    
    def inventory_progress(self, obj):
        """Display inventory progress as a readable string"""
        return format_html(
            '<span title="Progress: {}%">{}/{}</span>',
            obj.progress_percentage,
            obj.sold_quantity,
            obj.total_quantity
        )
    inventory_progress.short_description = 'Inventory'
    
    def stats_display(self, obj):
        """Display views and purchases stats"""
        return format_html(
            '<span style="background:#e3f2fd;padding:3px 8px;border-radius:3px;margin-right:5px;">👁️ {}</span>'
            '<span style="background:#e8f5e9;padding:3px 8px;border-radius:3px;">🛒 {}</span>',
            obj.views,
            obj.purchases
        )
    stats_display.short_description = 'Stats (Views/Purchases)'
    
    def extras_display(self, obj):
        """Display extra benefits"""
        extras = []
        if obj.free_shipping:
            extras.append('<span style="background:#fff3e0;padding:3px 8px;border-radius:3px;">🚚 Free Shipping</span>')
        if obj.free_gift_text:
            extras.append(f'<span style="background:#fce4ec;padding:3px 8px;border-radius:3px;">🎁 {obj.free_gift_text}</span>')
        return format_html(' '.join(extras)) if extras else '-'
    extras_display.short_description = 'Extra Benefits'
    
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
    readonly_fields = ['viewed_at']
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:product_recentlyviewedproduct_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


class ProductComboItemInline(admin.TabularInline):
    """Inline admin for ProductComboItem"""
    model = ProductComboItem
    extra = 1
    autocomplete_fields = ['product']
    fields = ['product', 'quantity', 'action_buttons']
    readonly_fields = ['action_buttons']

    def action_buttons(self, obj):
        if obj.pk:
            edit_url = reverse('admin:product_productcomboitem_change', args=[obj.id])
            return format_html(
                '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
                'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
                edit_url
            )
        return '-'
    action_buttons.short_description = 'Actions'


@admin.register(ProductCombo)
class ProductComboAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'main_product',
        'combo_selling_price',
        'combo_regular_price',
        'is_active',
        'is_featured',
        'item_count',
        'action_buttons',
    )
    list_filter = ('is_active', 'is_featured', 'created_at', 'main_product')
    search_fields = ('name', 'slug', 'description', 'main_product__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured')
    autocomplete_fields = ['main_product']
    inlines = [ProductComboItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'main_product', 'slug', 'description')
        }),
        ('Pricing', {
            'fields': ('combo_regular_price', 'combo_selling_price')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )

    def item_count(self, obj):
        count = obj.items.count()
        return format_html(
            '<span style="background-color:#007BFF; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">{}</span>',
            count
        )
    item_count.short_description = 'Items'

    def action_buttons(self, obj):
        edit_url = reverse('admin:product_productcombo_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'


@admin.register(ProductComboItem)
class ProductComboItemAdmin(admin.ModelAdmin):
    list_display = (
        'combo',
        'product',
        'quantity',
        'action_buttons',
    )
    list_filter = ('combo',)
    search_fields = ('combo__name', 'product__name')
    autocomplete_fields = ['combo', 'product']
    list_editable = ('quantity',)

    def action_buttons(self, obj):
        edit_url = reverse('admin:product_productcomboitem_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'
from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory
from django import forms
from django.utils.html import format_html

class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal', 'product_name', 'variant_name']
    fields = ['product', 'product_variant', 'product_name', 'variant_name', 'quantity', 'price', 'subtotal']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at', 'created_by', 'status']

class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
    
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = ['order_number', 'user', 'status', 'payment_status', 'total', 'created_at']
    list_editable = ['status']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'shipping_email']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'status_badge']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'notes'),
            'description': 'Update the status using the buttons below'
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'discount', 'total')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_email', 'shipping_phone', 
                    'shipping_address', 'shipping_city', 'shipping_state', 
                    'shipping_zip', 'shipping_country', 'tracking_number')
        }),
        ('Billing Information', {
            'fields': ('billing_name', 'billing_address', 'billing_city', 
                    'billing_state', 'billing_zip', 'billing_country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    class Media:
        css = {
            'all': ('admin/css/order_status.css',)
        }
        js = ('admin/js/order_status.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        """Use custom form only when editing a single order, not in list view"""
        if obj:
            kwargs['form'] = OrderAdminForm
        return super().get_form(request, obj, **kwargs)
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'pending': '#FFA500',
            'confirmed': '#4169E1',
            'processing': '#9370DB',
            'shipped': '#20B2AA',
            'delivered': '#228B22',
            'cancelled': '#DC143C',
            'refunded': '#FF69B4',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Save the order and create a status history entry if status changed"""
        if change:  # Only if editing existing order
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Create a status history entry
                OrderStatusHistory.objects.create(
                    order=obj,
                    status=obj.status,
                    notes=f'Status changed from {old_obj.get_status_display()} to {obj.get_status_display()}',
                    created_by=request.user
                )
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'product_variant', 'product_name', 'variant_name', 'quantity', 'price', 'subtotal']
    list_filter = ['created_at', 'order']
    search_fields = ['order__order_number', 'product_name', 'product__name', 'product_variant__id']
    readonly_fields = ['subtotal', 'product_name', 'variant_name']
    fieldsets = (
        ('Product Information', {
            'fields': ('order', 'product', 'product_variant', 'product_name', 'variant_name')
        }),
        ('Pricing', {
            'fields': ('quantity', 'price', 'subtotal')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
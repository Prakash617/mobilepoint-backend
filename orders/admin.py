from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal', 'product_name', 'variant_name', 'original_price', 'discount_display', 'promotions_display']
    fields = ['product', 'product_variant', 'product_name', 'variant_name', 'quantity', 'price', 'original_price', 'discount_percent', 'subtotal', 'deal', 'promotions', 'free_gift_detail', 'combo', 'combo_parent', 'is_combo_parent', 'discount_display']
    filter_horizontal = ['promotions']
    
    def discount_display(self, obj):
        """Display calculated discount amount"""
        if obj.original_price and obj.discount_percent:
            discount_amount = (obj.original_price * obj.discount_percent) / 100
            return format_html(
                '{:.2f} ({}%)',
                discount_amount,
                obj.discount_percent
            )
        return '-'
    discount_display.short_description = 'Discount'
    
    def promotions_display(self, obj):
        """Display all promotions applied to this order item"""
        promos = obj.promotions.all()
        if promos.exists():
            promo_items = []
            for promo in promos:
                if promo.promotion_type == 'free_shipping':
                    promo_items.append(f'🚚 {promo.title}')
                elif promo.promotion_type == 'free_gift':
                    promo_items.append(f'🎁 {promo.title}')
            return format_html(
                '<div style="color: green; font-weight: bold;">' +
                '<br>'.join(promo_items) +
                '</div>'
            )
        return format_html('<span style="color: gray;">No promotions</span>')
    promotions_display.short_description = 'Applied Promotions'

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at', 'created_by', 'status']

class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
    
    order_status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = ['order_number', 'user', 'order_status', 'payment_status', 'payment_method_badge', 'tax', 'shipping_cost', 'applied_promotions_display', 'total', 'created_at']
    list_editable = ['order_status']
    list_filter = ['order_status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__email', 'shipping_email', 'payment_transaction_id']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'status_badge', 'payment_method_badge', 'applied_promotions_display']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'order_status', 'payment_status', 'notes'),
            'description': 'Update the status using the buttons below'
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_transaction_id')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'discount', 'total')
        }),
        ('Promotions', {
            'fields': ('applied_promotions_display',),
            'description': 'Promotions applied to this order'
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
    
    def payment_method_badge(self, obj):
        """Display payment method as a colored badge"""
        colors = {
            'cod': '#FFA500',
            'khalti': '#5C2D91',
            'esewa': '#60BB46',
            'bank_transfer': '#4169E1',
        }
        icons = {
            'cod': '💵',
            'khalti': '🟣',
            'esewa': '🟢',
            'bank_transfer': '🏦',
        }
        color = colors.get(obj.payment_method, '#808080')
        icon = icons.get(obj.payment_method, '💳')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_payment_method_display()
        )
    payment_method_badge.short_description = 'Payment Method'
    
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
        color = colors.get(obj.order_status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color,
            obj.get_order_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Save the order and create a status history entry if status changed"""
        if change:  # Only if editing existing order
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.order_status != obj.order_status:
                # Create a status history entry
                OrderStatusHistory.objects.create(
                    order=obj,
                    status=obj.order_status,
                    notes=f'Status changed from {old_obj.get_order_status_display()} to {obj.get_order_status_display()}',
                    created_by=request.user
                )
        super().save_model(request, obj, form, change)
    
    def applied_promotions_display(self, obj):
        """Display all applied promotions from order items with descriptions and links. Hide free_shipping if shipping charge is applied."""
        from django.urls import reverse
        
        # Check if shipping charge is applied to the order
        has_shipping_cost = obj.shipping_cost > 0
        
        # Get all promotions from order items via many-to-many relationship
        seen_promo_ids = set()
        promotion_links = []
        
        for item in obj.items.prefetch_related('promotions'):
            for promo in item.promotions.all():
                # Skip free_shipping promotions if shipping charge is applied
                if promo.promotion_type == 'free_shipping' and has_shipping_cost:
                    continue
                
                # Skip duplicates
                if promo.id in seen_promo_ids:
                    continue
                seen_promo_ids.add(promo.id)
                
                # Generate edit URL
                edit_url = reverse('admin:product_promotion_change', args=[promo.id])
                
                # Icon and colors based on promotion type
                if promo.promotion_type == 'free_shipping':
                    icon = '🚚'
                    bg_color = '#e3f2fd'  # Light blue
                    border_color = '#1976d2'  # Blue
                    text_color = '#0d47a1'  # Dark blue
                else:  # free_gift
                    icon = '🎁'
                    bg_color = '#f3e5f5'  # Light purple
                    border_color = '#7b1fa2'  # Purple
                    text_color = '#4a148c'  # Dark purple
                
                # Build promotion display with description and type
                description = promo.description if promo.description else '(No description)'
                promotion_type = promo.get_promotion_type_display()
                
                promo_html = (
                    f'<div style="margin-bottom: 12px; padding: 10px; background-color: {bg_color}; '
                    f'border-left: 4px solid {border_color}; border-radius: 4px;">'
                    f'<a href="{edit_url}" style="text-decoration: none; color: {text_color};">'
                    f'<strong style="font-size: 14px;">{icon} {promo.title}</strong></a><br>'
                    f'<small style="color: #666; display: block; margin-top: 4px;">{description}</small><br>'
                    f'<small style="color: {border_color}; font-weight: bold; display: block; margin-top: 4px;">Type: {promotion_type}</small>'
                    f'</div>'
                )
                promotion_links.append(promo_html)
        
        if promotion_links:
            return mark_safe(
                '<div style="color: #333; font-weight: bold;">' +
                ''.join(promotion_links) +
                '</div>'
            )
        return mark_safe(
            '<span style="color: gray;">No promotions</span>'
        )
    applied_promotions_display.short_description = 'Applied Promotions'



@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'deal_link', 'promotions_links', 'combo_link', 'is_combo_parent', 'subtotal']
    list_filter = ['created_at', 'order', 'is_combo_parent', 'deal', 'promotions', 'combo']
    search_fields = ['order__order_number', 'product_name', 'product__name', 'product_variant__id', 'deal__title', 'promotions__title', 'combo__name']
    readonly_fields = ['subtotal', 'product_name', 'variant_name', 'discount_display', 'combo_items_display', 'created_at', 'updated_at']
    filter_horizontal = ['promotions']
    fieldsets = (
        ('Product Information', {
            'fields': ('order', 'product', 'product_variant', 'product_name', 'variant_name')
        }),
        ('Pricing', {
            'fields': ('quantity', 'price', 'original_price', 'discount_percent', 'discount_display', 'subtotal')
        }),
        ('Deal Information', {
            'fields': ('deal',),
            'description': 'Associated deal if this item is from a promotion'
        }),
        ('Promotion Information', {
            'fields': ('promotions', 'free_gift_detail'),
            'description': 'Free shipping or free gift promotions applied'
        }),
        ('Combo Information', {
            'fields': ('combo', 'combo_parent', 'is_combo_parent', 'combo_items_display'),
            'description': 'Combo bundle tracking. Parent items are the bundle itself, child items are bundle contents.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def deal_link(self, obj):
        """Display deal link if associated"""
        if obj.deal:
            from django.urls import reverse
            url = reverse('admin:product_deal_change', args=[obj.deal.id])
            return format_html('<a href="{}">{}</a>', url, obj.deal.title)
        return '-'
    deal_link.short_description = 'Deal'
    
    def promotions_links(self, obj):
        """Display links for all promotions applied to this order item"""
        promos = obj.promotions.all()
        if promos.exists():
            from django.urls import reverse
            promo_links = []
            for promo in promos:
                url = reverse('admin:product_promotion_change', args=[promo.id])
                icon = '🚚' if promo.promotion_type == 'free_shipping' else '🎁'
                promo_links.append(
                    f'<a href="{url}" style="margin-right: 10px;"><strong>{icon} {promo.title}</strong></a>'
                )
            return format_html(
                '<div style="display: flex; flex-wrap: wrap; gap: 10px;">' +
                ''.join(promo_links) +
                '</div>'
            )
        return format_html('<span style="color: gray;">-</span>')
    promotions_links.short_description = 'Promotions'
    
    def combo_link(self, obj):
        """Display combo link if associated"""
        if obj.combo:
            from django.urls import reverse
            url = reverse('admin:product_productcombo_change', args=[obj.combo.id])
            return format_html('<a href="{}">{}</a>', url, obj.combo.name)
        return '-'
    combo_link.short_description = 'Combo'
    
    def discount_display(self, obj):
        """Display calculated discount amount"""
        if obj.original_price and obj.discount_percent:
            discount_amount = (obj.original_price * obj.discount_percent) / 100
            return format_html(
                'Rs. {:.2f} ({}%)',
                discount_amount,
                obj.discount_percent
            )
        return '-'
    discount_display.short_description = 'Discount Amount'
    
    def combo_items_display(self, obj):
        """Display combo items in a readable format"""
        if obj.is_combo_parent and obj.combo:
            child_items = obj.combo_items.all()
            if child_items:
                items_html = '<ul>'
                for item in child_items:
                    items_html += f'<li>{item.product_name} (Qty: {item.quantity}) - Rs. {item.price}</li>'
                items_html += '</ul>'
                return format_html(items_html)
        return '-'
    combo_items_display.short_description = 'Combo Items'
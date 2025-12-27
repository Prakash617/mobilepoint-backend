from django.contrib import admin
from .models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['added_at', 'price_when_added']
    fields = ['product_variant', 'notes', 'price_when_added', 'notify_on_price_drop', 'notify_on_stock', 'added_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WishlistItemInline]
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items Count'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product_variant', 'price_when_added', 'is_price_dropped', 'is_in_stock', 'added_at']
    list_filter = ['notify_on_price_drop', 'notify_on_stock', 'added_at']
    search_fields = ['wishlist__user__username', 'product_variant__name']
    readonly_fields = ['added_at', 'price_when_added']
    
    def is_price_dropped(self, obj):
        return obj.is_price_dropped()
    is_price_dropped.boolean = True
    is_price_dropped.short_description = 'Price Dropped'
    
    def is_in_stock(self, obj):
        return obj.is_in_stock()
    is_in_stock.boolean = True
    is_in_stock.short_description = 'In Stock'
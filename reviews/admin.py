from django.contrib import admin
from .models import ProductReview

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'user',
        'rating',
        'title',
        'is_approved',
        'created_at',
    )
    list_filter = ('rating', 'is_approved', 'created_at', 'updated_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_approved',)  # Quickly approve/disapprove from list view
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('product', 'user', 'rating', 'title', 'comment', 'image')
        }),
        ('Moderation', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

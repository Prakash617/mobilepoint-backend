from django.contrib import admin
from .models import ProductReview
from django.utils.html import format_html
from django.urls import reverse

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'user',
        'rating',
        'title',
        'is_approved',
        'created_at',
        'action_buttons',
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
    
    def action_buttons(self, obj):
        edit_url = reverse('admin:reviews_productreview_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="padding:4px 10px; background-color:#28A745; color:white; '
            'border-radius:5px; text-decoration:none; margin-right:5px; font-weight:bold;">Edit</a>',
            edit_url
        )
    action_buttons.short_description = 'Actions'

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"{self.user.username}'s Wishlist"

    def items_count(self):
        return self.items.count()


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('product.ProductVariant', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    # Price tracking
    price_when_added = models.DecimalField(max_digits=10, decimal_places=2)
    notify_on_price_drop = models.BooleanField(default=False)
    notify_on_stock = models.BooleanField(default=True)

    class Meta:
        unique_together = ('wishlist', 'product_variant')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['wishlist', '-added_at']),
            models.Index(fields=['product_variant']),
        ]
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.wishlist.user.username} - {self.product_variant}"

    def clean(self):
        if self.pk is None:
            if WishlistItem.objects.filter(
                wishlist=self.wishlist,
                product_variant=self.product_variant
            ).exists():
                from django.core.exceptions import ValidationError
                raise ValidationError('This item is already in your wishlist.')

    def save(self, *args, **kwargs):
        if not self.price_when_added:
            self.price_when_added = self.product_variant.price
        super().save(*args, **kwargs)

    def get_price_difference(self):
        current_price = self.product_variant.price
        return current_price - self.price_when_added

    def is_price_dropped(self):
        return self.get_price_difference() < 0

    def is_in_stock(self):
        return self.product_variant.stock > 0

from django.db import models
from django.conf import settings

class ProductReview(models.Model):
    """Customer reviews for products"""
    product = models.ForeignKey(
        'product.product', 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='product_reviews'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], 
        help_text="Rating from 1 (worst) to 5 (best)"
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='reviews/', null=True, blank=True)

    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Review"
        ordering = ['-created_at']
        unique_together = ('product', 'user')
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product rating whenever a review is created or updated
        if self.product:
            self.product.update_rating()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        if product:
            product.update_rating()

    def __str__(self):
        if self.title:
            return f"{self.product.name} - {self.title}"
        return f"{self.product.name} - {self.rating} Stars"

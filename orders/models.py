# orders/models.py
from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=100, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    # Shipping Information
    shipping_name = models.CharField(max_length=200)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_zip = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)

    # Billing Information
    billing_name = models.CharField(max_length=200)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_zip = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)

    # Additional Info
    notes = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=200, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('product.ProductVariant', on_delete=models.PROTECT)

    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100)

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.product_name} - {self.variant_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"

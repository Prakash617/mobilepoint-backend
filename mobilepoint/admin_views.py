from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
from product.models import Product, ProductVariant, Category, Brand
from orders.models import Order, OrderItem
from accounts.models import User
from reviews.models import ProductReview
from wishlist.models import Wishlist, WishlistItem

@staff_member_required
def filehub_embed(request):
    return render(request, "filehub_embed.html")


@staff_member_required
def analytic_dashboard(request):
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Previous period for comparison
    previous_start_date = start_date - timedelta(days=days)
    previous_end_date = start_date
    
    # Total Revenue
    current_revenue = Order.objects.filter(
        created_at__gte=start_date,
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    previous_revenue = Order.objects.filter(
        created_at__gte=previous_start_date,
        created_at__lt=previous_end_date,
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    revenue_change = calculate_percentage_change(current_revenue, previous_revenue)
    
    # Total Orders
    current_orders = Order.objects.filter(created_at__gte=start_date).count()
    previous_orders = Order.objects.filter(
        created_at__gte=previous_start_date,
        created_at__lt=previous_end_date
    ).count()
    orders_change = calculate_percentage_change(current_orders, previous_orders)
    
    # Average Order Value
    avg_order_value = current_revenue / current_orders if current_orders > 0 else Decimal('0')
    previous_avg = previous_revenue / previous_orders if previous_orders > 0 else Decimal('0')
    avg_change = calculate_percentage_change(avg_order_value, previous_avg)
    
    # Total Products
    total_products = Product.objects.filter(is_active=True).count()
    total_variants = ProductVariant.objects.filter(is_active=True).count()
    low_stock_count = ProductVariant.objects.filter(
        is_active=True,
        stock_quantity__gt=0,
        stock_quantity__lte=F('low_stock_threshold')
    ).count()
    out_of_stock_count = ProductVariant.objects.filter(is_active=True, stock_quantity=0).count()
    
    # Order Status Distribution
    order_statuses = Order.objects.filter(created_at__gte=start_date).values('order_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Convert order_statuses to list of dicts for JSON
    order_statuses_list = list(order_statuses)
    
    # Revenue by Day (for chart)
    daily_revenue = Order.objects.filter(
        created_at__gte=start_date,
        payment_status='paid'
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total'),
        orders=Count('id')
    ).order_by('date')
    
    # Convert daily_revenue to list with serializable data
    daily_revenue_list = [
        {
            'date': item['date'].isoformat(),
            'revenue': float(item['revenue']) if item['revenue'] else 0,
            'orders': item['orders']
        }
        for item in daily_revenue
    ]
    
    # Top Selling Products
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__payment_status='paid'
    ).values(
        'product_name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:10]
    
    # Category Performance
    category_performance = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__payment_status='paid'
    ).values(
        'product_variant__product__category__name'
    ).annotate(
        revenue=Sum('subtotal'),
        quantity=Sum('quantity')
    ).order_by('-revenue')[:5]
    
    # Brand Performance
    brand_performance = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__payment_status='paid'
    ).values(
        'product_variant__product__brand__name'
    ).annotate(
        revenue=Sum('subtotal'),
        quantity=Sum('quantity')
    ).order_by('-revenue')[:5]
    
    # Customer Stats
    total_customers = User.objects.filter(is_active=True).count()
    new_customers = User.objects.filter(
        date_joined__gte=start_date
    ).count() if hasattr(User, 'date_joined') else 0
    
    # Reviews Stats
    total_reviews = ProductReview.objects.filter(created_at__gte=start_date).count()
    avg_rating = ProductReview.objects.filter(
        created_at__gte=start_date,
        is_approved=True
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    pending_reviews = ProductReview.objects.filter(is_approved=False).count()
    
    # Wishlist Stats
    wishlist_items_count = WishlistItem.objects.filter(added_at__gte=start_date).count()
    most_wishlisted = WishlistItem.objects.values(
        'product_variant__product__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Recent Orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'days': days,
        'current_revenue': current_revenue,
        'revenue_change': revenue_change,
        'current_orders': current_orders,
        'orders_change': orders_change,
        'avg_order_value': avg_order_value,
        'avg_change': avg_change,
        'total_products': total_products,
        'total_variants': total_variants,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'order_statuses': json.dumps(order_statuses_list),
        'daily_revenue': json.dumps(daily_revenue_list),
        'top_products': top_products,
        'category_performance': category_performance,
        'brand_performance': brand_performance,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 2),
        'pending_reviews': pending_reviews,
        'wishlist_items_count': wishlist_items_count,
        'most_wishlisted': most_wishlisted,
        'recent_orders': recent_orders,
    }
    
    return render(request, "admin/analytics_dashboard_iframe.html", context)


def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    try:
        current = Decimal(str(current))
        previous = Decimal(str(previous))
        change = ((current - previous) / previous) * 100
        return round(float(change), 1)
    except:
        return 0
    
    
def custompage(request):
    return render(request, 'admin/custompage.html')
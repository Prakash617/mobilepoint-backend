
from django.urls import path, include
from mobilepoint.urls import router
from .api_views import OrderViewSet, OrderItemViewSet, OrderStatusHistoryViewSet


router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'order-history', OrderStatusHistoryViewSet, basename='orderhistory')


app_name = 'orders'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
]
from django.urls import path, include
from mobilepoint.urls import router
from .api_views import WishlistViewSet, WishlistItemViewSet

router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'wishlist-items', WishlistItemViewSet, basename='wishlistitem')



app_name = 'wishlist'

urlpatterns = [
    path('api/', include(router.urls)),
]
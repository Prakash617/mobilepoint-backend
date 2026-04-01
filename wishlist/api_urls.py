from django.urls import path
from mobilepoint.urls import router
from .api_views import WishlistViewSet, WishlistItemViewSet

router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'wishlist-items', WishlistItemViewSet, basename='wishlistitem')



app_name = 'wishlist'

urlpatterns = [
    # Router endpoints are exposed once via mobilepoint/urls.py -> /api/
]
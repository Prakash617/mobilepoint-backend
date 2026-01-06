# products/urls.py

from django.urls import path, include
from mobilepoint.urls import router
from .api_views import CategoryViewSet, BrandViewSet, ProductViewSet, ProductVariantViewSet,DealViewSet ,RecentlyViewedProductViewSet
from .views import get_categories_by_brand


router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'recently-viewed', RecentlyViewedProductViewSet, basename='recently-viewed')


app_name = 'product'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    path('filter-categories/', get_categories_by_brand, name='get_categories_by_brand'),
]
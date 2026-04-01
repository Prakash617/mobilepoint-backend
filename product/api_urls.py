# products/urls.py

from django.urls import path, include
from mobilepoint.urls import router
from .api_views import (
    CategoryViewSet, BrandViewSet, ProductViewSet, ProductVariantViewSet,
    DealViewSet, RecentlyViewedProductViewSet,
    ProductComboViewSet, PromotionViewSet
)
from .views import get_categories_by_brand


router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'recently-viewed', RecentlyViewedProductViewSet, basename='recently-viewed')
router.register(r'combos', ProductComboViewSet, basename='combo')
router.register(r'promotions', PromotionViewSet, basename='promotion')


app_name = 'product'

urlpatterns = [
    # Router endpoints are exposed once via mobilepoint/urls.py -> /api/
    path('filter-categories/', get_categories_by_brand, name='get_categories_by_brand'),
]
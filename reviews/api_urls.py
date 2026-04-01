# products/urls.py

from django.urls import path
from mobilepoint.urls import router
from .api_views import ProductReviewViewSet


router.register(r'reviews', ProductReviewViewSet, basename='productreview')



app_name = 'reviews'

urlpatterns = [
    # Router endpoints are exposed once via mobilepoint/urls.py -> /api/
]
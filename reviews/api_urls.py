# products/urls.py

from django.urls import path, include
from mobilepoint.urls import router
from .api_views import ProductReviewViewSet


router.register(r'reviews', ProductReviewViewSet, basename='productreview')



app_name = 'reviews'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
]
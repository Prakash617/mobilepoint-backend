"""
URL configuration for mobilepoint project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from product.api_views import ProductRelatedPublicView
from accounts.api_views import (
    HiddenTokenObtainPairView,
    HiddenTokenRefreshView,
    HiddenTokenVerifyView,
)
from .admin_views import filehub_embed, analytic_dashboard, custompage
from .admin_site import secure_admin_site
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
router = DefaultRouter()
# Copy all existing registered models
secure_admin_site._registry = admin.site._registry

urlpatterns = [
    path('admin/', include('filehub.urls')),
    path('admin/custompage/', custompage, name='custom_page'),
    path("filemanager/", filehub_embed, name="admin_filehub"),
    path('api/auth/', include('accounts.api_urls')),
    path("analytic_dashboard/", analytic_dashboard, name="analytic_dashboard"),
    # path('admin/', admin.site.urls),
    path("admin/", secure_admin_site.urls),
    path('product/', include('product.api_urls')),
    # Direct route for frontend-friendly related products URL
    path('products/<slug:slug>/related/', ProductRelatedPublicView.as_view({'get': 'related'}), name='product-related'),
    path('orders/', include('orders.api_urls')),
    path('wishlist/', include('wishlist.api_urls')),
    path('website/', include('website.api_urls')),
    path('reviews/', include('reviews.api_urls')),
    path('menu/', include('menu.api_urls')),
    
     # ------------------jwt------------
    path('api/token/', HiddenTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', HiddenTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', HiddenTokenVerifyView.as_view(), name='token_verify'),
    path('api/', include(router.urls)),
    path('tinymce/', include('tinymce.urls')),
    # Optional: Django REST Framework browsable API authentication
    path('api-auth/', include('rest_framework.urls')),
    path('tinymce/', include('tinymce.urls')),
    
    
    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc UI (optional)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urls.py
from mobilepoint.urls import router

from .api_views import (
    MenuViewSet,
    MenuItemViewSet,
    PageViewSet
)


# Menu Management
router.register("menus", MenuViewSet, basename="menu")

# Menu Items
router.register("menu-items", MenuItemViewSet, basename="menu-item")
router.register('pages', PageViewSet, basename='page')

# app_name = 'menu'

urlpatterns = []
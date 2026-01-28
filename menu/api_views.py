from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_field, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from menu.models import Menu, MenuItem, Page
from .serializers import (
    MenuSerializer,
    MenuListSerializer,
    MenuCreateUpdateSerializer,
    MenuItemSerializer,
    MenuItemListSerializer,
    MenuItemCreateUpdateSerializer,
    PageSerializer
)


@extend_schema(tags=['Menus'])
class MenuViewSet(viewsets.ModelViewSet):
    """
    API for managing menus and their configuration.
    
    Menus are containers for menu items organized by location (header, footer, sidebar).
    They define where navigation items appear in the application.
    """
    queryset = Menu.objects.all().prefetch_related('items')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'location']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MenuListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MenuCreateUpdateSerializer
        return MenuSerializer
    
    def get_permissions(self):
        """Admin only for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]
    
    @extend_schema(
        operation_id='menus_by_location',
        parameters=[
            OpenApiParameter(
                name='location',
                description='Menu location (header, footer, or sidebar)',
                required=True,
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample('header', value='header'),
                    OpenApiExample('footer', value='footer'),
                    OpenApiExample('sidebar', value='sidebar'),
                ]
            ),
        ],
        responses={200: MenuSerializer(many=True)},
        description='Retrieve menus for a specific location (header, footer, or sidebar). Returns only active menus.'
    )
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """
        Get menus grouped by location
        GET /api/menus/by_location/?location=name_of_location
        """
        location = request.query_params.get('location')
        
        if not location:
            return Response(
                {'error': 'Location parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        menus = Menu.objects.filter(location=location, is_active=True)
        serializer = MenuSerializer(menus, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='menus_toggle_active',
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description='Toggle the active status of a menu. Admin only.'
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle menu active status
        POST /api/menus/{id}/toggle_active/
        """
        menu = self.get_object()
        menu.is_active = not menu.is_active
        menu.save()
        
        return Response({
            'message': f"Menu '{menu.name}' is now {'active' if menu.is_active else 'inactive'}",
            'is_active': menu.is_active
        })
    
    @extend_schema(
        operation_id='menus_items_tree',
        responses={200: MenuItemSerializer(many=True)},
        description='Get menu items in hierarchical tree structure with parent-child relationships.'
    )
    @action(detail=True, methods=['get'])
    def items_tree(self, request, pk=None):
        """
        Get menu items in tree structure
        GET /api/menus/{id}/items_tree/
        """
        menu = self.get_object()
        top_level_items = menu.items.filter(parent=None, is_active=True)
        serializer = MenuItemSerializer(top_level_items, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='menus_locations',
        responses={200: OpenApiTypes.OBJECT},
        description='List all available menu locations (header, footer, sidebar) with their labels.'
    )
    @action(detail=False, methods=['get'])
    def locations(self, request):
        """
        Get all available menu locations
        GET /api/menus/locations/
        """
        locations = [
            {'value': choice[0], 'label': choice[1]}
            for choice in Menu.MENU_LOCATION_CHOICES
        ]
        return Response(locations)
    
    @extend_schema(
        operation_id='menus_statistics',
        responses={200: OpenApiTypes.OBJECT},
        description='Get aggregated statistics about menus including counts by location and active status.'
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get menu statistics
        GET /api/menus/statistics/
        """
        stats = {
            'total_menus': Menu.objects.count(),
            'active_menus': Menu.objects.filter(is_active=True).count(),
            'total_items': MenuItem.objects.count(),
            'active_items': MenuItem.objects.filter(is_active=True).count(),
            'by_location': {}
        }
        
        for location, label in Menu.MENU_LOCATION_CHOICES:
            stats['by_location'][location] = {
                'label': label,
                'count': Menu.objects.filter(location=location).count(),
                'active': Menu.objects.filter(location=location, is_active=True).count()
            }
        
        return Response(stats)


@extend_schema(tags=['Menu Items'])
class MenuItemViewSet(viewsets.ModelViewSet):
    """
    API for managing individual menu items within menus.
    
    Menu items are links and navigation entries that appear in menus.
    They support hierarchical organization with parent-child relationships
    and can link to internal pages or external URLs.
    """
    queryset = MenuItem.objects.all().select_related('menu', 'parent')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['menu', 'parent', 'is_active', 'is_external', 'open_new_tab']
    search_fields = ['label_en', 'label_np', 'url']
    ordering_fields = ['order', 'created_at', 'label_en']
    ordering = ['order']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MenuItemListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MenuItemCreateUpdateSerializer
        return MenuItemSerializer
    
    def get_permissions(self):
        """Admin only for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]
    
    @extend_schema(
        operation_id='menu_items_by_menu',
        parameters=[
            OpenApiParameter(
                name='menu_id',
                description='The ID of the menu to filter items by',
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={200: MenuItemListSerializer(many=True)},
        description='Get all active menu items belonging to a specific menu.'
    )
    @action(detail=False, methods=['get'])
    def by_menu(self, request):
        """
        Get menu items by menu ID
        GET /api/menu-items/by_menu/?menu_id=1
        """
        menu_id = request.query_params.get('menu_id')
        
        if not menu_id:
            return Response(
                {'error': 'menu_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = MenuItem.objects.filter(menu_id=menu_id, is_active=True)
        serializer = MenuItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='menu_items_top_level',
        parameters=[
            OpenApiParameter(
                name='menu_id',
                description='Optional: Filter by menu ID. If not provided, returns top-level items from all menus.',
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={200: MenuItemSerializer(many=True)},
        description='Get only top-level menu items (those without a parent). These are typically the main navigation entries.'
    )
    @action(detail=False, methods=['get'])
    def top_level(self, request):
        """
        Get only top-level menu items (parent=None)
        GET /api/menu-items/top_level/?menu_id=1
        """
        menu_id = request.query_params.get('menu_id')
        
        queryset = MenuItem.objects.filter(parent=None, is_active=True)
        
        if menu_id:
            queryset = queryset.filter(menu_id=menu_id)
        
        serializer = MenuItemSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='menu_items_children',
        responses={200: MenuItemSerializer(many=True)},
        description='Get all child items of a specific menu item. Returns items in hierarchical structure.'
    )
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        Get children of a specific menu item
        GET /api/menu-items/{id}/children/
        """
        menu_item = self.get_object()
        children = menu_item.children.filter(is_active=True)
        serializer = MenuItemSerializer(children, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='menu_items_toggle_active',
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description='Toggle the active status of a menu item. Admin only.'
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle menu item active status
        POST /api/menu-items/{id}/toggle_active/
        """
        item = self.get_object()
        item.is_active = not item.is_active
        item.save()
        
        return Response({
            'message': f"Menu item '{item.label_en}' is now {'active' if item.is_active else 'inactive'}",
            'is_active': item.is_active
        })
    
    @extend_schema(
        operation_id='menu_items_reorder',
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description='Reorder menu items by providing a list of item IDs with their new order values. Admin only.',
        examples=[
            OpenApiExample(
                'Request Body',
                value={'items': [{'id': 1, 'order': 0}, {'id': 2, 'order': 1}]},
                request_only=True
            ),
        ]
    )
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder menu items
        POST /api/menu-items/reorder/
        Body: {"items": [{"id": 1, "order": 0}, {"id": 2, "order": 1}]}
        """
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response(
                {'error': 'items array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = 0
        for item_data in items_data:
            item_id = item_data.get('id')
            order = item_data.get('order')
            
            if item_id is not None and order is not None:
                MenuItem.objects.filter(id=item_id).update(order=order)
                updated_count += 1
        
        return Response({
            'message': f'{updated_count} menu items reordered successfully',
            'updated_count': updated_count
        })
    
    @extend_schema(
        operation_id='menu_items_duplicate',
        request=None,
        responses={201: MenuItemSerializer},
        description='Create a duplicate of a menu item with "(Copy)" appended to the label. The duplicate is created as inactive. Admin only.'
    )
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a menu item
        POST /api/menu-items/{id}/duplicate/
        """
        original = self.get_object()
        
        # Create duplicate
        duplicate = MenuItem.objects.create(
            menu=original.menu,
            parent=original.parent,
            label_en=f"{original.label_en} (Copy)",
            label_np=original.label_np,
            url=original.url,
            order=original.order + 1,
            icon=original.icon,
            is_external=original.is_external,
            open_new_tab=original.open_new_tab,
            is_active=False  # Set inactive by default
        )
        
        serializer = MenuItemSerializer(duplicate)
        return Response({
            'message': 'Menu item duplicated successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='menu_items_bulk_delete',
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description='Delete multiple menu items at once. Provide a list of item IDs. Admin only.',
        examples=[
            OpenApiExample(
                'Request Body',
                value={'ids': [1, 2, 3]},
                request_only=True
            ),
        ]
    )
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Delete multiple menu items
        DELETE /api/menu-items/bulk_delete/
        Body: {"ids": [1, 2, 3]}
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response(
                {'error': 'ids array is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = MenuItem.objects.filter(id__in=ids).delete()
        
        return Response({
            'message': f'{deleted_count} menu items deleted successfully',
            'deleted_count': deleted_count
        })
        

@extend_schema(tags=['Pages'])
class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for retrieving published pages.
    
    Pages are dynamic content pages that can be linked from menus.
    This is a read-only API - only published pages are visible to the public.
    """
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [AllowAny]  # public API
    lookup_field = "slug"  # access page by slug in URL

    # Optional: filter only published pages
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(status="published")

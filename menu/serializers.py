# serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from menu.models import Menu, MenuItem, Page


class MenuItemSerializer(serializers.ModelSerializer):
    """
    Full serializer for MenuItem with hierarchical children support.
    
    Used for displaying complete menu item structure with all child items
    recursively included. Includes nested children property for tree representation.
    """
    children = serializers.SerializerMethodField(
        help_text="Nested child menu items (recursive)"
    )
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'menu',
            'parent',
            'label_en',
            'label_np',
            'title',
            'sub_title',
            'url',
            'order',
            'icon',
            'is_external',
            'open_new_tab',
            'is_active',
            'created_at',
            'children',
        ]
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_children(self, obj) -> list[dict]:
        """Get child menu items recursively"""
        if obj.children.exists():
            return MenuItemSerializer(
                obj.children.filter(is_active=True),
                many=True,
                context=self.context
            ).data
        return []


class MenuItemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating menu items.
    
    Validates parent-child relationships and prevents circular references.
    Automatically fills URL from linked page if not explicitly provided.
    """
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'menu',
            'parent',
            'label_en',
            'label_np',
            'title',
            'sub_title',
            'url',
            'order',
            'icon',
            'is_external',
            'open_new_tab',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def validate_parent(self, value):
        """Ensure parent belongs to the same menu"""
        if value and self.instance:
            if value.menu != self.instance.menu:
                raise serializers.ValidationError(
                    "Parent menu item must belong to the same menu."
                )
        return value
    
    def validate(self, attrs):
        """Additional validation"""
        # Prevent circular references
        if attrs.get('parent') and self.instance:
            parent = attrs['parent']
            current = parent
            while current:
                if current == self.instance:
                    raise serializers.ValidationError({
                        "parent": "Cannot create circular reference in menu hierarchy."
                    })
                current = current.parent
        
        return attrs


class MenuItemListSerializer(serializers.ModelSerializer):
    """
    Simple serializer for listing menu items without children.
    
    Includes denormalized parent and menu information for easier consumption.
    Used in list endpoints for performance and simplicity.
    """
    parent_label = serializers.CharField(source='parent.label_en', read_only=True, help_text="Label of parent menu item")
    menu_name = serializers.CharField(source='menu.name', read_only=True, help_text="Name of parent menu")
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'menu',
            'menu_name',
            'parent',
            'parent_label',
            'label_en',
            'label_np',
            'title',
            'sub_title',
            'url',
            'order',
            'icon',
            'is_external',
            'open_new_tab',
            'is_active',
            'created_at',
        ]


class MenuSerializer(serializers.ModelSerializer):
    """Serializer for Menu with nested items"""
    items = serializers.SerializerMethodField(
        help_text="Top-level menu items with their children in hierarchical structure"
    )
    items_count = serializers.SerializerMethodField(
        help_text="Total count of all menu items (including inactive)"
    )
    
    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'location',
            'is_active',
            'created_at',
            'updated_at',
            'items',
            'items_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_items(self, obj) -> list[dict]:
        """Get only top-level menu items (parent=None) with their children"""
        top_level_items = obj.items.filter(parent=None, is_active=True)
        return MenuItemSerializer(top_level_items, many=True, context=self.context).data
    
    def get_items_count(self, obj) -> int:
        """Get total count of menu items"""
        return obj.items.count()


class MenuListSerializer(serializers.ModelSerializer):
    """Simple serializer for listing menus"""
    items_count = serializers.SerializerMethodField(
        help_text="Total count of menu items"
    )
    
    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'location',
            'is_active',
            'items_count',
            'created_at',
            'updated_at',
        ]
    
    def get_items_count(self, obj) -> int:
        return obj.items.count()


class MenuCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating menus"""
    
    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'location',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def validate_name(self, value):
        """Ensure unique menu name per location"""
        location = self.initial_data.get('location') or (
            self.instance.location if self.instance else None
        )
        
        queryset = Menu.objects.filter(name=value, location=location)
        
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                f"A menu with this name already exists in the '{location}' location."
            )
        
        return value


class PageSerializer(serializers.ModelSerializer):
    """
    Serializer for published Page content.
    
    Used for displaying dynamic pages that can be linked from menus.
    Only returns published pages. Pages can be accessed by their slug.
    """
    is_published = serializers.BooleanField(
        read_only=True,
        help_text="Indicates if page status is 'published'"
    )
    class Meta:
        model = Page
        fields = [
            "id",
            "title",
            "slug",
            "meta_description",
            "content",
            "excerpt",
            "featured_image",
            "seo_title",
            "keywords",
            "status",
            "published_at",
            "created_at",
            "updated_at",
            "is_published",
        ]
        read_only_fields = ["created_at", "updated_at", "is_published"]

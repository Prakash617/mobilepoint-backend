from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from .models import Wishlist, WishlistItem
from .serializers import (
    WishlistSerializer, WishlistItemSerializer, 
    WishlistItemCreateSerializer
)



class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).prefetch_related(
            'items__product_variant__product'
        )
    
    def get_object(self):
        """Get or create wishlist for current user"""
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist
    
    def list(self, request, *args, **kwargs):
        """Get current user's wishlist"""
        wishlist = self.get_object()
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Not allowed - wishlist is auto-created"""
        return Response(
            {'detail': 'Wishlist is automatically created for each user'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from wishlist"""
        wishlist = self.get_object()
        deleted_count = wishlist.items.count()
        wishlist.items.all().delete()
        
        return Response({
            'message': f'Removed {deleted_count} items from wishlist',
            'items_deleted': deleted_count
        })
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Get wishlist items count"""
        wishlist = self.get_object()
        return Response({
            'count': wishlist.items.count()
        })
    
    @action(detail=False, methods=['get'])
    def price_drops(self, request):
        """Get items with price drops"""
        wishlist = self.get_object()
        items = [item for item in wishlist.items.all() if item.is_price_dropped()]
        serializer = WishlistItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get out of stock items"""
        wishlist = self.get_object()
        items = [item for item in wishlist.items.all() if not item.is_in_stock()]
        serializer = WishlistItemSerializer(items, many=True)
        return Response(serializer.data)


class WishlistItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['product_variant__name', 'product_variant__product__name', 'notes']
    ordering_fields = ['added_at', 'price_when_added']
    ordering = ['-added_at']
    
    def get_queryset(self):
        wishlist = Wishlist.objects.get_or_create(user=self.request.user)[0]
        return WishlistItem.objects.filter(wishlist=wishlist).select_related(
            'product_variant__product'
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WishlistItemCreateSerializer
        return WishlistItemSerializer
    
    def create(self, request, *args, **kwargs):
        """Add item to wishlist"""
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_variant = serializer.validated_data['product_variant']
        
        # Check if item already exists
        if WishlistItem.objects.filter(
            wishlist=wishlist, 
            product_variant=product_variant
        ).exists():
            return Response(
                {'detail': 'This item is already in your wishlist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wishlist_item = serializer.save(wishlist=wishlist)
        
        output_serializer = WishlistItemSerializer(wishlist_item)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Remove item from wishlist"""
        instance = self.get_object()
        product_name = instance.product_variant.name
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Removed {product_name} from wishlist'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def move_to_cart(self, request, pk=None):
        """Move item from wishlist to cart"""
        item = self.get_object()
        
        # Here you would implement your cart logic
        # For now, just return success message
        # You can integrate with your cart system
        
        return Response({
            'message': f'Added {item.product_variant.name} to cart',
            'product_variant_id': item.product_variant.id
        })
    
    @action(detail=True, methods=['patch'])
    def toggle_price_notification(self, request, pk=None):
        """Toggle price drop notification"""
        item = self.get_object()
        item.notify_on_price_drop = not item.notify_on_price_drop
        item.save()
        
        return Response({
            'notify_on_price_drop': item.notify_on_price_drop
        })
    
    @action(detail=True, methods=['patch'])
    def toggle_stock_notification(self, request, pk=None):
        """Toggle stock notification"""
        item = self.get_object()
        item.notify_on_stock = not item.notify_on_stock
        item.save()
        
        return Response({
            'notify_on_stock': item.notify_on_stock
        })
    
    @action(detail=False, methods=['post'])
    def bulk_add(self, request):
        """Add multiple items to wishlist"""
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        product_variant_ids = request.data.get('product_variants', [])
        
        if not product_variant_ids:
            return Response(
                {'detail': 'No product variants provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        added_items = []
        skipped_items = []
        
        for variant_id in product_variant_ids:
            try:
                from products.models import ProductVariant
                variant = ProductVariant.objects.get(id=variant_id)
                
                item, created = WishlistItem.objects.get_or_create(
                    wishlist=wishlist,
                    product_variant=variant
                )
                
                if created:
                    added_items.append(variant.name)
                else:
                    skipped_items.append(variant.name)
            except:
                pass
        
        return Response({
            'added': len(added_items),
            'skipped': len(skipped_items),
            'added_items': added_items,
            'skipped_items': skipped_items
        })
    
    @action(detail=False, methods=['post'])
    def bulk_remove(self, request):
        """Remove multiple items from wishlist"""
        item_ids = request.data.get('item_ids', [])
        
        if not item_ids:
            return Response(
                {'detail': 'No item IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = self.get_queryset().filter(id__in=item_ids).delete()[0]
        
        return Response({
            'message': f'Removed {deleted_count} items from wishlist',
            'deleted_count': deleted_count
        })

# orders/api_views.py
"""
Order Management API Views

Provides comprehensive REST API endpoints for:
- Creating and managing orders
- Tracking order items
- Managing order status history
- Filtering, searching, and sorting orders

Authentication: Required (IsAuthenticated)
- Staff users can view all orders
- Regular users can only view their own orders
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderStatusHistorySerializer
)


@extend_schema_view(
    list=extend_schema(
        summary='List all orders',
        description='Get a list of orders. Staff can see all orders, users see only their own.',
        parameters=[
            OpenApiParameter(
                name='order_status',
                description='Filter by order status',
                required=False,
                type=OpenApiTypes.STR,
                enum=['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
            ),
            OpenApiParameter(
                name='payment_status',
                description='Filter by payment status',
                required=False,
                type=OpenApiTypes.STR,
                enum=['pending', 'paid', 'failed', 'refunded']
            ),
            OpenApiParameter(
                name='search',
                description='Search by order number, email, or shipping name',
                required=False,
                type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name='ordering',
                description='Order by created_at, total, or order_status (prefix with - for descending)',
                required=False,
                type=OpenApiTypes.STR
            ),
        ],
        tags=['Orders']
    ),
    create=extend_schema(
        summary='Create a new order',
        description='Create a new order with items, shipping, and billing information.',
        tags=['Orders']
    ),
    retrieve=extend_schema(
        summary='Get order details',
        description='Get full details of a specific order including items and status history.',
        tags=['Orders']
    ),
    update=extend_schema(
        summary='Update order',
        description='Update order shipping and billing information.',
        tags=['Orders']
    ),
    partial_update=extend_schema(
        summary='Partially update order',
        description='Partially update order fields.',
        tags=['Orders']
    ),
    destroy=extend_schema(
        summary='Delete order',
        description='Delete an order (typically used for cancellation).',
        tags=['Orders']
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    
    Provides the following actions:
    - list: Get all orders (staff see all, users see their own)
    - create: Create a new order
    - retrieve: Get order details
    - update/partial_update: Update order information
    - destroy: Cancel an order
    - update_status: Change order status with history tracking
    - update_payment_status: Update payment status
    - add_tracking: Add tracking number
    - cancel: Cancel an order
    - my_orders: Get current user's orders
    - statistics: Get order statistics
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['order_status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'shipping_email', 'shipping_name']
    ordering_fields = ['created_at', 'total', 'order_status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().select_related('user').prefetch_related('items', 'status_history')
        return Order.objects.filter(user=user).select_related('user').prefetch_related('items', 'status_history')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @extend_schema(
        summary='Update order status',
        description='Update the order status and create a history entry.',
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                'Update to shipped',
                value={
                    'order_status': 'shipped',
                    'notes': 'Package has been dispatched'
                }
            )
        ],
        tags=['Orders']
    )
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status and create history entry.
        
        Request body:
        {
            "order_status": "confirmed|processing|shipped|delivered|cancelled|refunded",
            "notes": "Optional notes about the status change"
        }
        """
        order = self.get_object()
        new_status = request.data.get('order_status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.order_status = new_status
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            created_by=request.user
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Update payment status',
        description='Update the payment status of an order.',
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                'Mark as paid',
                value={'payment_status': 'paid'}
            )
        ],
        tags=['Orders']
    )
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        """
        Update payment status.
        
        Request body:
        {
            "payment_status": "pending|paid|failed|refunded"
        }
        """
        order = self.get_object()
        new_status = request.data.get('payment_status')
        
        if new_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid payment status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.payment_status = new_status
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Add tracking number',
        description='Add or update the tracking number for an order.',
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                'FedEx tracking',
                value={'tracking_number': 'FDX123456789'}
            )
        ],
        tags=['Orders']
    )
    @action(detail=True, methods=['post'])
    def add_tracking(self, request, pk=None):
        """
        Add tracking number to order.
        
        Request body:
        {
            "tracking_number": "string"
        }
        """
        order = self.get_object()
        tracking_number = request.data.get('tracking_number')
        
        if not tracking_number:
            return Response(
                {'error': 'Tracking number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.tracking_number = tracking_number
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Cancel an order',
        description='Cancel an order if it has not been shipped or delivered yet.',
        tags=['Orders']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Cancel an order.
        
        Cannot cancel orders that have already been shipped or delivered.
        """
        order = self.get_object()
        
        if order.status in ['shipped', 'delivered']:
            return Response(
                {'error': 'Cannot cancel shipped or delivered orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            notes=request.data.get('notes', 'Order cancelled by user'),
            created_by=request.user
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Get current user orders',
        description='Get a paginated list of the current authenticated user\'s orders.',
        tags=['Orders']
    )
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        Get current user's orders.
        
        Returns a paginated list of orders belonging to the authenticated user.
        """
        orders = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(orders)
        
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Get order statistics',
        description='Get counts of orders by status. Staff can see all statistics, users see only their own.',
        responses={
            200: OpenApiTypes.OBJECT
        },
        tags=['Orders']
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get order statistics.
        
        Returns counts of orders by status. Staff can see all statistics, users see only their own.
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_orders': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'confirmed': queryset.filter(status='confirmed').count(),
            'processing': queryset.filter(status='processing').count(),
            'shipped': queryset.filter(status='shipped').count(),
            'delivered': queryset.filter(status='delivered').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
        }
        
        return Response(stats)


@extend_schema_view(
    list=extend_schema(
        summary='List order items',
        description='Get a list of order items with filtering by order.',
        parameters=[
            OpenApiParameter(
                name='order',
                description='Filter by order ID',
                required=False,
                type=OpenApiTypes.INT
            ),
        ],
        tags=['Order Items']
    ),
    retrieve=extend_schema(
        summary='Get order item details',
        description='Get details of a specific order item.',
        tags=['Order Items']
    ),
)
class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing order items.
    
    Read-only access to order items with filtering by order.
    Staff can see all items, users can only see items from their own orders.
    """
    queryset = OrderItem.objects.all().select_related('order', 'product_variant', 'product')
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(order__user=user)


@extend_schema_view(
    list=extend_schema(
        summary='List order status history',
        description='Get order status history with filtering by order and status.',
        parameters=[
            OpenApiParameter(
                name='order',
                description='Filter by order ID',
                required=False,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='status',
                description='Filter by status value',
                required=False,
                type=OpenApiTypes.STR
            ),
        ],
        tags=['Order Status History']
    ),
    retrieve=extend_schema(
        summary='Get status history entry',
        description='Get details of a specific status history entry.',
        tags=['Order Status History']
    ),
)
class OrderStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing order status history.
    
    Read-only access to order status changes with filtering by order and status.
    Staff can see all history, users can only see history from their own orders.
    """
    queryset = OrderStatusHistory.objects.all().select_related('order', 'created_by')
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'status']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(order__user=user)

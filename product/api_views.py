from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Min, Max, Sum
from .models import (
    Category,
    Brand,
    Product,
    ProductImage,
    ProductVariant,
    VariantAttribute,
    VariantAttributeValue,
    Deal, 
    RecentlyViewedProduct
)
from .serializers import (
    CategorySerializer,
    BrandSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductVariantListSerializer,
    ProductVariantDetailSerializer,
    DealListSerializer,
    DealDetailSerializer,
    DealCreateUpdateSerializer,
    RecentlyViewedProductSerializer,
)
from .utils import add_recently_viewed
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from .filters import DealFilter


from django.db.models import Count, Case, When, IntegerField


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for categories
    """

    # queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]
    # /categories/?is_featured=true
    # /categories/?top=true&limit=6
    # /categories/

    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)

        # 🔹 Featured categories
        is_featured = self.request.query_params.get("is_featured")
        if is_featured == "true":
            queryset = queryset.filter(is_featured=True)[:10]

        # 🔹 Dynamic top categories by product count
        top = self.request.query_params.get("top")
        if top == "true":
            limit = self.request.query_params.get("limit", 8)
            queryset = (
                queryset.annotate(product_count=Count("products"))
                .filter(product_count__gt=0)
                .order_by("-product_count")[: int(limit)]
            )

        return queryset
    
    @action(detail=False, methods=['get'], url_path='grouped-sections')
    def grouped_sections(self, request):  # <--- Added 'request' here
        """
        Returns top-level categories with their subcategories.
        """
        top_categories = Category.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).prefetch_related('children')[:3]

        serializer = self.get_serializer(top_categories, many=True)
        return Response(serializer.data)
class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for brands
    """

    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products

    list: Get all products
    retrieve: Get a single product by slug
    search: Search products
    featured: Get featured products
    by_category: Get products by category
    by_brand: Get products by brand
    """

    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category", "brand")
        .prefetch_related("images", "variants")
    )
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "brand", "is_featured"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "base_price"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get a single product by slug.
        Also track recently viewed products for logged-in users.
        """
        product = self.get_object()  # fetch product by slug

        # Track recently viewed
        if request.user.is_authenticated:
            add_recently_viewed(request.user, product)

        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured products"""
        featured_products = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], url_path="category/(?P<category_slug>[^/.]+)"
    )
    def by_category(self, request, category_slug=None):
        """Get products by category slug"""
        products = self.get_queryset().filter(category__slug=category_slug)

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def curated(self, request):
        """Curated products for the logged-in user"""
        user = request.user
        if user.is_authenticated:
            profile = user
            qs = (
                self.get_queryset()
                .filter(category__in=profile.favorite_categories.all())
                .order_by("-is_featured", "-id")[:10]
            )
        else:
            # fallback for anonymous users
            qs = self.get_queryset().order_by("-is_featured", "-id")[:10]

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="brand/(?P<brand_slug>[^/.]+)")
    def by_brand(self, request, brand_slug=None):
        """Get products by brand slug"""
        products = self.get_queryset().filter(brand__slug=brand_slug)

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def best_seller(self, request):
        """Get dynamically calculated best seller products"""

        # Annotate products with total sold quantity from variants
        products_with_sales = (
            self.get_queryset()
            .annotate(total_sold=Sum("variants__sold_quantity"))
            .order_by("-total_sold")
        )  # highest sold first

        # Optional: limit top N
        top_sellers = products_with_sales[:10]

        serializer = self.get_serializer(top_sellers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def related(self, request, slug=None):
        """Get related products for a product (by category and brand)

        Query params:
        - limit: integer (optional, default=8)
        """
        product = self.get_object()

        # limit and safety cap
        try:
            limit = int(request.query_params.get("limit", 5))
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, 50))

        # base queryset: active products excluding the current one
        qs = (
            Product.objects.filter(is_active=True)
            .exclude(pk=product.pk)
            .select_related("category", "brand")
            .prefetch_related("images", "variants")
        )

        # related by same category or same brand
        related_q = Q(category=product.category) | Q(brand=product.brand)
        qs = qs.filter(related_q)

        # boost same-category items and order by feature/recent/sales
        qs = qs.annotate(
            same_category=Case(When(category=product.category, then=1), default=0, output_field=IntegerField()),
            min_price=Min("variants__price"),
            total_sold=Sum("variants__sold_quantity"),
        ).order_by("-same_category", "-is_featured", "-total_sold", "-created_at")[:limit]

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    
    @action(detail=False, methods=["get"])
    def top_phones_tablets(self, request):
        """
        Homepage: Top Cellphones & Tablets (combined)

        Query params:
        - limit: integer (optional, default=10)
        - category_limit: integer (optional, default=6)
        """

        limit = int(request.query_params.get("limit", 10))
        category_limit = int(request.query_params.get("category_limit", 6))

        PHONE_KEYWORDS = [
            "phone", "mobile", "smartphone", "cell", "iphone", "android"
        ]
        TABLET_KEYWORDS = [
            "tablet", "tab", "ipad", "pad"
        ]

        ALL_KEYWORDS = PHONE_KEYWORDS + TABLET_KEYWORDS

        # --------------------------------------------------
        # Build reusable category Q filter
        # --------------------------------------------------
        category_q = Q()
        for word in ALL_KEYWORDS:
            category_q |= (
                Q(category__name__icontains=word)
                | Q(category__slug__icontains=word)
                | Q(category__parent__name__icontains=word)
                | Q(category__parent__slug__icontains=word)
            )

        # --------------------------------------------------
        # Top Products (Phones + Tablets)
        # --------------------------------------------------
        products = (
            Product.objects
            .filter(is_active=True)
            .filter(category_q)
            .annotate(
                min_price=Min("variants__price"),
                total_sold=Sum("variants__sold_quantity"),
            )
            .order_by("-total_sold", "-is_featured", "-created_at")[:limit]
        )

        product_data = self.get_serializer(products, many=True).data

        # --------------------------------------------------
        # Top Categories (Phones + Tablets)
        # --------------------------------------------------
        # category_filter_q = Q()
        # for word in ALL_KEYWORDS:
        #     category_filter_q |= (
        #         Q(name__icontains=word)
        #         | Q(slug__icontains=word)
        #         | Q(parent__name__icontains=word)
        #         | Q(parent__slug__icontains=word)
        #     )

        # categories = (
        #     Category.objects
        #     .filter(is_active=True)                        # Only active categories
        #     .filter(parent__isnull=True)                  # Only parent categories
        #     .filter(products__is_active=True)             # Only categories with active products
        #     .filter(category_filter_q)                    # Additional filters
        #     .annotate(product_count=Count('products', distinct=True))  # Count distinct products
        #     .order_by('-product_count', 'name')[:category_limit]       # Sort and limit
        # )

        # category_data = CategorySerializer(categories, many=True).data

        # --------------------------------------------------
        # Final Response
        # --------------------------------------------------
        # response = {
        #     "categories": category_data,
        #     "products": product_data,
        # }

        return Response(product_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def variants(self, request, slug=None):
        """Get all variants for a product"""
        product = self.get_object()
        variants = product.variants.filter(is_active=True)
        serializer = ProductVariantDetailSerializer(
            variants, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def find_variant(self, request, slug=None):
        """
        Find a specific variant based on selected attributes

        POST data example:
        {
            "attributes": {
                "Color": "Black",
                "Memory": "256GB"
            }
        }
        """
        product = self.get_object()
        attributes = request.data.get("attributes", {})

        if not attributes:
            return Response(
                {"error": "No attributes provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Find variant matching all attributes
        variants = product.variants.filter(is_active=True)

        for attr_name, attr_value in attributes.items():
            variants = variants.filter(
                attribute_values__attribute_value__attribute__name=attr_name,
                attribute_values__attribute_value__value=attr_value,
            )

        variant = variants.first()

        if variant:
            serializer = ProductVariantDetailSerializer(
                variant, context={"request": request}
            )
            return Response(serializer.data)
        else:
            return Response(
                {"error": "No variant found with the specified attributes"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for product variants
    """

    queryset = (
        ProductVariant.objects.filter(is_active=True)
        .select_related("product")
        .prefetch_related("attribute_values", "images")
    )
    serializer_class = ProductVariantDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["product", "is_default"]
    search_fields = ["sku", "product__name"]

    @action(detail=True, methods=["get"])
    def check_stock(self, request, pk=None):
        """Check stock availability for a variant"""
        variant = self.get_object()
        return Response(
            {
                "sku": variant.sku,
                "stock_quantity": variant.stock_quantity,
                "is_in_stock": variant.is_in_stock,
                "is_low_stock": variant.is_low_stock,
                "low_stock_threshold": variant.low_stock_threshold,
            }
        )


class DealViewSet(viewsets.ModelViewSet):
    """ViewSet for deals"""

    queryset = Deal.objects.select_related("product", "variant").prefetch_related(
        "product__brand", "product__category", "product__images", "variant__images"
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DealFilter
    search_fields = ["title", "product__name", "product__brand__name"]
    ordering_fields = [
        "created_at",
        "start_date",
        "end_date",
        "discount_percentage",
        "display_order",
    ]
    ordering = ["-is_featured", "display_order", "-created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DealCreateUpdateSerializer
        elif self.action == "retrieve":
            return DealDetailSerializer
        return DealListSerializer

    def get_permissions(self):
        """Admin only for create, update, delete"""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """Track view when deal is retrieved"""
        instance = self.get_object()

        # Track view
        self._track_view(request, instance)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _track_view(self, request, deal):
        """Track deal view"""
        DealView.objects.create(
            deal=deal,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            session_key=request.session.session_key or "",
            user=request.user if request.user.is_authenticated else None,
            referrer=request.META.get("HTTP_REFERER", ""),
            device_type=self._get_device_type(request),
        )
        deal.increment_view()

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _get_device_type(self, request):
        """Determine device type from user agent"""
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        if "mobile" in user_agent or "android" in user_agent:
            return "mobile"
        elif "tablet" in user_agent or "ipad" in user_agent:
            return "tablet"
        return "desktop"

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured deals"""
        deals = (
            self.get_queryset()
            .filter(
                is_featured=True,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
            .exclude(sold_quantity__gte=F("total_quantity"))
        )

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def live(self, request):
        """Get all live deals"""
        deals = (
            self.get_queryset()
            .filter(
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
            .exclude(sold_quantity__gte=F("total_quantity"))
        )

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming deals"""
        deals = (
            self.get_queryset()
            .filter(is_active=True, start_date__gt=timezone.now())
            .order_by("start_date")
        )

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def deal_of_the_day(self, request):
        """Get current deal of the day"""
        deal = (
            self.get_queryset()
            .filter(
                deal_type="deal_of_day",
                is_active=True,
                is_featured=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
            .exclude(sold_quantity__gte=F("total_quantity"))
            .first()
        )

        if not deal:
            return Response(
                {"detail": "No active deal of the day found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DealDetailSerializer(deal, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def flash_sales(self, request):
        """Get active flash sales"""
        deals = (
            self.get_queryset()
            .filter(
                deal_type="flash_sale",
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
            .exclude(sold_quantity__gte=F("total_quantity"))
        )

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def track_click(self, request, slug=None):
        """Track deal click"""
        deal = self.get_object()
        click_type = request.data.get("click_type", "view_detail")

        DealClick.objects.create(
            deal=deal,
            ip_address=self._get_client_ip(request),
            session_key=request.session.session_key or "",
            user=request.user if request.user.is_authenticated else None,
            click_type=click_type,
        )
        deal.increment_click()

        return Response({"status": "click tracked"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def purchase(self, request, slug=None):
        """Record a purchase (increment sold quantity)"""
        deal = self.get_object()
        quantity = request.data.get("quantity", 1)

        # Validate quantity
        if quantity < 1:
            return Response(
                {"error": "Quantity must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > deal.max_quantity_per_order:
            return Response(
                {"error": f"Maximum {deal.max_quantity_per_order} items per order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if deal is live
        if not deal.is_live:
            return Response(
                {"error": "Deal is not currently active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if quantity available
        if deal.remaining_quantity < quantity:
            return Response(
                {"error": f"Only {deal.remaining_quantity} items remaining"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Increment sold quantity
        success = deal.increment_sold(quantity)

        if success:
            return Response(
                {
                    "status": "success",
                    "quantity": quantity,
                    "remaining": deal.remaining_quantity,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to process purchase"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get deal statistics"""
        now = timezone.now()

        total_deals = self.get_queryset().count()
        active_deals = self.get_queryset().filter(is_active=True).count()
        live_deals = (
            self.get_queryset()
            .filter(is_active=True, start_date__lte=now, end_date__gte=now)
            .exclude(sold_quantity__gte=F("total_quantity"))
            .count()
        )

        upcoming_deals = (
            self.get_queryset().filter(is_active=True, start_date__gt=now).count()
        )

        expired_deals = self.get_queryset().filter(end_date__lt=now).count()

        # Revenue calculation
        revenue_data = self.get_queryset().aggregate(
            total_revenue=Sum(
                F("sold_quantity") * F("discounted_price"), output_field=DecimalField()
            ),
            total_views=Sum("view_count"),
            total_clicks=Sum("click_count"),
            total_sold=Sum("sold_quantity"),
        )

        # Conversion rate
        if revenue_data["total_clicks"] and revenue_data["total_clicks"] > 0:
            avg_conversion = (
                revenue_data["total_sold"] / revenue_data["total_clicks"]
            ) * 100
        else:
            avg_conversion = 0

        stats = {
            "total_deals": total_deals,
            "active_deals": active_deals,
            "live_deals": live_deals,
            "upcoming_deals": upcoming_deals,
            "expired_deals": expired_deals,
            "total_revenue": revenue_data["total_revenue"] or 0,
            "total_views": revenue_data["total_views"] or 0,
            "total_clicks": revenue_data["total_clicks"] or 0,
            "total_sold": revenue_data["total_sold"] or 0,
            "average_conversion_rate": round(avg_conversion, 2),
        }

        serializer = DealStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def analytics(self, request, slug=None):
        """Get detailed analytics for a specific deal"""
        deal = self.get_object()

        # Views over time
        views_by_day = (
            deal.view_logs.extra(select={"day": "DATE(viewed_at)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        # Clicks over time
        clicks_by_day = (
            deal.click_logs.extra(select={"day": "DATE(clicked_at)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        # Device breakdown
        device_breakdown = deal.view_logs.values("device_type").annotate(
            count=Count("id")
        )

        analytics = {
            "deal": DealDetailSerializer(deal, context={"request": request}).data,
            "views_by_day": list(views_by_day),
            "clicks_by_day": list(clicks_by_day),
            "device_breakdown": list(device_breakdown),
            "total_views": deal.view_count,
            "total_clicks": deal.click_count,
            "total_sold": deal.sold_quantity,
            "conversion_rate": deal.get_conversion_rate(),
            "revenue": float(deal.sold_quantity * deal.discounted_price),
        }

        return Response(analytics)

from django.contrib.auth import get_user_model

User = get_user_model()


class RecentlyViewedProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for recently viewed products
    """
    serializer_class = RecentlyViewedProductSerializer
    # permission_classes = [IsAuthenticated]  # only logged-in users
    pagination_class = None  # optional, remove pagination

    def get_queryset(self):
        # try:
        #     user = self.request.user
        # except: 
        user = User.objects.all()[0]


        # get limit from query params, default = 10
        limit = self.request.query_params.get("limit", 10)

        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        # optional safety cap
        limit = min(limit, 50)

        return (
            RecentlyViewedProduct.objects
            .filter(user=user)
            .order_by("-viewed_at")[:limit]
        )

    @action(detail=False, methods=["get"])
    def list_recent(self, request):
        """
        Get last 10 recently viewed products
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

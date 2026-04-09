from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Coalesce
from django.db.models import Q, Min, Max, Sum, Avg, DecimalField, F, Prefetch
from .pagination import ProductPagination
from django.utils import timezone
from .models import (
    Category,
    Brand,
    Product,
    ProductImage,
    ProductVariant,
    VariantAttribute,
    VariantAttributeValue,
    Deal,
    RecentlyViewedProduct,
    ProductCombo,
    ProductComboItem,
    Promotion
)
from reviews.models import ProductReview
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
    ProductComboListSerializer,
    ProductComboDetailSerializer,
    ProductComboForProductDetailSerializer,
    ProductComboCreateUpdateSerializer,
    PromotionListSerializer,
    PromotionDetailSerializer,
    PromotionCreateUpdateSerializer,
)
from .utils import add_recently_viewed
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from .filters import DealFilter, ProductFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


from django.db.models import Count, Case, When, IntegerField


@extend_schema(tags=["Product Categories"])
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
        limit = self.request.query_params.get("limit", 10)

        try:
            limit = int(limit)
        except ValueError:
            limit = 10  # fallback to default if query param is invalid
        
        # Featured categories
        is_featured = self.request.query_params.get("is_featured")
        if is_featured == "true":
            queryset = queryset.filter(is_featured=True)[:int(limit)]

        # Top categories by product count
        top = self.request.query_params.get("top")
        if top == "true":
            queryset = (
                queryset.annotate(product_count=Count("products"))
                .filter(product_count__gt=0)
                .order_by("-product_count")[:int(limit)]
            )

        # Popular categories by total sold quantity
        popular = self.request.query_params.get("is_popular")
        if popular == "true":
            popular_qs = queryset.annotate(total_sold=Sum("products__variants__sold_quantity"))\
                                .filter(total_sold__gt=0)\
                                .order_by("-total_sold")[:limit]
            if popular_qs.exists():
                return popular_qs
            else:
                # Fallback to featured if popular is empty
                featured_qs = queryset.filter(is_featured=True)[:limit]
                return featured_qs

        return queryset[:limit]
    
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


@extend_schema(tags=["Product Brands"])
class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for brands
    """

    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]


@extend_schema(tags=["Products"])
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
        .prefetch_related(
            "images",
            "variants",
            "variants__variant_attributes__attribute",
            "variants__images",
            "promotions",
            Prefetch(
                "combos",
                queryset=ProductCombo.objects.filter(is_active=True).prefetch_related(
                    "items__product__images",
                    "items__product__variants",
                    "items__product__promotions",
                ),
                to_attr="active_combos",
            ),
        )
    )
    lookup_field = "slug"
    filterset_class = ProductFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "brand", "is_featured"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "base_price"]
    ordering = ["-created_at"]
    pagination_class = ProductPagination

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ]
    )
    @action(detail=False, methods=["get"], url_path="category/(?P<category_slug>[^/.]+)")
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="brand_slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ]
    )
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
    
    @action(detail=False, methods=["get"], url_path="new")
    def new_products(self, request):
        """Get newly added products with dynamic limit"""

        # Get limit from query params, default 10
        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10

        # Fetch recent products from DB (pre-limit for performance)
        queryset = self.get_queryset().order_by("-created_at")[:50]

        # Filter in Python by is_new and respect limit
        new_products = []
        for product in queryset:
            if product.is_new:
                new_products.append(product)
                if len(new_products) == limit:
                    break

        # Paginate the filtered list (optional)
        page = self.paginate_queryset(new_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(new_products, many=True)
        return Response(serializer.data)

    from django.db.models import Count, Q
    from rest_framework.decorators import action
    from rest_framework.response import Response


    @action(detail=False, methods=['get'], url_path='filters_metadata')
    def filters_metadata(self, request):
        queryset = self.get_queryset().filter(is_active=True)

        # --- Multi-category filter with subcategories ---
        category_slugs = request.query_params.get("category")
        selected_category_ids = []
        all_category_ids = []

        if category_slugs:
            slugs = [slug.strip() for slug in category_slugs.split(",") if slug.strip()]
            # Get selected categories
            categories = Category.objects.filter(slug__in=slugs, is_active=True)
            selected_category_ids = list(categories.values_list('id', flat=True))
            all_category_ids.extend(selected_category_ids)

            # Include all subcategories recursively
            def get_subcategory_ids(cat_queryset):
                sub_ids = []
                for cat in cat_queryset:
                    children = cat.children.filter(is_active=True)
                    if children.exists():
                        child_ids = list(children.values_list('id', flat=True))
                        sub_ids.extend(child_ids)
                        sub_ids.extend(get_subcategory_ids(children))
                return sub_ids

            subcategory_ids = get_subcategory_ids(categories)
            all_category_ids.extend(subcategory_ids)

            # Filter products by all category IDs (parent + children)
            queryset = queryset.filter(category__id__in=all_category_ids)

        # --- Variant IDs for filtering attributes ---
        product_variant_ids = list(
            ProductVariant.objects.filter(product__in=queryset, is_active=True).values_list('id', flat=True)
        )

        # --- Brands metadata ---
        brands_qs = Brand.objects.filter(products__in=queryset, is_active=True)\
            .annotate(product_count=Count("products", distinct=True))\
            .order_by("name")
    
        brands = []
        for b in brands_qs:
            logo_url = b.logo.url if b.logo else None
            if logo_url and not logo_url.startswith("http"):
                logo_url = request.build_absolute_uri(logo_url)
            brands.append({
                "name": b.name,
                "slug": b.slug,
                "product_count": b.product_count,
                "logo": logo_url,
            })
    


        # --- Attributes + values metadata ---
        attributes = VariantAttribute.objects.prefetch_related("values").all()
        attribute_data = []
        for attr in attributes:
            values = (
                attr.values.filter(
                    product_variants__in=product_variant_ids
                )
                .annotate(count=Count("product_variants", distinct=True))
                .values("value", "id", "count", "color_code")
                .order_by("value")
            )
            attribute_data.append({
                "name": attr.name,
                "slug": attr.name.lower().replace(" ", "_"),
                "values": list(values)
            })
            
        # --- Ratings metadata from ProductReview ---
        ratings = []
        for star in range(1, 6):
            count = ProductReview.objects.filter(
                product__in=queryset,
                rating=star
            ).count()
            ratings.append({"rating": star, "count": count})

        # --- Only return subcategories, not the parent/selected category ---
        subcategories = Category.objects.filter(id__in=subcategory_ids).values("name", "slug", "parent_id")

        return Response({
            "brands": list(brands),
            "attributes": attribute_data,
            "categories": list(subcategories),
            "ratings": ratings[::-1],
        })

        
        
    @action(detail=False, methods=["get"], url_path="best_seller")
    def best_seller(self, request):
        """Get dynamically calculated best seller products with pagination"""

        # Optional pre-limit (for performance)
        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10

        category_slug = request.query_params.get("category")

        queryset = self.get_queryset()

        # 🔹 Filter by category slug if provided
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # 🔹 Annotate total sold quantity
        queryset = (
            queryset
            .annotate(total_sold=Sum("variants__sold_quantity"))
            .order_by("-total_sold")[:limit]
        )

        # 🔹 Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
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
            .prefetch_related("images", "variants", "promotions")
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
            .select_related("category", "brand")
            .prefetch_related("images", "variants", "promotions")
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
                    variant_attributes__attribute__name=attr_name,
                    variant_attributes__value=attr_value,
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


class ProductRelatedPublicView(ProductViewSet):
    """Frontend-friendly related products route hidden from OpenAPI docs."""

    @extend_schema(exclude=True)
    def related(self, request, slug=None):
        return super().related(request, slug=slug)


@extend_schema(tags=["Product Variants"])
class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for product variants
    """

    queryset = (
        ProductVariant.objects.filter(is_active=True)
        .select_related("product")
        .prefetch_related("variant_attributes", "images")
    )
    serializer_class = ProductVariantDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["product", "is_default"]
    search_fields = ["product__name"]

    @action(detail=True, methods=["get"])
    def check_stock(self, request, pk=None):
        """Check stock availability for a variant"""
        variant = self.get_object()
        return Response(
            {
                "stock_quantity": variant.stock_quantity,
                "is_in_stock": variant.is_in_stock,
                "is_low_stock": variant.is_low_stock,
                "low_stock_threshold": variant.low_stock_threshold,
            }
        )


@extend_schema(tags=["Deals"])
class DealViewSet(viewsets.ModelViewSet):
    """ViewSet for deals - simplified version"""

    queryset = Deal.objects.select_related("product").prefetch_related(
        "product__brand", "product__category", "product__images"
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DealFilter
    search_fields = ["title", "product__name", "product__brand__name"]
    ordering_fields = ["created_at", "start_at", "end_at", "discount_percent", "display_order"]
    ordering = ["-is_featured", "display_order", "-created_at"]
    pagination_class = ProductPagination

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

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured deals that are currently active"""
        now = timezone.now()
        deals = self.get_queryset().filter(
            is_featured=True,
            is_active=True,
            start_at__lte=now,
            end_at__gte=now,
        )

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def live(self, request):
        """Get all live (currently active) deals"""
        now = timezone.now()
        deals = self.get_queryset().filter(
            is_active=True,
            start_at__lte=now,
            end_at__gte=now,
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
        now = timezone.now()
        deals = self.get_queryset().filter(
            is_active=True,
            start_at__gt=now
        ).order_by("start_at")

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def deal_of_the_day(self, request):
        """Get current deal of the day"""
        now = timezone.now()
        deal = self.get_queryset().filter(
            deal_type="daily",
            is_active=True,
            is_featured=True,
            start_at__lte=now,
            end_at__gte=now,
        ).first()

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
        now = timezone.now()
        deals = self.get_queryset().filter(
            deal_type="flash",
            is_active=True,
            start_at__lte=now,
            end_at__gte=now,
        )

        page = self.paginate_queryset(deals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

from django.contrib.auth import get_user_model

User = get_user_model()


@extend_schema(tags=["Recently Viewed"])
class RecentlyViewedProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for recently viewed products
    """
    serializer_class = RecentlyViewedProductSerializer
    permission_classes = [IsAuthenticated]  # only logged-in users
    pagination_class = None  # optional, remove pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return RecentlyViewedProduct.objects.none()

        user = self.request.user
        if not user or not user.is_authenticated:
            return RecentlyViewedProduct.objects.none()


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

from rest_framework.decorators import api_view
@api_view(['GET'])
def get_categories_by_brand(request):
    brand_id = request.GET.get('brand_id')
    if not brand_id:
        return Response({"error": "Brand ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    categories = Category.objects.filter(brands__id=brand_id, is_active=True).values('id', 'name')
    return Response(list(categories))


# ===== PRODUCT COMBO VIEWSET =====


@extend_schema(tags=["Product Combos"])
class ProductComboViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product combos/bundles
    """
    queryset = (
        ProductCombo.objects
        .filter(is_active=True)
        .select_related('main_product')
        .prefetch_related('items__product__images', 'items__product__variants')
    )
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['main_product']
    search_fields = ['name', 'description', 'slug', 'main_product__name']
    ordering_fields = ['created_at', 'combo_selling_price']
    ordering = ['-is_featured', '-created_at']
    pagination_class = ProductPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductComboCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ProductComboDetailSerializer
        return ProductComboListSerializer

    def get_permissions(self):
        """Admin only for create, update, delete"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured product combos"""
        combos = self.get_queryset().filter(is_featured=True)

        page = self.paginate_queryset(combos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(combos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def items(self, request, slug=None):
        """Get items in a specific combo"""
        combo = self.get_object()
        items = combo.items.all().select_related('product').prefetch_related('product__images')

        page = self.paginate_queryset(items)
        if page is not None:
            from .serializers import ProductComboItemSerializer
            serializer = ProductComboItemSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        from .serializers import ProductComboItemSerializer
        serializer = ProductComboItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)


# ===== PROMOTION VIEWSET =====


@extend_schema(tags=["Promotions"])
class PromotionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing promotions (Free Shipping, Free Gift, etc.)
    
    Standard endpoints:
        list: GET /promotions/ - List all promotions with filtering
        create: POST /promotions/ - Create a new promotion (admin only)
        retrieve: GET /promotions/{id}/ - Get promotion details
        update: PUT /promotions/{id}/ - Update a promotion (admin only)
        partial_update: PATCH /promotions/{id}/ - Partially update a promotion (admin only)
        destroy: DELETE /promotions/{id}/ - Delete a promotion (admin only)
    
    Custom endpoints:
        active: GET /promotions/active/ - Get all currently active promotions (time-based)
        by_type: GET /promotions/by_type/?type=free_shipping - Filter by promotion type
        upcoming: GET /promotions/upcoming/ - Get promotions that haven't started yet
        expired: GET /promotions/expired/ - Get promotions that have ended
        summary: GET /promotions/summary/ - Get statistics summary
        products: GET /promotions/{id}/products/ - Get products in a promotion
    
    Query Parameters:
        - promotion_type: Filter by type ('free_shipping' or 'free_gift')
        - is_active: Filter by active status (true/false)
        - search: Search in title and description
        - ordering: Order by start_date, end_date, or created_at
        - limit: Limit results per page
        - offset: Pagination offset
    
    Permissions:
        - Read (list/retrieve): Available to all users
        - Create/Update/Delete: Admin/Staff only
    """
    
    queryset = Promotion.objects.prefetch_related('products')
    lookup_field = 'id'
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['promotion_type', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    pagination_class = ProductPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on the action.
        
        - Create/Update: PromotionCreateUpdateSerializer (validates input, manages dates)
        - Retrieve: PromotionDetailSerializer (full details with products)
        - List/Other: PromotionListSerializer (simplified view)
        """
        if self.action in ['create', 'update', 'partial_update']:
            return PromotionCreateUpdateSerializer
        elif self.action == 'retrieve':
            return PromotionDetailSerializer
        return PromotionListSerializer
    
    def get_permissions(self):
        """
        Override permissions:
        - Create, Update, Delete: Authenticated users only (admin check via staff_required)
        - All other actions: Allow any (read-only)
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'], url_path='active', url_name='active-promotions')
    def active(self, request):
        """
        Retrieve all currently active promotions.
        
        A promotion is considered active if:
            - is_active = True
            - start_date <= current_time
            - end_date >= current_time
        
        Returns: Paginated list of active PromotionListSerializer objects
        """
        promotions = Promotion.active()
        
        page = self.paginate_queryset(promotions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-type', url_name='by-type')
    def by_type(self, request):
        """
        Retrieve promotions filtered by type.
        
        Query Parameters:
            type (required): The promotion type filter
                - 'free_shipping': Free shipping promotions
                - 'free_gift': Free gift promotions
        
        Example: GET /promotions/by-type/?type=free_shipping
        
        Returns: Paginated list of promotions matching the type
        Status Codes:
            - 200: Success
            - 400: Missing or invalid 'type' parameter
        """
        promotion_type = request.query_params.get('type')
        
        if not promotion_type:
            return Response(
                {'error': 'type query parameter is required (free_shipping or free_gift)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate type
        valid_types = [choice[0] for choice in Promotion.PromotionType.choices]
        if promotion_type not in valid_types:
            return Response(
                {'error': f'Invalid type. Choose from: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        promotions = self.get_queryset().filter(promotion_type=promotion_type)
        
        page = self.paginate_queryset(promotions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='products', url_name='promotion-products')
    def products(self, request, id=None):
        """
        Retrieve all active products associated with a specific promotion.
        
        Path Parameters:
            id: The ID of the promotion
        
        Returns: Paginated list of ProductListSerializer objects
        
        Example: GET /promotions/1/products/
        """
        promotion = self.get_object()
        products = (
            promotion.products.filter(is_active=True)
            .select_related('category', 'brand')
            .prefetch_related('images', 'variants', 'promotions')
        )
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='upcoming', url_name='upcoming-promotions')
    def upcoming(self, request):
        """
        Retrieve all upcoming promotions (not yet started).
        
        Returns promotions where:
            - is_active = True
            - start_date > current_time
        
        Results are ordered by start_date (earliest first).
        
        Returns: Paginated list of upcoming PromotionListSerializer objects
        """
        now = timezone.now()
        promotions = self.get_queryset().filter(
            is_active=True,
            start_date__gt=now
        ).order_by('start_date')
        
        page = self.paginate_queryset(promotions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='expired', url_name='expired-promotions')
    def expired(self, request):
        """
        Retrieve all expired promotions (already ended).
        
        Returns promotions where:
            - end_date < current_time
        
        Results are ordered by end_date (most recent first).
        
        Returns: Paginated list of expired PromotionListSerializer objects
        """
        now = timezone.now()
        promotions = self.get_queryset().filter(
            end_date__lt=now
        ).order_by('-end_date')
        
        page = self.paginate_queryset(promotions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='summary', url_name='promotions-summary')
    def summary(self, request):
        """
        Retrieve promotional statistics and summary information.
        
        Returns a summary object containing:
            - total_promotions: Total number of promotions in the system
            - active_promotions: Number of currently active promotions
            - inactive_promotions: Number of inactive promotions
            - upcoming_promotions: Number of promotions not yet started
            - expired_promotions: Number of promotions that have ended
            - by_type: Breakdown by promotion type
                - free_shipping: Count of free shipping promotions
                - free_gift: Count of free gift promotions
        
        Returns: JSON object with statistics (not paginated)
        
        Example response:
            {
                "total_promotions": 15,
                "active_promotions": 5,
                "inactive_promotions": 3,
                "upcoming_promotions": 4,
                "expired_promotions": 3,
                "by_type": {
                    "free_shipping": 8,
                    "free_gift": 7
                }
            }
        """
        now = timezone.now()
        
        stats = {
            'total_promotions': Promotion.objects.count(),
            'active_promotions': Promotion.active().count(),
            'inactive_promotions': Promotion.objects.filter(is_active=False).count(),
            'upcoming_promotions': Promotion.objects.filter(
                is_active=True,
                start_date__gt=now
            ).count(),
            'expired_promotions': Promotion.objects.filter(
                end_date__lt=now
            ).count(),
            'by_type': {
                'free_shipping': Promotion.objects.filter(
                    promotion_type=Promotion.PromotionType.FREE_SHIPPING
                ).count(),
                'free_gift': Promotion.objects.filter(
                    promotion_type=Promotion.PromotionType.FREE_GIFT
                ).count(),
            }
        }
        
        return Response(stats)
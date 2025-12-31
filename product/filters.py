import django_filters
from .models import Deal



class DealFilter(django_filters.FilterSet):
    """Filter class for deals"""
    deal_type = django_filters.MultipleChoiceFilter(
        choices=Deal.DEAL_TYPE_CHOICES,
        field_name='deal_type'
    )
    min_price = django_filters.NumberFilter(field_name='discounted_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='discounted_price', lookup_expr='lte')
    min_discount = django_filters.NumberFilter(field_name='discount_percentage', lookup_expr='gte')
    is_live = django_filters.BooleanFilter(method='filter_is_live')
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    free_shipping = django_filters.BooleanFilter(field_name='free_shipping')
    category = django_filters.CharFilter(field_name='product__category__slug')
    brand = django_filters.CharFilter(field_name='product__brand__slug')
    
    class Meta:
        model = Deal
        fields = ['deal_type', 'is_featured', 'free_shipping', 'is_active']
    
    def filter_is_live(self, queryset, name, value):
        """Filter for live deals"""
        if value:
            now = timezone.now()
            return queryset.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).exclude(sold_quantity__gte=F('total_quantity'))
        return queryset
    

from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Product, ProductVariant, Brand, Category
from reviews.models import ProductReview


# class ProductFilter(filters.FilterSet):
#     """
#     Comprehensive filter class for Product model.
#     Supports all filters visible in the e-commerce UI.
#     """
    
#     # ==========================================
#     # PRICE FILTERS
#     # ==========================================
#     min_price = filters.NumberFilter(
#         field_name='base_price',
#         lookup_expr='gte',
#         label='Minimum Price'
#     )
    
#     max_price = filters.NumberFilter(
#         field_name='base_price',
#         lookup_expr='lte',
#         label='Maximum Price'
#     )
    
#     # Alternative: Price range filter (single field)
#     price_range = filters.RangeFilter(
#         field_name='base_price',
#         label='Price Range'
#     )
    
#     # ==========================================
#     # CATEGORY FILTERS
#     # ==========================================
#     category = filters.CharFilter(
#         method='filter_category',
#         label='Category (by slug)'
#     )
    
#     category_id = filters.NumberFilter(
#         field_name='category__id',
#         label='Category (by ID)'
#     )
    
#     # ==========================================
#     # BRAND FILTERS
#     # ==========================================
#     brand = filters.CharFilter(
#         method='filter_brands',
#         label='Brand(s) - comma separated slugs'
#     )
    
#     brand_id = filters.NumberFilter(
#         field_name='brand__id',
#         label='Brand (by ID)'
#     )
    
#     # ==========================================
#     # COLOR FILTER (from variants)
#     # ==========================================
#     color = filters.CharFilter(
#         method='filter_colors',
#         label='Color(s) - comma separated'
#     )
    
#     # ==========================================
#     # MEMORY FILTER (from variants)
#     # ==========================================
#     memory = filters.CharFilter(
#         method='filter_memory',
#         label='Memory - comma separated (e.g., 4GB,6GB,8GB)'
#     )
    
#     # ==========================================
#     # STORAGE FILTER (from variants)
#     # ==========================================
#     storage = filters.CharFilter(
#         method='filter_storage',
#         label='Storage - comma separated (e.g., 128GB,256GB)'
#     )
    
#     # ==========================================
#     # CONDITION FILTER
#     # ==========================================
#     # condition = filters.MultipleChoiceFilter(
#     #     field_name='condition',
#     #     choices=Product.CONDITION_CHOICES,
#     #     label='Condition'
#     # )
    
#     # Single condition filter
#     # condition_single = filters.ChoiceFilter(
#     #     field_name='condition',
#     #     choices=Product.CONDITION_CHOICES,
#     #     label='Single Condition'
#     # )
    
#     # ==========================================
#     # SCREEN SIZE FILTERS
#     # ==========================================
#     # screen_size = filters.CharFilter(
#     #     method='filter_screen_size',
#     #     label='Screen Size Range'
#     # )
    
#     # min_screen_size = filters.NumberFilter(
#     #     field_name='screen_size',
#     #     lookup_expr='gte',
#     #     label='Minimum Screen Size'
#     # )
    
#     # max_screen_size = filters.NumberFilter(
#     #     field_name='screen_size',
#     #     lookup_expr='lte',
#     #     label='Maximum Screen Size'
#     # )
    
#     # ==========================================
#     # RATING FILTER
#     # ==========================================
#     rating = filters.NumberFilter(
#         field_name='average_rating',
#         lookup_expr='gte',
#         label='Minimum Rating'
#     )
    
#     min_rating = filters.NumberFilter(
#         field_name='average_rating',
#         lookup_expr='gte',
#         label='Minimum Rating (alias)'
#     )
    
#     # ==========================================
#     # STOCK AVAILABILITY
#     # ==========================================
#     in_stock = filters.BooleanFilter(
#         method='filter_in_stock',
#         label='In Stock Only'
#     )
    
#     # ==========================================
#     # DISCOUNT/SALE FILTERS
#     # ==========================================
#     on_sale = filters.BooleanFilter(
#         method='filter_on_sale',
#         label='On Sale Only'
#     )
    
#     min_discount = filters.NumberFilter(
#         field_name='discount_percentage',
#         lookup_expr='gte',
#         label='Minimum Discount Percentage'
#     )
    
#     # ==========================================
#     # PRODUCT STATUS FILTERS
#     # ==========================================
#     is_featured = filters.BooleanFilter(
#         field_name='is_featured',
#         label='Featured Only'
#     )
    
#     # ==========================================
#     # SEARCH FILTERS
#     # ==========================================
#     search = filters.CharFilter(
#         method='filter_search',
#         label='Search (name, description, brand)'
#     )
    
#     name = filters.CharFilter(
#         field_name='name',
#         lookup_expr='icontains',
#         label='Product Name Contains'
#     )
    
#     class Meta:
#         model = Product
#         fields = {
#             'base_price': ['exact', 'gte', 'lte', 'range'],
#             # 'condition': ['exact', 'in'],
#             'is_active': ['exact'],
#             'is_featured': ['exact'],
#         }
    
#     # ==========================================
#     # CUSTOM FILTER METHODS
#     # ==========================================
    
#     def filter_category(self, queryset, name, value):
#         """
#         Filter by category slug.
#         Also includes products from child categories.
        
#         Example: ?category=cell-phones-tablets
#         """
#         try:
#             category = Category.objects.get(slug=value, is_active=True)
            
#             # Get category and all its children
#             category_ids = [category.id]
#             children = category.children.filter(is_active=True)
#             category_ids.extend(children.values_list('id', flat=True))
            
#             return queryset.filter(category_id__in=category_ids)
#         except Category.DoesNotExist:
#             return queryset.none()
    
#     def filter_brands(self, queryset, name, value):
#         """
#         Filter by multiple brand slugs (comma-separated).
        
#         Example: ?brand=apple,samsung,xiaomi
#         """
#         if not value:
#             return queryset
        
#         brand_slugs = [slug.strip() for slug in value.split(',')]
#         return queryset.filter(brand__slug__in=brand_slugs)
    
#     def filter_colors(self, queryset, name, value):
#         """
#         Filter by colors available in product variants.
#         Supports multiple colors (comma-separated).
        
#         Example: ?color=black,blue,silver
#         """
#         if not value:
#             return queryset
        
#         colors = [color.strip() for color in value.split(',')]
        
#         # Filter products that have variants with these colors
#         return queryset.filter(
#             variants__color__in=colors,
#             variants__is_available=True
#         ).distinct()
    
#     def filter_memory(self, queryset, name, value):
#         """
#         Filter by memory options in variants.
#         Supports multiple memory sizes (comma-separated).
        
#         Example: ?memory=4GB,6GB,8GB
#         """
#         if not value:
#             return queryset
        
#         memories = [mem.strip() for mem in value.split(',')]
        
#         return queryset.filter(
#             variants__memory__in=memories,
#             variants__is_available=True
#         ).distinct()
    
#     def filter_storage(self, queryset, name, value):
#         """
#         Filter by storage options in variants.
#         Supports multiple storage sizes (comma-separated).
        
#         Example: ?storage=128GB,256GB,512GB
#         """
#         if not value:
#             return queryset
        
#         storages = [storage.strip() for storage in value.split(',')]
        
#         return queryset.filter(
#             variants__storage__in=storages,
#             variants__is_available=True
#         ).distinct()
    
#     # def filter_screen_size(self, queryset, name, value):
#     #     """
#     #     Filter by screen size range.
        
#     #     Supported values:
#     #         - 7-under: Less than 7 inches
#     #         - 7-8.9: 7 to 8.9 inches
#     #         - 9-10.9: 9 to 10.9 inches
#     #         - 11-greater: 11 inches and above
        
#     #     Example: ?screen_size=7-8.9
#     #     """
#     #     if value == '7-under':
#     #         return queryset.filter(screen_size__lt=7)
#     #     elif value == '7-8.9':
#     #         return queryset.filter(screen_size__gte=7, screen_size__lt=9)
#     #     elif value == '9-10.9':
#     #         return queryset.filter(screen_size__gte=9, screen_size__lt=11)
#     #     elif value == '11-greater':
#     #         return queryset.filter(screen_size__gte=11)
#     #     else:
#     #         return queryset
    
#     def filter_in_stock(self, queryset, name, value):
#         """
#         Filter products that are in stock.
#         Checks if any variant is available with stock > 0.
        
#         Example: ?in_stock=true
#         """
#         if value:
#             return queryset.filter(
#                 variants__is_available=True,
#                 variants__stock_quantity__gt=0
#             ).distinct()
#         return queryset
    
#     def filter_on_sale(self, queryset, name, value):
#         """
#         Filter products that have a discount.
        
#         Example: ?on_sale=true
#         """
#         if value:
#             return queryset.filter(discount_percentage__gt=0)
#         return queryset
    
#     def filter_search(self, queryset, name, value):
#         """
#         Search across multiple fields.
#         Searches in: product name, description, brand name, category name
        
#         Example: ?search=iphone
#         """
#         if not value:
#             return queryset
        
#         return queryset.filter(
#             Q(name__icontains=value) |
#             Q(description__icontains=value) |
#             Q(brand__name__icontains=value) |
#             Q(category__name__icontains=value)
#         ).distinct()



from django_filters import rest_framework as filters
from .models import Product

class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass

from django_filters import rest_framework as filters
from django.db.models import Q

class ProductFilter(filters.FilterSet):
    # Existing filters
    category = CharInFilter(field_name="category__slug", lookup_expr="in")
    brand = CharInFilter(field_name="brand__slug", lookup_expr="in")
    min_price = filters.NumberFilter(field_name="variants__price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="variants__price", lookup_expr="lte")
    is_featured = filters.BooleanFilter(field_name="is_featured")
    search = filters.CharFilter(field_name="name", lookup_expr="icontains")

    # Attribute filters (dynamic)
    color = filters.CharFilter(method="filter_attribute")
    storage = filters.CharFilter(method="filter_attribute")
    # Rating filter (1-5 stars, comma-separated)
    rating = filters.CharFilter(method="filter_rating")

    class Meta:
        model = Product
        fields = ["category", "brand", "min_price", "max_price", "is_featured", "search", "color", "storage", "rating"]

    def filter_attribute(self, queryset, name, value):
        """
        Filter products by variant attribute values.
        Example: ?color=red,blue
        """
        if not value:
            return queryset
        values = [v.strip() for v in value.split(",")]

        value_filters = Q()
        for v in values:
            value_filters |= Q(variants__attribute_values__attribute_value__value__iexact=v)

        return queryset.filter(
            Q(variants__attribute_values__attribute_value__attribute__name__iexact=name),
            value_filters,
            variants__is_active=True
        ).distinct()

    def filter_rating(self, queryset, name, value):
        """
        Filter products by review rating (1-5).
        Example: ?rating=4,5
        """
        if not value:
            return queryset
        try:
            ratings = [int(r.strip()) for r in value.split(",") if r.strip()]
        except ValueError:
            return queryset.none()  # invalid input

        # Filter products with at least one review in the given ratings
        product_ids = ProductReview.objects.filter(
            product__in=queryset,
            rating__in=ratings
        ).values_list('product_id', flat=True).distinct()

        return queryset.filter(id__in=product_ids)
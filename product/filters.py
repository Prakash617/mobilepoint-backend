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
from django.utils import timezone
from .models import RecentlyViewedProduct

def add_recently_viewed(user, product):
    obj, created = RecentlyViewedProduct.objects.get_or_create(user=user, product=product)
    if not created:
        obj.viewed_at = timezone.now()
        obj.save()
from django.shortcuts import render
from django.http import JsonResponse
from .models import Category, Brand
from django.views.decorators.http import require_GET

@require_GET
def get_categories_by_brand(request):
    brand_id = request.GET.get('brand_id')
    categories_data = []

    if brand_id:
        try:
            brand = Brand.objects.get(id=brand_id)
            categories = brand.category.all().values('id', 'name').order_by('name')
            categories_data = list(categories)
        except Brand.DoesNotExist:
            pass # Return empty list if brand not found

    return JsonResponse(categories_data, safe=False)

# Create your views here.
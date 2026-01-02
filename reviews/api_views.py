

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from product.models import Product
from django.db.models import Avg, Count

from .models import ProductReview
from .serializers import ProductReviewSerializer

class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Product Reviews
    """
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]  # Anyone can view
        # return [permissions.IsAuthenticated()]  # Auth required to create/update
        return [permissions.AllowAny()]  # Anyone can view

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id, is_approved=True)
        return queryset
    
    def list(self, request, *args, **kwargs):
        product_slug = request.query_params.get("product_slug")

        queryset = self.get_queryset()

        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)

        # ⭐ Average rating
        average_rating = queryset.aggregate(
            avg=Avg("rating")
        )["avg"] or 0

        # ⭐ Star counts (1–5)
        star_counts_raw = (
            queryset
            .values("rating")
            .annotate(count=Count("id"))
        )

        # Ensure all stars exist (1–5)
        star_counts = {str(i): 0 for i in range(1, 6)}
        for item in star_counts_raw:
            star_counts[str(item["rating"])] = item["count"]

        # Serialize reviews
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "average_rating": round(average_rating, 1),
            "total_reviews": queryset.count(),
            "star_counts": star_counts,
            "results": serializer.data,
        })
    
    def create(self, request, *args, **kwargs):
        """
        Create a new product review using product slug
        """
        product_slug = request.data.get("product_slug")

        if not product_slug:
            return Response(
                {"product_slug": "Product slug is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, slug=product_slug)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            product=product,
            is_approved=False  # Requires admin approval
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
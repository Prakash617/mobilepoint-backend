from rest_framework import viewsets, permissions
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
        return [permissions.IsAuthenticated()]  # Auth required to create/update

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id, is_approved=True)
        return queryset

from rest_framework import serializers
from .models import ProductReview
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    product_slug = serializers.SlugField(
        source="product.slug",
        read_only=True
    )

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product",        # internal ID (optional to keep)
            "product_slug",   # 👈 returned to frontend
            "user",
            "rating",
            "title",
            "comment",
            "image",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "product",
            "product_slug",
            "is_approved",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        else:
            validated_data["user"] = None  # or anonymous user

        return super().create(validated_data)

from rest_framework import serializers
from .models import ProductReview

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # Show username
    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product",
            "user",
            "rating",
            "title",
            "comment",
            "image",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "is_approved", "created_at", "updated_at"]

    def create(self, validated_data):
        # Automatically assign user from context if available
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

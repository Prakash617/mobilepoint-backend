from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """For returning basic user info"""
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "profile_image", "is_verified"]


class RegisterSerializer(serializers.ModelSerializer):
    """For registering a new user"""
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "password2"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        # Remove password2 before saving
        validated_data.pop("password2")
        password = validated_data.pop("password")

        # Create user instance
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False  # require email verification if applicable
        user.save()
        return user


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Used for resending verification email"""
    email = serializers.EmailField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)

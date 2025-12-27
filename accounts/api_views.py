from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ResendVerificationEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from rest_framework.response import Response



class MeView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User created successfully. Please check your email to verify your account.",
                "user": RegisterSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

class VerifyEmailView(views.APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.GET.get("token")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            print(f'this is user: {user}')
            if not user.is_active:
                user.is_active = True
                user.is_verified = True
                user.save()
            return Response(
                {"message": "Email successfully verified"}, status=status.HTTP_200_OK
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Activation link expired"}, status=status.HTTP_400_BAD_REQUEST
            )
        except (jwt.exceptions.DecodeError, TokenError):
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResendVerificationEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            return Response(
                {"message": "This account has already been verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = RefreshToken.for_user(user).access_token

        current_site = get_current_site(request).domain
        relative_link = reverse("verify-email")
        verification_url = f"http://{current_site}{relative_link}?token={str(token)}"

        subject = "Verify your email"
        message = f"Hi {user.username}, please use this link to verify your email: \n{verification_url}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

        return Response(
            {
                "message": "Verification email has been resent. Please check your email to verify your account."
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token_generator = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        current_site = get_current_site(request).domain
        relative_link = reverse(
            "password-reset-confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        reset_url = f"http://{current_site}{relative_link}"

        subject = "Password Reset Request"
        message = f"Hi {user.first_name}, use the link below to reset your password:\n{reset_url}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

        return Response(
            {"message": "Password reset email sent."}, status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            user = None

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Invalid token or user ID."},
            status=status.HTTP_400_BAD_REQUEST,
        )




class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data["refresh"]
        access = response.data["access"]

        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=False, # For development
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
        )
        del response.data["refresh"]
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        if "refresh" in response.data:
            access = response.data["access"]
            response.set_cookie(
                key="refresh_token",
                value=response.data["refresh"],
                httponly=True,
                # secure=True,
                secure=False,         #for development
                samesite="lax",
                max_age=7 * 24 * 60 * 60,
                path="/",
            )
           
            del response.data["refresh"]
        return response
    
# auth/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.COOKIES.get("refresh_token")
        if not refresh:
            return Response({"detail": "No refresh token"}, status=400)

        try:
            token = RefreshToken(refresh)
            token.blacklist()
            response = Response({"detail": "Logged out"}, status=205)
            response.delete_cookie("refresh_token")
            response.delete_cookie("access_token")
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=400)
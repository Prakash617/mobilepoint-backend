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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse



@extend_schema(
    tags=["User"],
    summary="Get or update current user profile",
    description="Retrieve or update the authenticated user's profile information. Requires access token in Authorization header.",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Unauthorized - Invalid or missing access token"),
    },
)
class MeView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Auth"],
    summary="Register a new user",
    description="Create a new user account. A verification email will be sent to the provided email address.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="User created successfully",
            response=RegisterSerializer,
        ),
        400: OpenApiResponse(description="Bad request - Validation errors"),
    },
)
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

@extend_schema(
    tags=["Auth"],
    summary="Verify email address",
    description="Verify user email address using the token sent via email.",
    parameters=[
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Email verification token",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Email successfully verified"),
        400: OpenApiResponse(description="Invalid or expired token"),
    },
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


@extend_schema(
    tags=["Auth"],
    summary="Resend verification email",
    description="Resend the email verification link to the user's email address.",
    request=ResendVerificationEmailSerializer,
    responses={
        200: OpenApiResponse(description="Verification email resent successfully"),
        400: OpenApiResponse(description="Account already verified"),
        404: OpenApiResponse(description="User not found"),
    },
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


@extend_schema(
    tags=["Auth"],
    summary="Request password reset",
    description="Send a password reset link to the user's email address.",
    request=PasswordResetRequestSerializer,
    responses={
        200: OpenApiResponse(description="Password reset email sent"),
        404: OpenApiResponse(description="User with this email does not exist"),
    },
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


@extend_schema(
    tags=["Auth"],
    summary="Confirm password reset",
    description="Reset user password using the token and uidb64 from the reset link.",
    request=PasswordResetConfirmSerializer,
    parameters=[
        OpenApiParameter(
            name="uidb64",
            type=str,
            location=OpenApiParameter.PATH,
            required=True,
            description="Base64 encoded user ID",
        ),
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            required=True,
            description="Password reset token",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Password reset successfully"),
        400: OpenApiResponse(description="Invalid token or user ID"),
    },
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




from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

@extend_schema(
    tags=["Auth"],
    summary="Login and obtain access token",
    description="""Authenticate user and obtain access token.
    
    **Authentication Flow:**
    - Refresh token is stored in Django session (server-side)
    - Only access token is returned to the client
    - Session expires after 7 days
    
    **Usage:**
    - Send username/email and password
    - Receive access token
    - Use access token in Authorization header: `Bearer <token>`
    """,
    responses={
        200: OpenApiResponse(
            description="Login successful",
            response={
                "type": "object",
                "properties": {
                    "access": {"type": "string", "description": "JWT access token"}
                },
            },
        ),
        401: OpenApiResponse(description="Invalid credentials"),
    },
)
class SessionTokenObtainPairView(TokenObtainPairView):
    """
    Login:
    - Refresh token stored in Django session
    - Only access token returned to client
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        refresh = response.data.get("refresh")
        access = response.data.get("access")

        # Store refresh token in session
        request.session["refresh_token"] = refresh
        request.session.set_expiry(7 * 24 * 60 * 60)  # 7 days

        # Remove refresh token from response
        response.data = {
            "access": access
        }

        return response


from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response


@extend_schema(
    tags=["Auth"],
    summary="Refresh access token",
    description="""Refresh the access token using the refresh token stored in Django session.
    
    **How it works:**
    - Refresh token is automatically retrieved from session (no need to send it)
    - Returns a new access token
    - Session must be valid (not expired)
    """,
    request=None,
    responses={
        200: OpenApiResponse(
            description="Token refreshed successfully",
            response={
                "type": "object",
                "properties": {
                    "access": {"type": "string", "description": "New JWT access token"}
                },
            },
        ),
        401: OpenApiResponse(description="No refresh token in session or session expired"),
    },
)
class SessionTokenRefreshView(TokenRefreshView):
    """
    Refresh access token using refresh token from session
    """

    def post(self, request, *args, **kwargs):
        refresh = request.session.get("refresh_token")

        if not refresh:
            return Response(
                {"detail": "No refresh token in session"},
                status=401
            )

        request.data["refresh"] = refresh
        response = super().post(request, *args, **kwargs)

        # Rotate refresh token if enabled
        if "refresh" in response.data:
            request.session["refresh_token"] = response.data["refresh"]
            del response.data["refresh"]

        return response

    
# auth/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

@extend_schema(
    tags=["Auth"],
    summary="Logout user",
    description="""Logout the current user by invalidating the session.
    
    **Actions performed:**
    - Blacklists the refresh token (if token blacklisting is enabled)
    - Clears the Django session
    - Requires valid access token in Authorization header
    """,
    request=None,
    responses={
        205: OpenApiResponse(description="Logged out successfully"),
        401: OpenApiResponse(description="Unauthorized - Invalid or missing access token"),
    },
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.session.get("refresh_token")

        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass

        request.session.flush()  # clears entire session

        return Response(
            {"detail": "Logged out successfully"},
            status=205
        )


@extend_schema(tags=["Auth"])
class AuthTokenObtainPairView(TokenObtainPairView):
    """SimpleJWT token pair endpoint tagged for Swagger grouping."""


@extend_schema(tags=["Auth"])
class AuthTokenRefreshView(TokenRefreshView):
    """SimpleJWT token refresh endpoint tagged for Swagger grouping."""


@extend_schema(tags=["Auth"])
class AuthTokenVerifyView(TokenVerifyView):
    """SimpleJWT token verify endpoint tagged for Swagger grouping."""


@extend_schema(exclude=True)
class HiddenTokenObtainPairView(AuthTokenObtainPairView):
    """Project-level token endpoint hidden from Swagger."""


@extend_schema(exclude=True)
class HiddenTokenRefreshView(AuthTokenRefreshView):
    """Project-level token refresh endpoint hidden from Swagger."""


@extend_schema(exclude=True)
class HiddenTokenVerifyView(AuthTokenVerifyView):
    """Project-level token verify endpoint hidden from Swagger."""

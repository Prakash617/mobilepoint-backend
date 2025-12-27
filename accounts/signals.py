from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.models import Site # Import Site model

from .models import User

@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created and not instance.is_verified and not instance.is_superuser:
        # Generate a token for email verification
        token = RefreshToken.for_user(instance).access_token

        # Get the current site domain dynamically
        current_site = Site.objects.get_current()
        domain = current_site.domain

        # Build the verification URL
        relative_link = reverse("verify-email")
        verification_url = f"http://{domain}{relative_link}?token={str(token)}"

        # Send the verification email
        subject = "Verify your email"
        message = f"Hi {instance.first_name}, please use this link to verify your email:\n{verification_url}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list)

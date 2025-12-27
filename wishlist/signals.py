from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Wishlist


@receiver(post_save, sender=User)
def create_user_wishlist(sender, instance, created, **kwargs):
    """Automatically create wishlist when user is created"""
    if created:
        Wishlist.objects.create(user=instance)


# wishlist/apps.py
from django.apps import AppConfig


class WishlistConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wishlist'
    
    def ready(self):
        import wishlist.signals
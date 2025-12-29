from django.urls import path, include
from mobilepoint.urls import router
from .api_views import (
    CarouselViewSet, AdvertisementViewSet, 
    # BannerViewSet,
    # TestimonialViewSet, FAQViewSet,
    NewsletterSubscriberViewSet,
    ContactMessageViewSet, SiteSettingsViewSet, CuratedItemViewSet
)
router.register(r'carousels', CarouselViewSet, basename='carousel')
router.register(r'advertisements', AdvertisementViewSet, basename='advertisement')
# router.register(r'banners', BannerViewSet, basename='banner')
# router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
# router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'newsletter', NewsletterSubscriberViewSet, basename='newsletter')
router.register(r'contact', ContactMessageViewSet, basename='contact')
router.register(r'settings', SiteSettingsViewSet, basename='settings')
router.register(r"curated", CuratedItemViewSet, basename="curated")
router.register(r'site-settings', SiteSettingsViewSet, basename='site-settings')


app_name = 'website'

urlpatterns = [
    path('api/', include(router.urls)),
]
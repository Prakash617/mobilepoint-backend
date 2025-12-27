from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from .models import (
    Carousel, CarouselSlide, Advertisement, Banner,
    Testimonial, FAQ, NewsletterSubscriber, ContactMessage, SiteSettings , CuratedItem
)
from .serializers import (
    CarouselSerializer, AdvertisementSerializer, BannerSerializer,
    TestimonialSerializer, FAQSerializer, NewsletterSubscriberSerializer,
    ContactMessageSerializer, SiteSettingsSerializer ,CuratedItemSerializer
)


class CarouselViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Carousel.objects.filter(is_active=True).prefetch_related('slides')
    serializer_class = CarouselSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['position']
    
    @action(detail=False, methods=['get'])
    def by_position(self, request):
        """Get carousels by position"""
        position = request.query_params.get('position', 'home_main')
        carousels = self.get_queryset().filter(position=position)
        serializer = self.get_serializer(carousels, many=True)
        return Response(serializer.data)


class AdvertisementViewSet(viewsets.ModelViewSet):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ad_type', 'position', 'is_active']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'track_impression', 'track_click']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        
        # Public users only see active, valid ads
        now = timezone.now()
        return self.queryset.filter(
            is_active=True,
            start_date__lte=now
        ).exclude(
            end_date__lt=now
        )
    
    @action(detail=False, methods=['get'])
    def by_position(self, request):
        """Get ads by position"""
        position = request.query_params.get('position')
        device = request.query_params.get('device', 'desktop')  # desktop or mobile
        
        if not position:
            return Response(
                {'error': 'Position parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ads = self.get_queryset().filter(position=position)
        
        # Filter by device
        if device == 'mobile':
            ads = ads.filter(show_on_mobile=True)
        else:
            ads = ads.filter(show_on_desktop=True)
        
        # Only return valid ads
        valid_ads = [ad for ad in ads if ad.is_valid()]
        
        serializer = self.get_serializer(valid_ads, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def track_impression(self, request, pk=None):
        """Track ad impression"""
        ad = self.get_object()
        ad.increment_impression()
        return Response({'status': 'impression tracked'})
    
    
    # http://127.0.0.1:8000/api/advertisements/1/track_click/
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def track_click(self, request, pk=None):
        """Track ad click"""
        ad = self.get_object()
        ad.increment_click()
        return Response({'status': 'click tracked'})


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['banner_type', 'position', 'is_active']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        
        # Public users only see active, valid banners
        return self.queryset.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active banners"""
        banners = [b for b in self.get_queryset() if b.is_valid()]
        serializer = self.get_serializer(banners, many=True)
        return Response(serializer.data)


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.filter(is_active=True)
    serializer_class = TestimonialSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_featured', 'rating', 'product']
    ordering_fields = ['created_at', 'rating', 'order']
    ordering = ['order', '-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured testimonials"""
        testimonials = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(testimonials, many=True)
        return Response(serializer.data)


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['question', 'answer']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'mark_helpful']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when FAQ is viewed"""
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def mark_helpful(self, request, pk=None):
        """Mark FAQ as helpful"""
        faq = self.get_object()
        faq.helpful_count += 1
        faq.save(update_fields=['helpful_count'])
        return Response({'status': 'marked as helpful'})
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get FAQs grouped by category"""
        categories = dict(FAQ.CATEGORY_CHOICES)
        result = {}
        
        for category_key, category_name in categories.items():
            faqs = self.get_queryset().filter(category=category_key)
            result[category_key] = {
                'name': category_name,
                'faqs': self.get_serializer(faqs, many=True).data
            }
        
        return Response(result)


class NewsletterSubscriberViewSet(viewsets.ModelViewSet):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def subscribe(self, request):
        """Subscribe to newsletter"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Successfully subscribed to newsletter'},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def unsubscribe(self, request):
        """Unsubscribe from newsletter"""
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            subscriber.is_active = False
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save()
            return Response({'message': 'Successfully unsubscribed'})
        except NewsletterSubscriber.DoesNotExist:
            return Response(
                {'error': 'Email not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_read', 'replied']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        message.is_read = True
        message.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reply(self, request, pk=None):
        """Reply to contact message"""
        message = self.get_object()
        reply_text = request.data.get('reply_message')
        
        if not reply_text:
            return Response(
                {'error': 'Reply message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.reply_message = reply_text
        message.replied = True
        message.replied_at = timezone.now()
        message.is_read = True
        message.save()
        
        # Here you can add email sending logic
        
        return Response({'status': 'reply sent'})


class SiteSettingsViewSet(viewsets.ModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def list(self, request, *args, **kwargs):
        """Get site settings (always returns single instance)"""
        settings, created = SiteSettings.objects.get_or_create(id=1)
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

class CuratedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for 'Curated For You' homepage section
    """
    serializer_class = CuratedItemSerializer

    def get_queryset(self):
        return (
            CuratedItem.objects
            .filter(is_active=True)
            .order_by("position", "-created_at")
        )
from rest_framework import serializers
from .models import (
    Carousel, CarouselSlide, Advertisement, 
    # Banner, 
    # Testimonial, FAQ, 
    NewsletterSubscriber, ContactMessage, SiteSettings, CuratedItem
)


class CarouselSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselSlide
        fields = [
            'id', 'title', 'subtitle', 'description', 'image',
            'link_url', 'link_text', 'product', 'order', 'is_active'
        ]


class CarouselSerializer(serializers.ModelSerializer):
    slides = CarouselSlideSerializer(many=True, read_only=True)
    
    class Meta:
        model = Carousel
        fields = [
            'id', 'title', 'position', 'is_active', 'auto_play', 
            'auto_play_speed', 'show_indicators', 'show_arrows', 
            'order', 'slides', 'created_at'
        ]


class AdvertisementSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    ctr = serializers.SerializerMethodField()
    
    class Meta:
        model = Advertisement
        fields = [
            'id', 'title', 'ad_type', 'position', 'image', 'mobile_image',
            'video_url', 'html_content', 'link_url', 'open_in_new_tab',
            'is_active', 'start_date', 'end_date', 'show_on_mobile',
            'show_on_desktop', 'max_impressions', 'current_impressions',
            'click_count', 'ctr', 'is_valid', 'order'
        ]
        read_only_fields = ['current_impressions', 'click_count']
    
    def get_ctr(self, obj):
        """Calculate click-through rate"""
        if obj.current_impressions > 0:
            return round((obj.click_count / obj.current_impressions) * 100, 2)
        return 0


# class BannerSerializer(serializers.ModelSerializer):
#     is_valid = serializers.BooleanField(read_only=True)
    
#     class Meta:
#         model = Banner
#         fields = [
#             'id', 'title', 'banner_type', 'position', 'heading', 'subheading',
#             'description', 'image', 'mobile_image', 'background_color',
#             'text_color', 'button_text', 'button_link', 'button_color',
#             'is_active', 'start_date', 'end_date', 'is_valid', 'order'
#         ]


# class TestimonialSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Testimonial
#         fields = [
#             'id', 'customer_name', 'customer_image', 'designation',
#             'company', 'rating', 'title', 'content', 'product',
#             'is_featured', 'is_active', 'created_at'
#         ]


# class FAQSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FAQ
#         fields = [
#             'id', 'category', 'question', 'answer', 'is_active',
#             'order', 'view_count', 'helpful_count', 'created_at'
#         ]
#         read_only_fields = ['view_count', 'helpful_count']


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['id', 'email', 'name', 'is_active', 'subscribed_at']
        read_only_fields = ['subscribed_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'phone', 'subject', 'message',
            'is_read', 'replied', 'reply_message', 'replied_at', 'created_at'
        ]
        read_only_fields = ['is_read', 'replied', 'replied_at', 'created_at']


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        
class CuratedItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    linked_type = serializers.SerializerMethodField()

    class Meta:
        model = CuratedItem
        fields = (
            "id",
            "title",
            "subtitle",
            "image",
            # "badge_text",
            # "badge_color",
            "button_text",
            "link_url",
            "linked_type",
            "position",
        )

    def get_image(self, obj):
        if obj.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_linked_type(self, obj):
        if obj.product:
            return "product"
        if obj.category:
            return "category"
        return "custom"

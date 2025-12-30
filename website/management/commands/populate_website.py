from django.core.management.base import BaseCommand
from django.utils import timezone

from website.models import (
    SiteSettings,
    Carousel,
    Advertisement,
    NewsletterSubscriber,
    ContactMessage,
)


class Command(BaseCommand):
    help = "Populate initial website data (SiteSettings, Carousel, Advertisement, sample subscriber/message)"

    def handle(self, *args, **options):
        created = []

        ss_defaults = {
            'site_tagline': 'Welcome to My Store',
            'site_description': 'Default description',
            'email': 'noreply@example.com',
            'phone': '+0000000000',
        }
        ss, ss_created = SiteSettings.objects.get_or_create(site_name='My Store', defaults=ss_defaults)
        if ss_created:
            created.append('SiteSettings')
        else:
            changed = False
            for k, v in ss_defaults.items():
                if not getattr(ss, k):
                    setattr(ss, k, v)
                    changed = True
            if changed:
                ss.save()

        carousel, c_created = Carousel.objects.get_or_create(
            title='Homepage Main', defaults={'position': 'home_main', 'is_active': True, 'order': 0}
        )
        if c_created:
            created.append('Carousel: Homepage Main')

        ad_defaults = {
            'ad_type': 'photo',
            'position': 'home_top',
            'is_active': True,
            'start_date': timezone.now(),
        }
        ad, ad_created = Advertisement.objects.get_or_create(title='Home Top Sample', defaults=ad_defaults)
        if ad_created:
            created.append('Advertisement: Home Top Sample')

        ns, ns_created = NewsletterSubscriber.objects.get_or_create(
            email='subscriber@example.com', defaults={'name': 'Sample Subscriber'}
        )
        if ns_created:
            created.append('NewsletterSubscriber: subscriber@example.com')

        cm, cm_created = ContactMessage.objects.get_or_create(
            email='visitor@example.com', subject='Sample Message',
            defaults={'name': 'Visitor', 'message': 'Hello from populate command.'}
        )
        if cm_created:
            created.append('ContactMessage: Sample Message')

        if created:
            self.stdout.write(self.style.SUCCESS('Populate complete. Created: %s' % (', '.join(created))))
        else:
            self.stdout.write('Nothing created — items already exist or no changes needed.')

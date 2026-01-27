from django.core.management.base import BaseCommand
import random
from accounts.models import User
from product.models import Product
from reviews.models import ProductReview


class Command(BaseCommand):
    help = 'Creates sample product reviews for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of reviews to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing reviews before creating sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing reviews...'))
            ProductReview.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ All reviews cleared'))
        
        count = options['count']
        self.stdout.write(f'Creating {count} sample reviews...')

        users = list(User.objects.filter(is_active=True))
        products = list(Product.objects.filter(is_active=True))

        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return

        if not products:
            self.stdout.write(self.style.ERROR('No products found. Please create products first.'))
            return

        review_titles = {
            5: [
                'Excellent product!', 'Best purchase ever!', 'Absolutely love it!',
                'Perfect!', 'Highly recommend!', 'Amazing quality!', 'Worth every penny!',
                'Exceeded expectations!', 'Five stars!', 'Outstanding!'
            ],
            4: [
                'Very good product', 'Great quality', 'Really happy with it',
                'Good value', 'Pleased with purchase', 'Works great', 'Nice product',
                'Would buy again', 'Solid choice', 'Pretty good'
            ],
            3: [
                'It\'s okay', 'Average product', 'Meets expectations',
                'Not bad', 'Decent', 'Fair quality', 'Acceptable',
                'Could be better', 'Works as expected', 'Satisfactory'
            ],
            2: [
                'Disappointed', 'Not great', 'Expected better',
                'Below average', 'Had issues', 'Not impressed', 'Subpar',
                'Needs improvement', 'Not worth it', 'Mediocre'
            ],
            1: [
                'Terrible', 'Very disappointed', 'Do not buy',
                'Waste of money', 'Poor quality', 'Defective', 'Awful',
                'Not recommended', 'Regret buying', 'Horrible'
            ]
        }

        review_comments = {
            5: [
                'This product exceeded all my expectations. The quality is outstanding and it works perfectly. I would highly recommend this to anyone looking for a reliable product.',
                'Absolutely amazing! The build quality is excellent and the performance is top-notch. Best purchase I\'ve made this year.',
                'I\'m thoroughly impressed with this product. It\'s exactly what I needed and the quality is exceptional. Five stars!',
                'Perfect in every way. Great design, excellent functionality, and outstanding value for money. Couldn\'t be happier!',
            ],
            4: [
                'Very pleased with this purchase. The product works well and the quality is good. Minor issues but overall a great buy.',
                'Good product overall. Does what it\'s supposed to do and the quality is solid. Would recommend.',
                'Happy with my purchase. The product met my expectations and works great. Good value for the price.',
                'Really like this product. Quality is good and it works as advertised. A few minor things could be improved but very satisfied.',
            ],
            3: [
                'It\'s an okay product. Does the job but nothing special. Quality is average and there are some minor issues.',
                'Decent product for the price. Works as expected but could be better. Not disappointed but not amazed either.',
                'Average product. It works but has some limitations. For the price, it\'s acceptable.',
                'Fair quality. Does what it\'s supposed to do but I expected a bit more. It\'s okay.',
            ],
            2: [
                'Somewhat disappointed with this product. The quality isn\'t great and I\'ve had some issues. Expected better.',
                'Not very happy with this purchase. It works but has several problems. Quality could be much better.',
                'Below my expectations. The product has some issues and the quality is questionable. Wouldn\'t buy again.',
                'Had high hopes but was let down. Multiple issues and the quality is not what I expected for the price.',
            ],
            1: [
                'Very disappointed. The product doesn\'t work as advertised and the quality is terrible. Would not recommend.',
                'Waste of money. Poor quality and doesn\'t function properly. Very unhappy with this purchase.',
                'Horrible product. Multiple defects and poor performance. Save your money and look elsewhere.',
                'Extremely disappointed. The product is defective and the quality is abysmal. Do not buy this.',
            ]
        }

        reviews_created = 0
        approved_count = 0

        for i in range(count):
            user = random.choice(users)
            product = random.choice(products)

            # Check if user already reviewed this product
            if ProductReview.objects.filter(user=user, product=product).exists():
                continue

            # Rating distribution: more 4-5 stars, fewer 1-2 stars
            rating = random.choices(
                [1, 2, 3, 4, 5],
                weights=[5, 10, 20, 30, 35]  # Weighted towards higher ratings
            )[0]

            # 80% of reviews are approved
            is_approved = random.random() < 0.8

            review = ProductReview.objects.create(
                product=product,
                user=user,
                rating=rating,
                title=random.choice(review_titles[rating]),
                comment=random.choice(review_comments[rating]),
                is_approved=is_approved,
            )
            reviews_created += 1
            if is_approved:
                approved_count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Successfully created {reviews_created} reviews'))
        self.stdout.write(self.style.SUCCESS(f'  {approved_count} approved, {reviews_created - approved_count} pending'))
        
        # Calculate average rating
        avg_rating = ProductReview.objects.filter(is_approved=True).aggregate(
            avg=models.Avg('rating')
        )['avg'] or 0
        
        self.stdout.write(self.style.SUCCESS(f'  Average rating: {avg_rating:.2f}/5.0'))


from django.db import models

from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Creates sample users for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of users to create',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f'Creating {count} sample users...')

        first_names = [
            'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'James', 'Emma',
            'Robert', 'Olivia', 'William', 'Ava', 'Richard', 'Isabella', 'Joseph',
            'Sophia', 'Thomas', 'Mia', 'Charles', 'Charlotte', 'Christopher', 'Amelia',
            'Daniel', 'Harper', 'Matthew', 'Evelyn'
        ]

        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Thompson', 'White', 'Harris', 'Clark'
        ]

        users_created = 0

        for i in range(count):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(f'  User {email} already exists, skipping...')
                continue

            user = User.objects.create_user(
                email=email,
                password='password123',  # Default password for testing
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=True,
            )
            users_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Successfully created {users_created} users'))
        self.stdout.write(self.style.SUCCESS(f'  Total users in database: {User.objects.count()}'))

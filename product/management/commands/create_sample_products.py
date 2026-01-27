from django.core.management.base import BaseCommand
from product.models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant
)
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Creates sample products with variants for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing data before creating sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            ProductVariant.objects.all().delete()
            VariantAttributeValue.objects.all().delete()
            VariantAttribute.objects.all().delete()
            Product.objects.all().delete()
            Brand.objects.all().delete()
            # Delete child categories first, then parent categories
            Category.objects.filter(parent__isnull=False).delete()
            Category.objects.filter(parent__isnull=True).delete()
            self.stdout.write(self.style.SUCCESS('✓ All data cleared'))
        
        self.stdout.write('Creating sample data...')

        # Categories
        electronics, _ = Category.objects.get_or_create(
            slug='electronics',
            defaults={'name': 'Electronics', 'description': 'Electronic devices and gadgets'}
        )
        smartphones, _ = Category.objects.get_or_create(
            slug='smartphones',
            defaults={'name': 'Smartphones', 'parent': electronics, 'description': 'Mobile phones and accessories'}
        )
        laptops, _ = Category.objects.get_or_create(
            slug='laptops',
            defaults={'name': 'Laptops', 'parent': electronics, 'description': 'Laptop computers'}
        )

        # Brands
        apple, _ = Brand.objects.get_or_create(slug='apple', defaults={'name': 'Apple'})
        samsung, _ = Brand.objects.get_or_create(slug='samsung', defaults={'name': 'Samsung'})
        dell, _ = Brand.objects.get_or_create(slug='dell', defaults={'name': 'Dell'})
        
        # Associate brands with categories
        apple.category.add(smartphones, electronics)
        samsung.category.add(smartphones, electronics)
        dell.category.add(laptops, electronics)

        # Variant Attributes
        color_attr, _ = VariantAttribute.objects.get_or_create(name='Color', defaults={'display_name': 'Choose Color'})
        memory_attr, _ = VariantAttribute.objects.get_or_create(name='Memory', defaults={'display_name': 'Choose Memory'})
        storage_attr, _ = VariantAttribute.objects.get_or_create(name='Storage', defaults={'display_name': 'Choose Storage'})
        ram_attr, _ = VariantAttribute.objects.get_or_create(name='RAM', defaults={'display_name': 'Choose RAM'})

        # Variant Attribute Values
        red, _ = VariantAttributeValue.objects.get_or_create(attribute=color_attr, types='color', value='Red', defaults={'color_code': '#FF0000'})
        blue, _ = VariantAttributeValue.objects.get_or_create(attribute=color_attr, types='color', value='Blue', defaults={'color_code': '#0000FF'})
        black, _ = VariantAttributeValue.objects.get_or_create(attribute=color_attr, types='color', value='Black', defaults={'color_code': '#000000'})
        silver, _ = VariantAttributeValue.objects.get_or_create(attribute=color_attr, types='color', value='Silver', defaults={'color_code': '#C0C0C0'})

        mem_128gb, _ = VariantAttributeValue.objects.get_or_create(attribute=memory_attr, types='text', value='128GB')
        mem_256gb, _ = VariantAttributeValue.objects.get_or_create(attribute=memory_attr, types='text', value='256GB')
        mem_512gb, _ = VariantAttributeValue.objects.get_or_create(attribute=memory_attr, types='text', value='512GB')

        storage_256gb, _ = VariantAttributeValue.objects.get_or_create(attribute=storage_attr, types='text', value='256GB SSD')
        storage_512gb, _ = VariantAttributeValue.objects.get_or_create(attribute=storage_attr, types='text', value='512GB SSD')
        storage_1tb, _ = VariantAttributeValue.objects.get_or_create(attribute=storage_attr, types='text', value='1TB SSD')

        ram_8gb, _ = VariantAttributeValue.objects.get_or_create(attribute=ram_attr, types='text', value='8GB')
        ram_16gb, _ = VariantAttributeValue.objects.get_or_create(attribute=ram_attr, types='text', value='16GB')
        ram_32gb, _ = VariantAttributeValue.objects.get_or_create(attribute=ram_attr, types='text', value='32GB')

        # Products
        iphone, _ = Product.objects.get_or_create(
            slug='iphone-15',
            defaults={
                'name': 'iPhone 15',
                'description': 'The latest iPhone with advanced features.',
                'category': smartphones,
                'brand': apple,
                'base_price': 799.00,
                'specifications': "<ul><li>Processor: A16 Bionic</li><li>Screen: 6.1-inch</li></ul>",
                'is_active': True,
                'is_featured': True
            }
        )

        # iPhone Variants
        if not ProductVariant.objects.filter(product=iphone).exists():
            iphone_variants_data = [
                {'attributes': [black, mem_128gb], 'price': 799.00, 'stock': 50},
                {'attributes': [black, mem_256gb], 'price': 899.00, 'stock': 40},
                {'attributes': [blue, mem_128gb], 'price': 799.00, 'stock': 45},
                {'attributes': [blue, mem_256gb], 'price': 899.00, 'stock': 35},
            ]
            for i, vdata in enumerate(iphone_variants_data):
                variant = ProductVariant.objects.create(
                    product=iphone,
                    price=vdata['price'],
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                variant.variant_attributes.set(vdata['attributes'])

        # Samsung Galaxy S24
        galaxy_s24, _ = Product.objects.get_or_create(
            slug='samsung-galaxy-s24',
            defaults={
                'name': 'Samsung Galaxy S24',
                'description': 'Premium Android smartphone with advanced AI features.',
                'category': smartphones,
                'brand': samsung,
                'base_price': 699.00,
                'specifications': "<ul><li>Processor: Snapdragon 8 Gen 3</li><li>Screen: 6.2-inch Dynamic AMOLED</li><li>Camera: 50MP Main</li></ul>",
                'is_active': True,
                'is_featured': True
            }
        )

        # Galaxy S24 Variants
        if not ProductVariant.objects.filter(product=galaxy_s24).exists():
            s24_variants_data = [
                {'attributes': [black, mem_128gb], 'price': 699.00, 'stock': 60},
                {'attributes': [black, mem_256gb], 'price': 799.00, 'stock': 50},
                {'attributes': [silver, mem_128gb], 'price': 699.00, 'stock': 55},
                {'attributes': [silver, mem_256gb], 'price': 799.00, 'stock': 45},
            ]
            for i, vdata in enumerate(s24_variants_data):
                variant = ProductVariant.objects.create(
                    product=galaxy_s24,
                    price=vdata['price'],
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                variant.variant_attributes.set(vdata['attributes'])

        # Samsung Galaxy A54
        galaxy_a54, _ = Product.objects.get_or_create(
            slug='samsung-galaxy-a54',
            defaults={
                'name': 'Samsung Galaxy A54',
                'description': 'Mid-range smartphone with excellent value.',
                'category': smartphones,
                'brand': samsung,
                'base_price': 399.00,
                'specifications': "<ul><li>Processor: Exynos 1380</li><li>Screen: 6.4-inch Super AMOLED</li><li>Camera: 50MP Main</li></ul>",
                'is_active': True,
                'is_featured': False
            }
        )

        # Galaxy A54 Variants
        if not ProductVariant.objects.filter(product=galaxy_a54).exists():
            a54_variants_data = [
                {'attributes': [black, mem_128gb], 'price': 399.00, 'stock': 70},
                {'attributes': [black, mem_256gb], 'price': 449.00, 'stock': 60},
                {'attributes': [blue, mem_128gb], 'price': 399.00, 'stock': 65},
            ]
            for i, vdata in enumerate(a54_variants_data):
                variant = ProductVariant.objects.create(
                    product=galaxy_a54,
                    price=vdata['price'],
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                variant.variant_attributes.set(vdata['attributes'])

        # Dell XPS 15
        dell_xps15, _ = Product.objects.get_or_create(
            slug='dell-xps-15',
            defaults={
                'name': 'Dell XPS 15',
                'description': 'Premium laptop for professionals and creators.',
                'category': laptops,
                'brand': dell,
                'base_price': 1299.00,
                'specifications': "<ul><li>Processor: Intel Core i7-13th Gen</li><li>Display: 15.6-inch FHD+</li><li>Graphics: NVIDIA GeForce RTX 4050</li></ul>",
                'is_active': True,
                'is_featured': True
            }
        )

        # Dell XPS 15 Variants
        if not ProductVariant.objects.filter(product=dell_xps15).exists():
            xps15_variants_data = [
                {'attributes': [ram_16gb, storage_512gb], 'price': 1299.00, 'stock': 30},
                {'attributes': [ram_16gb, storage_1tb], 'price': 1499.00, 'stock': 25},
                {'attributes': [ram_32gb, storage_512gb], 'price': 1599.00, 'stock': 20},
                {'attributes': [ram_32gb, storage_1tb], 'price': 1799.00, 'stock': 15},
            ]
            for i, vdata in enumerate(xps15_variants_data):
                variant = ProductVariant.objects.create(
                    product=dell_xps15,
                    price=vdata['price'],
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                variant.variant_attributes.set(vdata['attributes'])

        # Dell Inspiron 15
        dell_inspiron15, _ = Product.objects.get_or_create(
            slug='dell-inspiron-15',
            defaults={
                'name': 'Dell Inspiron 15',
                'description': 'Reliable everyday laptop for work and study.',
                'category': laptops,
                'brand': dell,
                'base_price': 599.00,
                'specifications': "<ul><li>Processor: Intel Core i5-12th Gen</li><li>Display: 15.6-inch FHD</li><li>Graphics: Intel Iris Xe</li></ul>",
                'is_active': True,
                'is_featured': False
            }
        )

        # Dell Inspiron 15 Variants
        if not ProductVariant.objects.filter(product=dell_inspiron15).exists():
            inspiron15_variants_data = [
                {'attributes': [ram_8gb, storage_256gb], 'price': 599.00, 'stock': 50},
                {'attributes': [ram_8gb, storage_512gb], 'price': 699.00, 'stock': 40},
                {'attributes': [ram_16gb, storage_512gb], 'price': 799.00, 'stock': 35},
            ]
            for i, vdata in enumerate(inspiron15_variants_data):
                variant = ProductVariant.objects.create(
                    product=dell_inspiron15,
                    price=vdata['price'],
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                variant.variant_attributes.set(vdata['attributes'])

        # iPhone 14
        iphone14, _ = Product.objects.get_or_create(
            slug='iphone-14',
            defaults={
                'name': 'iPhone 14',
                'description': 'Previous generation iPhone with great performance.',
                'category': smartphones,
                'brand': apple,
                'base_price': 699.00,
                'specifications': "<ul><li>Processor: A15 Bionic</li><li>Screen: 6.1-inch</li><li>Camera: Dual 12MP</li></ul>",
                'is_active': True,
                'is_featured': False
            }
        )

        # iPhone 14 Variants
        if not ProductVariant.objects.filter(product=iphone14).exists():
            iphone14_variants_data = [
                {'attributes': [black, mem_128gb], 'price': 699.00, 'stock': 55},
                {'attributes': [black, mem_256gb], 'price': 799.00, 'stock': 45},
                {'attributes': [red, mem_128gb], 'price': 699.00, 'stock': 40},
                {'attributes': [blue, mem_128gb], 'price': 699.00, 'stock': 50},
            ]
            for i, vdata in enumerate(iphone14_variants_data):
                variant = ProductVariant.objects.create(
                    product=iphone14,
                    price=vdata['price'],
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                variant.variant_attributes.set(vdata['attributes'])

        # ===== PRODUCTS WITHOUT VARIANTS =====
        # These products don't have color/memory options - simple products with base price only
        
        # Apple AirPods Pro (No variants - simple product)
        Product.objects.get_or_create(
            slug='apple-airpods-pro',
            defaults={
                'name': 'Apple AirPods Pro (2nd Gen)',
                'description': 'Premium wireless earbuds with active noise cancellation.',
                'category': electronics,
                'brand': apple,
                'base_price': 249.00,
                'specifications': "<ul><li>Active Noise Cancellation</li><li>Adaptive Transparency</li><li>Spatial Audio</li><li>MagSafe Charging Case</li></ul>",
                'is_active': True,
                'is_featured': True
            }
        )

        # Samsung Galaxy Buds2 Pro (No variants)
        Product.objects.get_or_create(
            slug='samsung-galaxy-buds2-pro',
            defaults={
                'name': 'Samsung Galaxy Buds2 Pro',
                'description': 'High-quality wireless earbuds with intelligent ANC.',
                'category': electronics,
                'brand': samsung,
                'base_price': 199.00,
                'specifications': "<ul><li>Intelligent ANC</li><li>360 Audio</li><li>Hi-Fi Sound</li><li>IPX7 Water Resistant</li></ul>",
                'is_active': True,
                'is_featured': False
            }
        )

        # Dell USB-C Hub (No variants)
        Product.objects.get_or_create(
            slug='dell-usb-c-hub',
            defaults={
                'name': 'Dell USB-C Mobile Adapter',
                'description': 'Compact USB-C hub with multiple ports for connectivity.',
                'category': electronics,
                'brand': dell,
                'base_price': 79.00,
                'specifications': "<ul><li>USB-C Power Delivery</li><li>HDMI Port</li><li>2x USB-A Ports</li><li>Ethernet Port</li></ul>",
                'is_active': True,
                'is_featured': False
            }
        )

        self.stdout.write(self.style.SUCCESS(f'✓ Sample data created successfully'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {Category.objects.count()} categories'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {Brand.objects.count()} brands'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {Product.objects.count()} products'))
        self.stdout.write(self.style.SUCCESS(f'  - Created {ProductVariant.objects.count()} product variants'))

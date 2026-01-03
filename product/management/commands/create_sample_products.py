from django.core.management.base import BaseCommand
from product.models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant, ProductVariantAttributeValue
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
            ProductVariantAttributeValue.objects.all().delete()
            ProductVariant.objects.all().delete()
            VariantAttributeValue.objects.all().delete()
            VariantAttribute.objects.all().delete()
            Product.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()
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
                {'color': black, 'memory': mem_128gb, 'price': 799.00, 'stock': 50},
                {'color': black, 'memory': mem_256gb, 'price': 899.00, 'stock': 40},
                {'color': blue, 'memory': mem_128gb, 'price': 799.00, 'stock': 45},
                {'color': blue, 'memory': mem_256gb, 'price': 899.00, 'stock': 35},
            ]
            for i, vdata in enumerate(iphone_variants_data):
                variant = ProductVariant.objects.create(
                    product=iphone,
                    selling_price=vdata['price'],
                    regular_price=vdata['price'] + 100,
                    stock_quantity=vdata['stock'],
                    is_default=(i == 0)
                )
                ProductVariantAttributeValue.objects.create(variant=variant, attribute_value=vdata['color'])
                ProductVariantAttributeValue.objects.create(variant=variant, attribute_value=vdata['memory'])

        self.stdout.write(self.style.SUCCESS('✓ Sample data created successfully'))

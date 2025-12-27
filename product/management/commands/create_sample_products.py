"""
Sample data creation script for testing the product variant system.
Save this as: products/management/commands/create_sample_products.py

Run with: python manage.py create_sample_products
"""

from django.core.management.base import BaseCommand
from product.models import (
    Category, Brand, Product, VariantAttribute, VariantAttributeValue,
    ProductVariant, ProductVariantAttributeValue
)


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
        
        # Create Categories (get_or_create to avoid duplicates)
        electronics, created = Category.objects.get_or_create(
            slug='electronics',
            defaults={
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Electronics category created'))
        else:
            self.stdout.write('- Electronics category already exists')
        
        smartphones, created = Category.objects.get_or_create(
            slug='smartphones',
            defaults={
                'name': 'Smartphones',
                'parent': electronics,
                'description': 'Mobile phones and accessories'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Smartphones category created'))
        else:
            self.stdout.write('- Smartphones category already exists')
        
        laptops, created = Category.objects.get_or_create(
            slug='laptops',
            defaults={
                'name': 'Laptops',
                'parent': electronics,
                'description': 'Laptop computers'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Laptops category created'))
        else:
            self.stdout.write('- Laptops category already exists')
        
        # Create Brands (get_or_create to avoid duplicates)
        apple, created = Brand.objects.get_or_create(
            slug='apple',
            defaults={
                'name': 'Apple',
                'description': 'Apple Inc.'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Apple brand created'))
        else:
            self.stdout.write('- Apple brand already exists')
        
        samsung, created = Brand.objects.get_or_create(
            slug='samsung',
            defaults={
                'name': 'Samsung',
                'description': 'Samsung Electronics'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Samsung brand created'))
        else:
            self.stdout.write('- Samsung brand already exists')
        
        dell, created = Brand.objects.get_or_create(
            slug='dell',
            defaults={
                'name': 'Dell',
                'description': 'Dell Technologies'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Dell brand created'))
        else:
            self.stdout.write('- Dell brand already exists')
        
        # Create Variant Attributes
        color_attr, created = VariantAttribute.objects.get_or_create(
            name='Color',
            defaults={'display_name': 'Choose Color'}
        )
        
        memory_attr, created = VariantAttribute.objects.get_or_create(
            name='Memory',
            defaults={'display_name': 'Choose Memory'}
        )
        
        storage_attr, created = VariantAttribute.objects.get_or_create(
            name='Storage',
            defaults={'display_name': 'Choose Storage'}
        )
        
        ram_attr, created = VariantAttribute.objects.get_or_create(
            name='RAM',
            defaults={'display_name': 'Choose RAM'}
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Variant Attributes created/verified'))
        
        # Create Variant Attribute Values - Colors
        red, _ = VariantAttributeValue.objects.get_or_create(
            attribute=color_attr,
            value='Red',
            defaults={'color_code': '#FF0000'}
        )
        
        blue, _ = VariantAttributeValue.objects.get_or_create(
            attribute=color_attr,
            value='Blue',
            defaults={'color_code': '#0000FF'}
        )
        
        black, _ = VariantAttributeValue.objects.get_or_create(
            attribute=color_attr,
            value='Black',
            defaults={'color_code': '#000000'}
        )
        
        silver, _ = VariantAttributeValue.objects.get_or_create(
            attribute=color_attr,
            value='Silver',
            defaults={'color_code': '#C0C0C0'}
        )
        
        # Memory values (for smartphones)
        mem_128gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=memory_attr,
            value='128GB'
        )
        
        mem_256gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=memory_attr,
            value='256GB'
        )
        
        mem_512gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=memory_attr,
            value='512GB'
        )
        
        # Storage values (for laptops)
        storage_256gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=storage_attr,
            value='256GB SSD'
        )
        
        storage_512gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=storage_attr,
            value='512GB SSD'
        )
        
        storage_1tb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=storage_attr,
            value='1TB SSD'
        )
        
        # RAM values
        ram_8gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=ram_attr,
            value='8GB'
        )
        
        ram_16gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=ram_attr,
            value='16GB'
        )
        
        ram_32gb, _ = VariantAttributeValue.objects.get_or_create(
            attribute=ram_attr,
            value='32GB'
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Variant Attribute Values created/verified'))
        
        # Create Product 1: iPhone 15
        iphone, created = Product.objects.get_or_create(
            slug='iphone-15',
            defaults={
                'name': 'iPhone 15',
                'description': 'The latest iPhone with advanced features and stunning design.',
                'category': smartphones,
                'brand': apple,
                'base_price': 799.00,
                'specifications': {
                    'processor': 'A16 Bionic',
                    'screen': '6.1-inch Super Retina XDR',
                    'camera': '48MP Main + 12MP Ultra Wide'
                },
                'is_active': True,
                'is_featured': True
            }
        )
        
        if created:
            # Create iPhone variants
            iphone_variants_data = [
                {'color': black, 'memory': mem_128gb, 'price': 799.00, 'stock': 50},
                {'color': black, 'memory': mem_256gb, 'price': 899.00, 'stock': 40},
                {'color': blue, 'memory': mem_128gb, 'price': 799.00, 'stock': 45},
                {'color': blue, 'memory': mem_256gb, 'price': 899.00, 'stock': 35},
            ]
            
            for i, variant_data in enumerate(iphone_variants_data):
                variant = ProductVariant.objects.create(
                    product=iphone,
                    sku=f'IPH15-{variant_data["color"].value[:3].upper()}-{variant_data["memory"].value}',
                    price=variant_data['price'],
                    compare_at_price=variant_data['price'] + 100,
                    stock_quantity=variant_data['stock'],
                    is_default=(i == 0)
                )
                
                # Link attributes to variant
                ProductVariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_value=variant_data['color']
                )
                
                ProductVariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_value=variant_data['memory']
                )
            
            self.stdout.write(self.style.SUCCESS('✓ iPhone 15 with variants created'))
        else:
            self.stdout.write('- iPhone 15 already exists')
        
        # Create Product 2: Samsung Galaxy S24
        galaxy, created = Product.objects.get_or_create(
            slug='samsung-galaxy-s24',
            defaults={
                'name': 'Samsung Galaxy S24',
                'description': 'Premium Android smartphone with cutting-edge technology.',
                'category': smartphones,
                'brand': samsung,
                'base_price': 699.00,
                'specifications': {
                    'processor': 'Snapdragon 8 Gen 3',
                    'screen': '6.2-inch Dynamic AMOLED',
                    'camera': '50MP Main + 12MP Ultra Wide + 10MP Telephoto'
                },
                'is_active': True,
                'is_featured': True
            }
        )
        
        if created:
            # Create Galaxy variants
            galaxy_variants_data = [
                {'color': black, 'memory': mem_128gb, 'price': 699.00, 'stock': 60},
                {'color': black, 'memory': mem_256gb, 'price': 799.00, 'stock': 50},
                {'color': silver, 'memory': mem_128gb, 'price': 699.00, 'stock': 55},
                {'color': silver, 'memory': mem_256gb, 'price': 799.00, 'stock': 45},
            ]
            
            for i, variant_data in enumerate(galaxy_variants_data):
                variant = ProductVariant.objects.create(
                    product=galaxy,
                    sku=f'S24-{variant_data["color"].value[:3].upper()}-{variant_data["memory"].value}',
                    price=variant_data['price'],
                    compare_at_price=variant_data['price'] + 80,
                    stock_quantity=variant_data['stock'],
                    is_default=(i == 0)
                )
                
                ProductVariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_value=variant_data['color']
                )
                
                ProductVariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_value=variant_data['memory']
                )
            
            self.stdout.write(self.style.SUCCESS('✓ Samsung Galaxy S24 with variants created'))
        else:
            self.stdout.write('- Samsung Galaxy S24 already exists')
        
        # Create Product 3: Dell XPS 15
        xps, created = Product.objects.get_or_create(
            slug='dell-xps-15',
            defaults={
                'name': 'Dell XPS 15',
                'description': 'High-performance laptop for professionals and creators.',
                'category': laptops,
                'brand': dell,
                'base_price': 1299.00,
                'specifications': {
                    'processor': 'Intel Core i7-13700H',
                    'screen': '15.6-inch FHD+ Display',
                    'graphics': 'NVIDIA GeForce RTX 4050'
                },
                'is_active': True,
                'is_featured': True
            }
        )
        
        if created:
            # Create XPS variants (RAM + Storage combinations)
            xps_variants_data = [
                {'ram': ram_8gb, 'storage': storage_256gb, 'price': 1299.00, 'stock': 30},
                {'ram': ram_8gb, 'storage': storage_512gb, 'price': 1399.00, 'stock': 25},
                {'ram': ram_16gb, 'storage': storage_512gb, 'price': 1599.00, 'stock': 20},
                {'ram': ram_16gb, 'storage': storage_1tb, 'price': 1799.00, 'stock': 15},
                {'ram': ram_32gb, 'storage': storage_1tb, 'price': 2099.00, 'stock': 10},
            ]
            
            for i, variant_data in enumerate(xps_variants_data):
                variant = ProductVariant.objects.create(
                    product=xps,
                    sku=f'XPS15-{variant_data["ram"].value}-{variant_data["storage"].value.split()[0]}',
                    price=variant_data['price'],
                    compare_at_price=variant_data['price'] + 200,
                    stock_quantity=variant_data['stock'],
                    is_default=(i == 0)
                )
                
                ProductVariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_value=variant_data['ram']
                )
                
                ProductVariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_value=variant_data['storage']
                )
            
            self.stdout.write(self.style.SUCCESS('✓ Dell XPS 15 with variants created'))
        else:
            self.stdout.write('- Dell XPS 15 already exists')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Categories: {Category.objects.count()}')
        self.stdout.write(f'Brands: {Brand.objects.count()}')
        self.stdout.write(f'Products: {Product.objects.count()}')
        self.stdout.write(f'Variant Attributes: {VariantAttribute.objects.count()}')
        self.stdout.write(f'Variant Attribute Values: {VariantAttributeValue.objects.count()}')
        self.stdout.write(f'Product Variants: {ProductVariant.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*50))
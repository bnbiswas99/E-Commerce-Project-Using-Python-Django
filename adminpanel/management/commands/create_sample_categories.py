from django.core.management.base import BaseCommand
from homepage.models import Category

class Command(BaseCommand):
    help = 'Create sample categories for testing'

    def handle(self, *args, **options):
        # Check existing categories
        existing_count = Category.objects.count()
        self.stdout.write(f'Current categories in database: {existing_count}')
        
        if existing_count == 0:
            # Create sample categories
            categories_data = [
                {
                    'name': 'Electronics',
                    'description': 'Electronic devices, gadgets, and accessories',
                    'is_active': True
                },
                {
                    'name': 'Clothing',
                    'description': 'Apparel and fashion items',
                    'is_active': True
                },
                {
                    'name': 'Books',
                    'description': 'Books, magazines, and educational materials',
                    'is_active': True
                },
                {
                    'name': 'Home & Garden',
                    'description': 'Home improvement and gardening supplies',
                    'is_active': False
                },
                {
                    'name': 'Sports',
                    'description': 'Sports equipment and accessories',
                    'is_active': True
                }
            ]
            
            created_count = 0
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    name=cat_data['name'],
                    defaults=cat_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'✅ Created: {category.name}')
                else:
                    self.stdout.write(f'ℹ️  Exists: {category.name}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} categories!')
            )
        else:
            self.stdout.write('Categories already exist:')
            for category in Category.objects.all():
                status = "🟢 Active" if category.is_active else "🔴 Inactive"
                self.stdout.write(f'  - {category.name} ({status})')
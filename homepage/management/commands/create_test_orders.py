from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from homepage.models import Customer, Order, OrderItem, Product, Category, Division, District, Thana
import random


class Command(BaseCommand):
    help = 'Create test orders for different dates'

    def handle(self, *args, **options):
        # Create test customer if doesn't exist
        customer, created = Customer.objects.get_or_create(
            email='testcustomer@example.com',
            defaults={
                'username': 'Test Customer',
                'is_active': True
            }
        )
        if created:
            customer.set_password('testpass123')
            customer.save()
            self.stdout.write(f'Created test customer: {customer.email}')

        # Create test category and product if doesn't exist
        category, _ = Category.objects.get_or_create(
            name='Test Category',
            defaults={'description': 'Test category for demo orders'}
        )
        
        product, _ = Product.objects.get_or_create(
            name='Test Product',
            defaults={
                'price': 100.00,
                'category': category,
                'available': True,
                'stock': 100
            }
        )

        # Get location data
        division = Division.objects.first()
        district = District.objects.first() 
        thana = Thana.objects.first()

        if not all([division, district, thana]):
            self.stdout.write(self.style.ERROR('Location data not found. Run populate_locations command first.'))
            return

        # Create orders for different dates
        today = timezone.now().date()
        dates_to_create = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=2),
            today - timedelta(days=7),
            today - timedelta(days=30),
        ]

        payment_methods = ['bkash', 'rocket', 'upay', 'nagad']
        statuses = ['pending', 'confirmed', 'processing', 'delivered']

        orders_created = 0
        
        for date in dates_to_create:
            # Create 2-5 orders per date
            num_orders = random.randint(2, 5)
            
            for i in range(num_orders):
                # Create order with specific date
                order_datetime = timezone.make_aware(
                    datetime.combine(date, datetime.min.time().replace(
                        hour=random.randint(8, 20),
                        minute=random.randint(0, 59)
                    ))
                )
                
                order = Order.objects.create(
                    user=customer,
                    created_at=order_datetime,
                    division=division,
                    district=district,
                    thana=thana,
                    area='Test Area',
                    detailed_address='Test Address Details',
                    phone_number='01700000000',
                    payment_method=random.choice(payment_methods),
                    payment_phone='01700000000',
                    status=random.choice(statuses),
                    total_price=random.randint(50, 500)
                )
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 3),
                    price=product.price
                )
                
                orders_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {orders_created} test orders across different dates')
        )
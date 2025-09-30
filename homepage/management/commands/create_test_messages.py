from django.core.management.base import BaseCommand
from homepage.models import ContactMessage
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Create test contact messages'

    def handle(self, *args, **options):
        # Sample data
        test_messages = [
            {
                'name': 'John Smith',
                'email': 'john.smith@email.com',
                'message': 'Hi, I am interested in your products. Could you please provide more information about shipping to Chittagong?'
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.j@gmail.com',
                'message': 'I placed an order last week but haven\'t received any updates. Could you please check the status? My order number is #12345.'
            },
            {
                'name': 'Ahmed Rahman',
                'email': 'ahmed.rahman@yahoo.com',
                'message': 'Your website is great! I have a suggestion for adding more payment methods like Nagad and Rocket.'
            },
            {
                'name': 'Lisa Chen',
                'email': 'lisa.chen@hotmail.com',
                'message': 'The product I received was damaged during shipping. I would like to return it and get a replacement. Please let me know the process.'
            },
            {
                'name': 'Mohammad Ali',
                'email': 'm.ali@email.com',
                'message': 'Hello, I am a retailer and interested in bulk orders. Do you offer wholesale prices? Please contact me for business partnership.'
            },
            {
                'name': 'Emma Wilson',
                'email': 'emma.wilson@gmail.com',
                'message': 'I love shopping on your site! The delivery was fast and products are good quality. Keep up the great work!'
            },
            {
                'name': 'Rashid Hassan',
                'email': 'rashid.hassan@outlook.com',
                'message': 'I am having trouble with checkout. The page keeps loading but doesn\'t complete the order. Please help!'
            },
            {
                'name': 'Maria Garcia',
                'email': 'maria.garcia@email.com',
                'message': 'Do you ship internationally? I am currently in Dubai and would like to order some products for my family in Bangladesh.'
            }
        ]

        # Create messages with different timestamps
        for i, msg_data in enumerate(test_messages):
            # Create messages from different times (last 2 weeks)
            created_time = timezone.now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            
            message = ContactMessage.objects.create(
                name=msg_data['name'],
                email=msg_data['email'],
                message=msg_data['message'],
                created_at=created_time,
                is_read=random.choice([True, False])
            )
            
            # Add replies to some messages
            if random.choice([True, False]) and message.is_read:
                message.admin_reply = f"Dear {message.name},\n\nThank you for contacting Yotta Plus Shop. We have received your message and will address your concern promptly.\n\nBest regards,\nCustomer Service Team"
                message.replied_at = created_time + timedelta(hours=random.randint(1, 48))
                message.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(test_messages)} test contact messages'
            )
        )
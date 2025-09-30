from django.core.management.base import BaseCommand
from adminpanel.models import AdminUser

class Command(BaseCommand):
    help = 'Create admin user with provided credentials'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Admin email address')
        parser.add_argument('username', type=str, help='Admin username') 
        parser.add_argument('password', type=str, help='Admin password')

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        password = options['password']

        try:
            # Check if admin already exists
            if AdminUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Admin user with email {email} already exists.')
                )
                return

            # Create the admin user
            admin_user = AdminUser.objects.create_superuser(
                email=email,
                username=username,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Admin user created successfully!\n'
                    f'   Email: {admin_user.email}\n'
                    f'   Username: {admin_user.username}\n'
                    f'   ID: {admin_user.id}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin user: {e}')
            )
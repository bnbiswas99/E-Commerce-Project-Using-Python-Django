from django.core.management.base import BaseCommand
from adminpanel.models import AdminUser
from django.core.exceptions import ValidationError
import getpass

class Command(BaseCommand):
    help = 'Create a new admin user'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Admin email address')
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--password', type=str, help='Admin password')

    def handle(self, *args, **options):
        email = options.get('email')
        username = options.get('username')
        password = options.get('password')

        # Interactive mode if no arguments provided
        if not email:
            email = input('Email: ')
        
        if not username:
            username = input('Username: ')
        
        if not password:
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match.')
                )
                return

        try:
            # Check if admin already exists
            if AdminUser.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.ERROR(f'Admin user with email {email} already exists.')
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
                    f'Admin user "{admin_user.username}" ({admin_user.email}) created successfully!'
                )
            )

        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
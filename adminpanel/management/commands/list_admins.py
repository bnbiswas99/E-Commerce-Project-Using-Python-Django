from django.core.management.base import BaseCommand
from adminpanel.models import AdminUser

class Command(BaseCommand):
    help = 'List all admin users'

    def handle(self, *args, **options):
        admins = AdminUser.objects.all().order_by('id')
        
        if not admins.exists():
            self.stdout.write(
                self.style.WARNING('No admin users found.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('📋 Admin Users List:\n' + '='*50)
        )
        
        for admin in admins:
            status = "🟢 Active" if admin.is_active else "🔴 Inactive"
            superuser = "👑 Superuser" if admin.is_superuser else "👤 Regular"
            
            self.stdout.write(
                f'ID: {admin.id:2d} | {admin.email:25s} | {admin.username:15s} | {status} | {superuser}'
            )
            
        self.stdout.write('='*50)
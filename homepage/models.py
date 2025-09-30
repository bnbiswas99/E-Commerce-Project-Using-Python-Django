# homepage/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.utils import timezone


# ------------------------------
# Category model
# ------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="category_images/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_products_count(self):
        return self.products.filter(available=True).count()
    
    def get_image_url(self):
        """
        Returns the proper image URL whether it's a stored URL string or an uploaded file.
        """
        if self.image:
            # Check if the image field contains a URL string (starts with http)
            image_str = str(self.image)
            if image_str.startswith('http'):
                return image_str
            else:
                # It's an uploaded file, use the standard URL
                try:
                    return self.image.url
                except:
                    return None
        return None


# ------------------------------
# Product model
# ------------------------------
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name
    
    def get_image_url(self):
        """
        Returns the proper image URL whether it's a stored URL string or an uploaded file.
        """
        if self.image:
            # Check if the image field contains a URL string (starts with http)
            image_str = str(self.image)
            if image_str.startswith('http'):
                return image_str
            else:
                # It's an uploaded file, use the standard URL
                try:
                    return self.image.url
                except Exception as e:
                    print(f"Error getting image URL for {self.name}: {e}")
                    return None
        return None


# ------------------------------
# Customer model
# ------------------------------
class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Customers must have an email address")
        email = self.normalize_email(email)
        customer = self.model(email=email, **extra_fields)
        customer.set_password(password)
        customer.save(using=self._db)
        return customer

    def create_superuser(self, email, password=None, **extra_fields):
        raise ValueError("Use Django's admin User model for admin accounts.")


class Customer(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Avoid group/permission conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customer_set',
        blank=True,
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customer_permissions_set',
        blank=True,
        verbose_name='user permissions'
    )

    objects = CustomerManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
           
# ------------------------------
# Cart
# ------------------------------
class Cart(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"
    
# ------------------------------
# Address and Payment Models
# ------------------------------
class Division(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class District(models.Model):
    name = models.CharField(max_length=100)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='districts')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Thana(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='thanas')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Area(models.Model):
    name = models.CharField(max_length=100)
    thana = models.ForeignKey(Thana, on_delete=models.CASCADE, related_name='areas')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


# ------------------------------
# Orders
# ------------------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('bkash', 'bKash'),
        ('rocket', 'Rocket'),
        ('upay', 'Upay'),
        ('nagad', 'Nagad'),
    ]
    
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # Captures exact timestamp when order is created
    updated_at = models.DateTimeField(auto_now=True)      # Updates when order status changes
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Address Information
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    thana = models.ForeignKey(Thana, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    detailed_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Payment Information
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, blank=True, null=True)
    payment_phone = models.CharField(max_length=15, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    def get_full_address(self):
        address_parts = []
        if self.detailed_address:
            address_parts.append(self.detailed_address)
        if self.area:
            address_parts.append(self.area)
        if self.thana:
            address_parts.append(self.thana.name)
        if self.district:
            address_parts.append(self.district.name)
        if self.division:
            address_parts.append(self.division.name)
        return ', '.join(address_parts)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.product.name} (Order #{self.order.id})"


# ------------------------------
# Contact Message model
# ------------------------------
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    admin_reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} - {self.email}"

    def mark_as_read(self):
        self.is_read = True
        self.save()


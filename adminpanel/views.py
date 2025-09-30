from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import AdminUser
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect, get_object_or_404
from homepage.models import Product, Category
from .forms import ProductForm, CategoryForm
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from homepage.models import Customer, Order, OrderItem
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from homepage.models import OrderItem
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator

def admin_login(request):
    if request.user.is_authenticated and request.session.get('admin_user_id'):
        return redirect("admin_dashboard")   # Already logged in → skip login

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Use custom backend explicitly
        user = authenticate(
            request,
            email=email,
            password=password,
            backend='adminpanel.backends.AdminBackend'
        )

        if user is not None and isinstance(user, AdminUser):
            login(request, user, backend='adminpanel.backends.AdminBackend')
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid admin credentials")

    return render(request, "adminpanel/loginAdmin.html")


def is_admin(user):
    return isinstance(user, AdminUser)


def admin_dashboard(request):
    return render(request, "adminpanel/dashboard.html")

def admin_logout(request):
    logout(request)
    return redirect("admin_login")   # Always send back to admin login

# ✅ Only allow superusers/staff
def admin_required(view_func):
    return user_passes_test(
        lambda u: isinstance(u, AdminUser) and u.is_superuser,
        login_url=reverse_lazy('admin_login')
    )(view_func)


@admin_required
def manage_products(request):
    products = Product.objects.all()
    return render(request, 'adminpanel/manage_products.html', {'products': products})

@admin_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Welcome! Login successful.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    return render(request, 'adminpanel/product_form.html', {'form': form, 'title': 'Add Product'})

@admin_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('manage_products')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'adminpanel/product_form.html', {'form': form, 'title': 'Edit Product'})

@admin_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, f"Product '{product.name}' has been deleted successfully!")
        return redirect('manage_products')
    return render(request, 'adminpanel/confirm_delete.html', {'product': product})

# ================================
# Category Management Views
# ================================

@admin_required
def manage_categories(request):
    categories = Category.objects.all().order_by('name')
    active_categories_count = categories.filter(is_active=True).count()
    total_products = Product.objects.count()
    
    context = {
        'categories': categories,
        'active_categories_count': active_categories_count,
        'total_products': total_products,
    }
    return render(request, 'adminpanel/manage_categories.html', context)

@admin_required
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' has been created successfully!")
            return redirect('manage_categories')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm()
    return render(request, 'adminpanel/category_form.html', {'form': form, 'title': 'Add Category'})

@admin_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' has been updated successfully!")
            return redirect('manage_categories')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CategoryForm(instance=category)
    return render(request, 'adminpanel/category_form.html', {'form': form, 'title': 'Edit Category'})

@admin_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category_name = category.name
        products_count = category.get_products_count()
        
        if products_count > 0:
            messages.error(request, f"Cannot delete category '{category_name}' because it has {products_count} products. Please move or delete the products first.")
            return redirect('manage_categories')
        
        category.delete()
        messages.success(request, f"Category '{category_name}' has been deleted successfully!")
        return redirect('manage_categories')
    
    return render(request, 'adminpanel/confirm_delete_category.html', {
        'category': category,
        'products_count': category.get_products_count()
    })

@admin_required
def category_products(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products = category.products.all().order_by('name')
    return render(request, 'adminpanel/category_products.html', {
        'category': category,
        'products': products
    })

@admin_required
def bulk_delete_categories(request):
    if request.method == 'POST':
        category_ids = request.POST.getlist('category_ids')
        
        if not category_ids:
            messages.error(request, "No categories selected for deletion.")
            return redirect('manage_categories')
        
        # Get categories to delete
        categories_to_delete = Category.objects.filter(id__in=category_ids)
        total_selected = len(category_ids)
        
        if not categories_to_delete.exists():
            messages.error(request, "Selected categories not found.")
            return redirect('manage_categories')
        
        # Check for categories with products
        categories_with_products = []
        categories_without_products = []
        
        for category in categories_to_delete:
            products_count = category.get_products_count()
            if products_count > 0:
                categories_with_products.append((category, products_count))
            else:
                categories_without_products.append(category)
        
        # Delete categories without products
        deleted_count = 0
        deleted_names = []
        
        for category in categories_without_products:
            deleted_names.append(category.name)
            category.delete()
            deleted_count += 1
        
        # Prepare messages
        if deleted_count > 0:
            if deleted_count == 1:
                messages.success(request, f"Category '{deleted_names[0]}' has been deleted successfully!")
            else:
                messages.success(request, f"{deleted_count} categories have been deleted successfully: {', '.join(deleted_names)}")
        
        if categories_with_products:
            skipped_info = []
            for category, products_count in categories_with_products:
                skipped_info.append(f"'{category.name}' ({products_count} products)")
            
            if len(categories_with_products) == 1:
                messages.warning(request, f"Cannot delete category {skipped_info[0]}. Please move or delete the products first.")
            else:
                messages.warning(request, f"Cannot delete {len(categories_with_products)} categories with products: {', '.join(skipped_info)}. Please move or delete the products first.")
    
    return redirect('manage_categories')

@admin_required
def toggle_category_status(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        new_status = request.POST.get('is_active') == 'true'
        
        category.is_active = new_status
        category.save()
        
        status_text = "activated" if new_status else "deactivated"
        messages.success(request, f"Category '{category.name}' has been {status_text} successfully!")
    
    return redirect('manage_categories')

@admin_required
def manage_customers(request):
    query = request.GET.get("q", "")
    customers = Customer.objects.all()

    if query:
        customers = customers.filter(username__icontains=query) | customers.filter(email__icontains=query)

    return render(
        request,
        "adminpanel/manage_customers.html",
        {"customers": customers, "query": query},
    )

@admin_required
def manage_customers(request):
    query = request.GET.get("q", "")
    customers = Customer.objects.all()

    if query:
        customers = customers.filter(username__icontains=query) | customers.filter(email__icontains=query)

    return render(
        request,
        "adminpanel/manage_customers.html",
        {"customers": customers, "query": query},
    )


@admin_required
def customer_orders(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(user=customer).order_by("-created_at")
    return render(
        request,
        "adminpanel/customer_orders.html",
        {"customer": customer, "orders": orders},
    )

@admin_required
def sales_overview(request):
    from datetime import datetime, timedelta
    from django.db.models import Count
    import json
    
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday())   # Monday
    start_month = today.replace(day=1)
    
    # Revenue Statistics
    daily_revenue = OrderItem.objects.filter(
        order__created_at__date=today
    ).aggregate(total=Sum(F("quantity") * F("price")))['total'] or 0
    
    weekly_revenue = OrderItem.objects.filter(
        order__created_at__date__gte=start_week
    ).aggregate(total=Sum(F("quantity") * F("price")))['total'] or 0
    
    monthly_revenue = OrderItem.objects.filter(
        order__created_at__date__gte=start_month
    ).aggregate(total=Sum(F("quantity") * F("price")))['total'] or 0
    
    # Order Statistics
    daily_orders = Order.objects.filter(created_at__date=today).count()
    weekly_orders = Order.objects.filter(created_at__date__gte=start_week).count()
    monthly_orders = Order.objects.filter(created_at__date__gte=start_month).count()
    
    # Last 7 days revenue data for line chart
    last_7_days = []
    last_7_days_revenue = []
    last_7_days_orders = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_revenue = OrderItem.objects.filter(
            order__created_at__date=date
        ).aggregate(total=Sum(F("quantity") * F("price")))['total'] or 0
        
        day_orders = Order.objects.filter(created_at__date=date).count()
        
        last_7_days.append(date.strftime('%m/%d'))
        last_7_days_revenue.append(float(day_revenue))
        last_7_days_orders.append(day_orders)
    
    # Last 12 months revenue data for monthly chart
    monthly_revenue_data = []
    monthly_labels = []
    monthly_order_data = []
    
    for i in range(11, -1, -1):
        if today.month - i <= 0:
            month = today.month - i + 12
            year = today.year - 1
        else:
            month = today.month - i
            year = today.year
            
        month_start = datetime(year, month, 1).date()
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        month_revenue = OrderItem.objects.filter(
            order__created_at__date__gte=month_start,
            order__created_at__date__lte=month_end
        ).aggregate(total=Sum(F("quantity") * F("price")))['total'] or 0
        
        month_orders = Order.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        
        monthly_labels.append(datetime(year, month, 1).strftime('%b %Y'))
        monthly_revenue_data.append(float(month_revenue))
        monthly_order_data.append(month_orders)
    
    # Top selling products (last 30 days)
    top_products = OrderItem.objects.filter(
        order__created_at__date__gte=today - timedelta(days=30)
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_sold')[:10]
    
    # Order status distribution
    status_data = Order.objects.filter(
        created_at__date__gte=start_month
    ).values('status').annotate(count=Count('id')).order_by('status')
    
    # Calculate additional metrics
    avg_daily_revenue = weekly_revenue / 7 if weekly_revenue > 0 else 0
    avg_order_value = monthly_revenue / monthly_orders if monthly_orders > 0 else 0

    # Convert data to JSON for JavaScript
    context = {
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'daily_orders': daily_orders,
        'weekly_orders': weekly_orders,
        'monthly_orders': monthly_orders,
        'last_7_days_labels': json.dumps(last_7_days),
        'last_7_days_revenue': json.dumps(last_7_days_revenue),
        'last_7_days_orders': json.dumps(last_7_days_orders),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_revenue_data': json.dumps(monthly_revenue_data),
        'monthly_order_data': json.dumps(monthly_order_data),
        'top_products': list(top_products),
        'status_data': list(status_data),
        'avg_daily_revenue': avg_daily_revenue,
        'avg_order_value': avg_order_value,
    }
    
    return render(request, "adminpanel/sales_analytics.html", context)


# ================================
# Order Management Views
# ================================

@admin_required
def manage_orders(request):
    """Comprehensive order management with filtering options"""
    # Get filter parameters
    filter_type = request.GET.get('filter', 'all')  # all, today, week, month
    status_filter = request.GET.get('status', 'all')  # all, pending, confirmed, etc.
    search_query = request.GET.get('search', '')
    
    # Base queryset
    orders = Order.objects.all().select_related('user').prefetch_related('items__product')
    
    # Apply time filters
    today = timezone.now().date()
    if filter_type == 'today':
        orders = orders.filter(created_at__date=today)
    elif filter_type == 'week':
        start_week = today - timedelta(days=today.weekday())
        orders = orders.filter(created_at__date__gte=start_week)
    elif filter_type == 'month':
        start_month = today.replace(day=1)
        orders = orders.filter(created_at__date__gte=start_month)
    
    # Apply status filter
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Apply search filter
    if search_query:
        orders = orders.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Order by newest first
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 25)  # 25 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_orders = orders.count()
    total_amount = sum(order.total_price for order in orders)
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_orders': total_orders,
        'total_amount': total_amount,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'adminpanel/manage_orders.html', context)


@admin_required
def order_detail(request, order_id):
    """Detailed view of a specific order with comprehensive information"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all().select_related('product__category')
    
    # Determine if this is accessed from management page or reports
    # Check both URL parameter and HTTP_REFERER for source detection
    source = request.GET.get('source', '')
    referer = request.META.get('HTTP_REFERER', '')
    show_actions = False
    view_source = 'management'  # default
    
    # First check URL parameter (most reliable)
    if source == 'daily' or source == 'monthly':
        show_actions = False
        view_source = 'reports'
    elif source == 'management':
        show_actions = True
        view_source = 'management'
    else:
        # Fallback to referer check
        if 'daily-orders' in referer or 'monthly-orders' in referer:
            show_actions = False
            view_source = 'reports'
        elif 'manage-orders' in referer:
            show_actions = True
            view_source = 'management'
        else:
            # Default for direct access - allow actions
            show_actions = True
            view_source = 'management'
    
    # Get customer statistics
    customer = order.user
    customer_orders = Order.objects.filter(user=customer)
    customer_stats = {
        'total_orders': customer_orders.count(),
        'total_spent': sum(float(o.total_price) for o in customer_orders),
        'pending_orders': customer_orders.filter(status='pending').count(),
        'completed_orders': customer_orders.filter(status='delivered').count(),
    }
    
    # Get product details for each item
    enhanced_items = []
    for item in order_items:
        product = item.product
        enhanced_items.append({
            'item': item,
            'product': product,
            'category': product.category,
            'stock_status': 'In Stock' if product.stock > 0 else 'Out of Stock',
            'availability': 'Available' if product.available else 'Unavailable',
            'subtotal': item.price * item.quantity
        })
    
    context = {
        'order': order,
        'order_items': order_items,
        'enhanced_items': enhanced_items,
        'customer_stats': customer_stats,
        'show_actions': show_actions,  # Flag to control action buttons
        'view_source': view_source  # Source of the request (reports/management)
    }
    
    return render(request, 'adminpanel/order_detail.html', context)


@admin_required
def confirm_order(request, order_id):
    """Confirm an order and update its status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Update order status
        new_status = request.POST.get('status', 'confirmed')
        order.status = new_status
        order.save()
        
        # Add success message
        messages.success(request, f'Order #{order.id} has been {new_status}!')
        
        # Return JSON response for AJAX calls
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Order #{order.id} has been {new_status}!',
                'new_status': order.get_status_display()
            })
        
        return redirect('order_detail', order_id=order.id)
    
    return redirect('manage_orders')


@admin_required
def bulk_confirm_orders(request):
    """Confirm multiple orders at once"""
    if request.method == 'POST':
        order_ids = request.POST.getlist('order_ids')
        new_status = request.POST.get('bulk_status', 'confirmed')
        
        if order_ids:
            updated_count = Order.objects.filter(id__in=order_ids).update(status=new_status)
            messages.success(request, f'{updated_count} orders have been {new_status}!')
        else:
            messages.error(request, 'No orders selected.')
    
    return redirect('manage_orders')


@admin_required
def daily_orders(request):
    """Daily orders view with date selection"""
    from datetime import datetime, date
    from django.core.paginator import Paginator
    
    # Get selected date from query params or use today
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Filter orders by selected date
    orders = Order.objects.filter(
        created_at__date=selected_date
    ).select_related('user').prefetch_related('items__product').order_by('-created_at')
    
    # Calculate statistics for selected date
    total_orders = orders.count()
    total_revenue = sum(float(order.total_price) for order in orders) if orders else 0
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    delivered_orders = orders.filter(status='delivered').count()
    
    # Pagination
    paginator = Paginator(orders, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'selected_date': selected_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'view_type': 'daily'
    }
    
    return render(request, 'adminpanel/daily_orders.html', context)


@admin_required
def monthly_orders(request):
    """Monthly orders view with month/year selection"""
    from datetime import datetime, date
    from calendar import monthrange
    from collections import defaultdict
    from django.core.paginator import Paginator
    
    # Get current date
    today = timezone.now().date()
    
    # Get selected month and year from query params
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    
    # Create start and end dates for the selected month
    start_date = date(selected_year, selected_month, 1)
    _, last_day = monthrange(selected_year, selected_month)
    end_date = date(selected_year, selected_month, last_day)
    
    # Filter orders by selected month and year
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('user').prefetch_related('items__product').order_by('-created_at')
    
    # Calculate statistics for selected month
    total_orders = orders.count()
    total_revenue = sum(float(order.total_price) for order in orders) if orders else 0
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    delivered_orders = orders.filter(status='delivered').count()
    
    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Group by day for daily breakdown chart
    daily_breakdown = []
    for day in range(1, last_day + 1):
        current_date = date(selected_year, selected_month, day)
        day_orders = orders.filter(created_at__date=current_date)
        day_count = day_orders.count()
        day_revenue = sum(float(order.total_price) for order in day_orders) if day_orders else 0
        
        daily_breakdown.append({
            'day': day,
            'orders': day_count,
            'revenue': day_revenue
        })
    
    # Pagination
    paginator = Paginator(orders, 25)  # Show 25 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare month and year choices for the form
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    # Generate year choices (current year ± 2 years)
    years = list(range(today.year - 2, today.year + 3))
    
    # Get selected month name
    month_name = dict(months)[selected_month]
    
    context = {
        'orders': page_obj,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_name': month_name,
        'months': months,
        'years': years,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'avg_order_value': avg_order_value,
        'daily_breakdown': daily_breakdown,
        'view_type': 'monthly'
    }
    
    return render(request, 'adminpanel/monthly_orders.html', context)


# ================================
# Contact Messages Views
# ================================

@admin_required
def contact_messages(request):
    """View all contact messages from users"""
    from homepage.models import ContactMessage
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    messages_queryset = ContactMessage.objects.all()
    
    # Apply filters
    if status_filter == 'unread':
        messages_queryset = messages_queryset.filter(is_read=False)
    elif status_filter == 'read':
        messages_queryset = messages_queryset.filter(is_read=True)
    elif status_filter == 'replied':
        messages_queryset = messages_queryset.filter(admin_reply__isnull=False)
    
    # Apply search
    if search_query:
        messages_queryset = messages_queryset.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(messages_queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_messages = ContactMessage.objects.count()
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    read_messages = ContactMessage.objects.filter(is_read=True).count()
    
    context = {
        'messages': page_obj,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        'read_messages': read_messages,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'adminpanel/contact_messages.html', context)


@admin_required
def contact_message_detail(request, message_id):
    """View and reply to a specific contact message"""
    from homepage.models import ContactMessage
    from django.utils import timezone
    
    message = get_object_or_404(ContactMessage, id=message_id)
    
    # Mark as read when viewing
    if not message.is_read:
        message.mark_as_read()
    
    if request.method == 'POST':
        admin_reply = request.POST.get('admin_reply')
        if admin_reply:
            message.admin_reply = admin_reply
            message.replied_at = timezone.now()
            message.save()
            
            messages.success(request, 'Reply saved successfully!')
            return redirect('contact_message_detail', message_id=message.id)
    
    context = {
        'message': message,
    }
    
    return render(request, 'adminpanel/contact_message_detail.html', context)


@admin_required
def mark_message_read(request, message_id):
    """Mark a message as read/unread"""
    from homepage.models import ContactMessage
    
    if request.method == 'POST':
        message = get_object_or_404(ContactMessage, id=message_id)
        action = request.POST.get('action')
        
        if action == 'mark_read':
            message.is_read = True
        elif action == 'mark_unread':
            message.is_read = False
        
        message.save()
        
        return JsonResponse({'success': True, 'is_read': message.is_read})
    
    return JsonResponse({'success': False})


@admin_required
def delete_contact_message(request, message_id):
    """Delete a contact message"""
    from homepage.models import ContactMessage
    
    if request.method == 'POST':
        message = get_object_or_404(ContactMessage, id=message_id)
        message.delete()
        messages.success(request, 'Message deleted successfully!')
        return redirect('contact_messages')
    
    return redirect('contact_messages')

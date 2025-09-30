# adminpanel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name="admin_login"),
    path('dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('logout/', views.admin_logout, name="admin_logout"),
    
    # Categories
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('categories/<int:pk>/products/', views.category_products, name='category_products'),
    path('categories/bulk-delete/', views.bulk_delete_categories, name='bulk_delete_categories'),
    path('categories/<int:pk>/toggle-status/', views.toggle_category_status, name='toggle_category_status'),
    
    # Products
    path('products/', views.manage_products, name='manage_products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    
    # Customers
    path('customers/', views.manage_customers, name='manage_customers'),
    path('customers/<int:customer_id>/orders/', views.customer_orders, name='customer_orders'),
    path('sales-overview/', views.sales_overview, name='sales_overview'),
    
    # Order Management
    path('orders/', views.manage_orders, name='manage_orders'),
    path('orders/<int:order_id>/', views.order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/confirm/', views.confirm_order, name='confirm_order'),
    path('orders/bulk-confirm/', views.bulk_confirm_orders, name='bulk_confirm_orders'),
    path('orders/daily/', views.daily_orders, name='daily_orders'),
    path('orders/monthly/', views.monthly_orders, name='monthly_orders'),
    
    # Contact Messages
    path('messages/', views.contact_messages, name='contact_messages'),
    path('messages/<int:message_id>/', views.contact_message_detail, name='contact_message_detail'),
    path('messages/<int:message_id>/mark-read/', views.mark_message_read, name='mark_message_read'),
    path('messages/<int:message_id>/delete/', views.delete_contact_message, name='delete_contact_message'),
    
]

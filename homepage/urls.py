# homepage/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('products/', views.product_list, name='product_list'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('site-logout/', views.site_logout, name='site_logout'),

    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('profile/', views.profile, name='profile'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('decrease-quantity/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('checkout/', views.checkout, name='checkout'),

    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    
    # AJAX URLs for cascading dropdowns
    path('ajax/load-districts/', views.load_districts, name='ajax_load_districts'),
    path('ajax/load-thanas/', views.load_thanas, name='ajax_load_thanas'),
]

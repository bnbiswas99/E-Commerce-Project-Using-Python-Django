# homepage/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Customer, Product, Cart, CartItem, Order, OrderItem, Category, Division, District, Thana, Area, ContactMessage
from .forms import CustomerRegisterForm, CustomerLoginForm
from django.shortcuts import render


def about(request):
    return render(request, "homepage/about.html")

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if name and email and message:
            # Create contact message
            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message
            )
            # Add success message
            from django.contrib import messages
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
        else:
            from django.contrib import messages
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, "homepage/contact.html")


# -----------------------
# Homepage view
# -----------------------
def homepage(request):
    # Get active categories from database
    categories = Category.objects.filter(is_active=True).order_by('name')
    featured_products = Product.objects.filter(available=True, stock__gt=0)[:8]

    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())

    return render(
        request,
        'homepage/home.html',
        {
            'categories': categories,
            'featured_products': featured_products,
            'cart_count': cart_count,
        }
    )


# -----------------------
# Product list / search
# -----------------------
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    # Get all available products
    products = Product.objects.filter(available=True)

    # Filter by category if specified
    if category_id and category_id != 'all':
        try:
            category_obj = Category.objects.get(id=category_id, is_active=True)
            products = products.filter(category=category_obj)
        except Category.DoesNotExist:
            pass

    # Filter by search query
    if query:
        products = products.filter(name__icontains=query)

    # Get active categories for the filter dropdown
    categories = Category.objects.filter(is_active=True).order_by('name')

    return render(request, 'homepage/products.html', {
        'products': products,
        'query': query,
        'selected_category': category_id,
        'categories': categories,
    })


# -----------------------
# Cart functions
# -----------------------
def add_to_cart(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        if not product.available:
            messages.error(request, "This product is not available.")
            return redirect('product_list')

        if request.user.is_authenticated and isinstance(request.user, Customer):
            cart, created = Cart.objects.get_or_create(user=request.user)
            item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            item.quantity += 1
            item.save()
        else:
            cart = request.session.get('cart', {})
            cart[str(product_id)] = cart.get(str(product_id), 0) + 1
            request.session['cart'] = cart

        messages.success(request, f"'{product.name}' has been added to your cart!")

    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
    return redirect('product_list')


def remove_from_cart(request, product_id):
    if request.user.is_authenticated and isinstance(request.user, Customer):
        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.get(cart=cart, product_id=product_id).delete()
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            pass
    else:
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
    return redirect('view_cart')


def decrease_quantity(request, product_id):
    if request.user.is_authenticated and isinstance(request.user, Customer):
        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            pass
    else:
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            if cart[str(product_id)] > 1:
                cart[str(product_id)] -= 1
            else:
                del cart[str(product_id)]
            request.session['cart'] = cart
    return redirect('view_cart')


def view_cart(request):
    items = []
    total = 0

    if request.user.is_authenticated and isinstance(request.user, Customer):
        cart, created = Cart.objects.get_or_create(user=request.user)
        for item in cart.items.select_related('product'):
            subtotal = item.product.price * item.quantity
            items.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal
            })
            total += subtotal
    else:
        cart = request.session.get('cart', {})
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                subtotal = product.price * quantity
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                total += subtotal
            except Product.DoesNotExist:
                continue

    return render(request, 'homepage/cart.html', {'items': items, 'total': total})


# -----------------------
# Context processor for cart count
# -----------------------
def cart_count(request):
    if request.user.is_authenticated and isinstance(request.user, Customer):
        cart, created = Cart.objects.get_or_create(user=request.user)
        return {'cart_count': sum(item.quantity for item in cart.items.all())}
    else:
        cart = request.session.get('cart', {})
        return {'cart_count': sum(cart.values())}


# -----------------------
# Customer registration
# -----------------------
def register_view(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! You can now log in.")
            return redirect('login')
    else:
        form = CustomerRegisterForm()
    return render(request, 'homepage/register.html', {'form': form})


# -----------------------
# Customer login
# -----------------------
def login_view(request):
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            customer = authenticate(request, email=email, password=password)
            if customer is not None and isinstance(customer, Customer):
                login(request, customer)

                # Sync session cart into DB cart
                session_cart = request.session.get('cart', {})
                cart, created = Cart.objects.get_or_create(user=customer)
                for product_id, qty in session_cart.items():
                    product = Product.objects.get(id=product_id)
                    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                    item.quantity += qty
                    item.save()
                request.session['cart'] = {}

                return redirect('homepage')
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = CustomerLoginForm()
    return render(request, 'homepage/login.html', {'form': form})


# -----------------------
# Customer logout
# -----------------------
def site_logout(request):
    logout(request)
    return redirect('homepage')


# -----------------------
# Customer profile
# -----------------------
@login_required
def profile(request):
    return render(request, 'homepage/profile.html')


# -----------------------
# Checkout
# -----------------------
@login_required
def checkout(request):
    if not isinstance(request.user, Customer):
        messages.error(request, "Only customers can checkout.")
        return redirect('homepage')

    cart, created = Cart.objects.get_or_create(user=request.user)

    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    if request.method == 'POST':
        from .forms import CheckoutForm
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Create the order with all the details
            order = Order.objects.create(
                user=request.user,
                division=form.cleaned_data['division'],
                district=form.cleaned_data['district'],
                thana=form.cleaned_data['thana'],
                area=form.cleaned_data['area'],
                detailed_address=form.cleaned_data['detailed_address'],
                phone_number=form.cleaned_data['phone_number'],
                payment_method=form.cleaned_data['payment_method'],
                payment_phone=form.cleaned_data['payment_phone'],
                total_price=0
            )

            total = 0
            for item in cart.items.select_related('product'):
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    if product.stock == 0:
                        product.available = False
                    product.save()

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=product.price,
                        quantity=item.quantity
                    )
                    total += product.price * item.quantity
                else:
                    messages.error(request, f"Not enough stock for {product.name}")
                    order.delete()  # Delete the incomplete order
                    form = CheckoutForm()  # Reset form
                    return render(request, 'homepage/checkout.html', {
                        'form': form,
                        'cart': cart,
                        'cart_total': cart.total()
                    })

            order.total_price = total
            order.save()

            # Clear the cart
            cart.items.all().delete()

            messages.success(request, f"🎉 Order #{order.id} placed successfully! You will receive a confirmation call shortly.")
            return redirect('order_confirmation', order_id=order.id)
    else:
        from .forms import CheckoutForm
        form = CheckoutForm()

    return render(request, 'homepage/checkout.html', {
        'form': form,
        'cart': cart,
        'cart_total': cart.total()
    })


@login_required
def order_confirmation(request, order_id):
    """Display order confirmation page"""
    if not isinstance(request.user, Customer):
        messages.error(request, "Access denied.")
        return redirect('homepage')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return render(request, 'homepage/order_confirmation.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('homepage')


# -----------------------
# Purchase history
# -----------------------
@login_required
def order_history(request):
    if not isinstance(request.user, Customer):
        messages.error(request, "Only customers can view orders.")
        return redirect('homepage')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'homepage/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    if not isinstance(request.user, Customer):
        messages.error(request, "Only customers can view order details.")
        return redirect('homepage')

    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'homepage/order_detail.html', {'order': order})


# -----------------------
# AJAX Views for Cascading Dropdowns
# -----------------------
def load_districts(request):
    """AJAX view to load districts based on selected division"""
    division_id = request.GET.get('division_id')
    districts = District.objects.filter(division_id=division_id).order_by('name')
    return JsonResponse(list(districts.values('id', 'name')), safe=False)


def load_thanas(request):
    """AJAX view to load thanas based on selected district"""
    district_id = request.GET.get('district_id')
    thanas = Thana.objects.filter(district_id=district_id).order_by('name')
    return JsonResponse(list(thanas.values('id', 'name')), safe=False)




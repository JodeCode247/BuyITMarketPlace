from django.shortcuts import render,redirect,get_object_or_404
from .models import Product,MyUsers,Cart,CartItems,Category,Order,PackageForm
import json
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.contrib.auth import login,logout
from django.core.exceptions import FieldError
from django.utils import timezone
from django.db.models import Q
from .handler import upload_to_drive, merge_carts
from django.conf import settings
from . import paystack
from django.db import transaction
from .smart import ai_search , get_embedding ,manual_search_fallback
from pgvector.django import CosineDistance


def test_func(user):
        return user.is_authenticated # example.


@csrf_protect # Enable CSRF protection
def get_cart_count(request):
    cart = get_cart(request)
    if cart:
        count = cart.items_count
    return JsonResponse({'count': count})

from django.db.models import Q
from django.shortcuts import render
from pgvector.django import CosineDistance 

def index(request):
    query = request.GET.get('query', '').strip()
    products = Product.objects.all()
    parsed_data = None
    
    if query:
        word_count = len(query.split())
        has_numbers = any(char.isdigit() for char in query)

        # 1. LIGHTWEIGHT SEARCH: For simple queries like "Shoes" or "Apple"
        if word_count <= 2 and not has_numbers:
            products = products.filter(
                Q(name__icontains=query) | 
                Q(category__name__icontains=query)
            )
        
        # 2. AI & SEMANTIC SEARCH: For complex queries like "Nike under 50k"
        else:
            parsed_data = ai_search(query)
            
            if parsed_data:
                search_term = parsed_data.get('search_term', query)
                max_price = parsed_data.get('max_price')
                brand = parsed_data.get('brand')

                # Apply hard filters first (Price and Brand)
                if max_price:
                    products = products.filter(price__lte=max_price)
                if brand:
                    products = products.filter(name__icontains=brand)
                
            else:
                fall_search =manual_search_fallback(query)
                max_price = fall_search.get('max_price')
                search_term = fall_search.get('search_term')
                print(search_term)
                if search_term:
                    products = products.filter(
            Q(name__icontains=search_term) | 
            Q(category__name__icontains=search_term)
        )
                if max_price:
                    products = products.filter(price__lte=max_price)
    # Final limit for performance
    products = products[:24]

    context = {
        'products': products,
        'query': query,
        'parsed_data': parsed_data
    }

    if request.headers.get('HX-Request'):
        return render(request, 'onlineStore/partials/product_list.html', context)
    
    return render(request, 'onlineStore/index.html', context)

@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        try:      
            data = json.loads(request.body)
            product_id = int(data.get('product_id'))
            if product_id:
                product = Product.objects.get(pk=product_id)
                if product.number_available:
                    cart = get_cart(request)
                    print(cart.cart_id)

                    cart_item, created = CartItems.objects.get_or_create(cart=cart, product=product)

                    if not created:
                        if cart_item.quantity <= cart_item.product.number_available :
                            if cart_item.product.number_available == cart_item.quantity:
                                return JsonResponse({'status': 'error', 'message': 'product number exceeeded'}, status=400)
                            cart_item.quantity+=1
                            cart_item.save()
                            return JsonResponse({'status': 'success', 'message': 'Product added to cart'},status=200)
                        else:
                            return JsonResponse({'status': 'error', 'message': 'product number exceeeded'}, status=400)

                    return JsonResponse({'status': 'success', 'message': 'Product added to cart'})
                return JsonResponse({'status': 'error', 'message': 'Bad operation'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Product ID missing'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def get_cart(request):
    if request.user.is_authenticated:        
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(cart_id=cart_id, user__isnull=True)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = str(cart.cart_id)
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = str(cart.cart_id)
    return cart

import json
from django.http import JsonResponse
from .models import Product, CartItems # Ensure correct imports

@csrf_protect 
def viewCart(request):
    cart = get_cart(request)
    
    if request.method == 'POST':
        try:  
            data = json.loads(request.body)
            product_id = data.get('product_id')
            action = data.get('action')
            product = Product.objects.get(pk=product_id)
        except (json.JSONDecodeError, Product.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invalid data or product'}, status=400)
            
        cart_item, created = CartItems.objects.get_or_create(cart=cart, product=product)

        if action == "decrement":
            if cart_item.quantity > 0:
                cart_item.quantity -= 1
                cart_item.save()
            if cart_item.quantity == 0:
                cart_item.delete()
                new_qty = 0
            else:
                new_qty = cart_item.quantity

        elif action == 'increment':
            print(cart_item.quantity )
            if cart_item.quantity >= product.number_available and not created:
                return JsonResponse({'status': 'error', 'message': 'items limit reached'}, status=400)
            
            cart_item.quantity += 1
            cart_item.save()
            new_qty = cart_item.quantity
        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)

        # CRITICAL: Calculate new values for the frontend AJAX update
        # Assuming your CartItem model has a sum_price property and Cart has total_price
        return JsonResponse({
            'status': 'success',
            'message': 'Cart updated',
            'new_quantity': new_qty,
            'new_item_sum_price': cart_item.sum_price if new_qty > 0 else 0,
            'new_total_price': cart.total_price # Uses the property in your Cart model
        }, status=200)

    # GET logic
    if cart:
        cart_items = cart.cartItems.all()
        total_price = cart.total_price
        context = {
            "total_price": total_price,
            'cart_items': cart_items,
            "cart_id": cart.id
        }
        return render(request, "onlineStore/cart.html", context)
    
    return render(request, "onlineStore/cart.html", {"cart_items": [], "total_price": 0}) 

@csrf_protect # Enable CSRF protection
def delete_cart_item(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            print(request.body)
           
            if product_id:
                product = Product.objects.get(pk=product_id)
                cart = get_cart(request)
                
                try:
                    cart_item = CartItems.objects.get(cart=cart, product=product)
                    cart_item.delete()
                    return JsonResponse({'status': 'success', 'message': 'Cart item deleted'})                 
                except CartItems.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Cart item not found'}, status=404)
                
            else:
                return JsonResponse({'status': 'error', 'message': 'Product ID missing'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def products_description(request,id):
        cart= get_cart(request)
      
        product = Product.objects.get(id=id)


        try:
            product_cart_item = CartItems.objects.get(product=product,cart=cart)
               
        except CartItems.DoesNotExist:
            product_cart_item =''
        
        context={'product':product,'product_cart_item':product_cart_item}

        return render(request,"onlineStore/product.html",context)

@csrf_protect # Enable CSRF protection
def create_product(request):
    if request.method == 'POST':
        name = request.POST.get('name').title()
        category_name = request.POST.get('category', '').title()
        price = request.POST.get('price')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        number_available = request.POST.get('number_available')


        if not all([name, category_name, price, description,number_available]):
            messages.error(request, 'Please fill all fields.')
            return render(request, 'onlineStore/create_prod.html', {'name': name, 'category': category_name, 'price': price, 'description': description})

        try:
            category_obj = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            category_obj = Category.objects.create(name=category_name)

        product = Product.objects.create(
            name=name,
            category=category_obj,
            price=price,
            description=description,
            image=None ,
            number_available=number_available
        )

        if image:
            upload_response = upload_to_drive(image.open('rb'))
                  

            if upload_response:
                print(upload_response)
                product.image_url = upload_response['secure_url']
                product.save()  # Save again to store the Google Drive URL and ID
                messages.success(request, 'Product created successfully with image uploaded ')
                return redirect('onlinestore:products_description', id=product.id)
            else:
                messages.warning(request, 'Product created successfully, but image upload failed.')
                return redirect('onlinestore:products_description', id=product.id)
        else:
            messages.success(request, 'Product created successfully without an image.')
            return redirect('onlinestore:products_description', id=product.id)
    
    return render(request, 'onlineStore/create_prod.html')


# @login_required(login_url='onlinestore:login_user')
# @user_passes_test(test_func, login_url='onlinestore:login_user') # Ensure the user is authenticated and passes the test_func
@csrf_protect # Enable CSRF protection
def checkout(request):
    if request.method=='POST':
        try:
            cart= get_cart(request)
            data = json.loads(request.body)
            print(data)
            name = data.get('name').title()
            email = data.get('email')
            phone_number = data.get('phone_number')
            address = data.get('address')
            country = data.get('country').title()
            state = data.get('state').title()
            description = data.get('description')
            
            if cart.items_count > 0 and cart.items_count!=0 :
                if request.user.is_authenticated:
                    package = PackageForm.objects.create(customer_name=name,address=address,phone_number=phone_number,
                                               country=country,state=state,description=description,email=email,)
                    
                    order = Order.objects.create(cart=cart,
                                                 user=request.user,package_detail=package,
                                                 total_amount=cart.total_price,
                                                                )
                                                  
                    
                    if  data.get('payment_option')=='Paystack':
                        paystack_data = {'status': 'success',
                                           'public_key' :settings.PAYSTACK_PUBLIC_KEY,
                                            'transaction_id': str(order.order_id),
                                            'amount': order.total_amount, #get the total price from the cart.
                                            'email': request.user.email,
                                            'username': request.user.username,
                                            
                                            }
                                
                        return JsonResponse(paystack_data,)
                    
                    elif  data.get('payment_option')=='flutterwave':
                        print('flutter APPROVED')
                        data = {'status': 'success',
                                            'transaction_id':  str(order.order_id),
                                            'amount': order.total_amount, #get the total price from the cart.
                                            'email': request.user.email,
                                            'username': request.user.username,
                                            
                                            
                                        }
                                
                        return JsonResponse(data)
                    else:
                        return HttpResponse('invalid payment execution')
                else:
                    print('User not authenticated')
                    return JsonResponse({'error': ' Sign in to checkout '}, status=401)

            else:      
                return JsonResponse({'error': 'Cart is empty Please add items to your cart'}, status=400) # added json response.

                                              
        except Cart.DoesNotExist:
                return JsonResponse({'error': 'Cart not found'}, status=404)



@login_required(login_url='onlinestore:login_user')
def confirm_order_payment(request, transaction_id):
    order = Order.objects.get(order_id=transaction_id)
    if order.status == 'paid':
        messages.info(request, 'Order already confirmed.')
        return redirect('onlinestore:home')
   
    response = paystack.verify_payment(transaction_id)
    if response:
        messages.success(request, 'Order payment confirmed successfully!')
        return redirect('onlinestore:home')
    else:
        messages.error(request, 'Order payment confirmation failed. , if debited send us this Order ID '+ '"' +str(transaction_id)+ '"'+' for refund')
        return redirect('onlinestore:home')


@login_required(login_url='onlinestore:login_user')
def orders(request):
    orders = Order.objects.filter(user=request.user, status='paid').order_by('-created_at')

    if request.method == 'POST':
        filter_date = request.POST.get('filter-date')
        print(filter_date)
        if filter_date:
            try:
                # Attempt to filter by date.  This will work for dates without time.
                orders = orders.filter(created_at__date=filter_date).order_by('-created_at')
                if not orders.exists():
                    messages.error(request, 'No purchases found for the selected date.')
                    return redirect('onlinestore:orders')
            except FieldError:
                 try:
                    # Convert filter_date to a datetime object at midnight
                    filter_date_start = timezone.datetime.strptime(filter_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.get_current_timezone())
                    filter_date_end = filter_date_start + timezone.timedelta(days=1)
                    orders = orders.filter(created_at__gte=filter_date_start, created_at__lt=filter_date_end).order_by('-created_at')
                    if not orders.exists():
                        messages.error(request, 'No purchases found for the selected date.')
                        return redirect('onlinestore:orders')
                 except ValueError:
                    messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
                    return redirect('onlinestore:orders')
        else:
            messages.error(request, 'No purchased during this period select a valid date.')
            return redirect('onlinestore:orders')

    context = {'orders': orders}
    return render(request, 'onlineStore/orders.html', context)


from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        # 2. Input Validation (Security Barrier)
        if not all([username, email, password,password2]):
            messages.error(request, 'All fields are required.')
            return redirect('onlinestore:register')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('onlinestore:register')

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('onlinestore:register')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('onlinestore:register')

        # 3. Secure Account Creation
        try:
            # Check if user exists without revealing it (prevents enumeration)
            if MyUsers.objects.filter(email=email).exists() or MyUsers.objects.filter(username=username).exists():
                messages.error(request, 'That username or email is already taken.')
                return redirect('onlinestore:register')

            user = MyUsers.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('onlinestore:login_user')

        except IntegrityError:
            messages.error(request, 'A database error occurred. Please try again.')
            return redirect('onlinestore:register')
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            messages.error(request, 'An unexpected error occurred.')
            return redirect('onlinestore:register')
    return render(request, 'userform.html')


@csrf_protect
def clear_cart(request):
    if request.method == 'POST':
        cart = get_cart(request)
        if cart:
            cart.cartItems.all().delete()       
            return JsonResponse({'status': 'success', 'message': 'Cart cleared'})
        
        return JsonResponse({'status': 'error', 'message': 'Cart not found'}, status=404)
    
    return redirect('onlinestore:cart')


from django.contrib import messages, auth
from django.core.cache import cache
from django.views.decorators.debug import sensitive_post_parameters

@sensitive_post_parameters('password')
@csrf_protect
def login_user(request):
    if request.user.is_authenticated:
        return redirect('onlinestore:home')

    next_url = request.GET.get('next', 'onlinestore:home')

    if request.method == 'POST':
        email = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return redirect('onlinestore:login_user')
        
        # # Security: Get real IP even if behind a proxy (like Heroku/NGINX)
        # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        # if x_forwarded_for:
        #     ip_address = x_forwarded_for.split(',')[0]
        # else:
        #     ip_address = request.META.get('REMOTE_ADDR')

        # lockout_key = f"lockout_{ip_address}"
        # attempts_key = f"attempts_{ip_address}"
        
        # if cache.get(lockout_key):
        #     messages.error(request, 'Too many failed attempts. Please try again in 10 minutes.')
        #     return redirect('onlinestore:login_user')
    
        user=MyUsers.objects.filter(email=email).first()

        if user and user.check_password(password):
            if user.is_active:
                # cache.delete(attempts_key)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth.login(request, user)
                
                merge_carts(request, user)
                
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect to 'next' if it exists and is a safe internal URL
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('onlinestore:home')
            else:
                messages.error(request, 'This account has been disabled.')
                return redirect('onlinestore:login_user')
    #     else:
    #         fail_count = cache.get(attempts_key, 0) + 1
    #         cache.set(attempts_key, fail_count, timeout=600)

    #         if fail_count >= 5:
    #             cache.set(lockout_key, True, timeout=600)
    #             messages.error(request, 'Security Lockout: Too many attempts. Try again in 10 minutes.')
    #         else:
    #             messages.error(request, 'Invalid email or password.')
            
    #         return redirect('onlinestore:login_user')

    return render(request, 'userform.html', {
        "debug_check": settings.DEBUG,
        "next": next_url
    })


def logout_user(request):
    logout(request)
    messages.success(request,'you are logged out')
    return redirect('onlinestore:home')





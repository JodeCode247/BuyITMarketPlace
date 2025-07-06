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
 

def test_func(user):
        return user.is_authenticated # example.


@csrf_protect # Enable CSRF protection
def get_cart_count(request):
    cart = get_cart(request)
    if cart:
        count = cart.items_count
    else:
        count = 0
    return JsonResponse({'count': count})


def index(request):
    if request.method == 'GET':
        query = request.GET.get('query')
        if query:
        
            products = Product.objects.filter(Q(name__icontains=query)
                                            | Q(price__icontains=query)
                                            | Q(category__name__icontains=query)
                                            | Q(description__icontains=query)).values()
            if products.exists():
                context = {'products': products}
                return render(request, 'onlineStore/index.html', context)
        
            else:
                print("ITEM NOT FOUND")
                messages.error(request, 'No products found matching your search.')
                return redirect('onlinestore:home')
            
    try:
        products = Product.objects.only('name')
    except:
       return redirect('onlinestore:login_user')
        
    
    context = {'products':products}
    return render(request,"onlineStore/index.html",context)


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
                            return JsonResponse({'status': 'success', 'message': 'Quantity incremented'},status=400)
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
        print(cart_id,'found')
        print(request.session.items())
        if cart_id:
            try:
                cart = Cart.objects.get(cart_id=cart_id, user__isnull=True)
            except Cart.DoesNotExist:
                print('bad create')
                cart = Cart.objects.create()
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = str(cart.cart_id)
            print(request.session.get('cart_id'))
    return cart

@csrf_protect 
def viewCart(request):
    cart = get_cart(request)
    
    if request.method=='POST':
        try:  
            data = json.loads(request.body)
            product_id = data.get('product_id')
            action = data.get('action')
            print(data)
            product = Product.objects.get(pk=product_id)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
        try:
            cart_item = CartItems.objects.get(cart=cart,product=product)
            
            if action=="decrement":
                if cart_item.quantity >= 1:
                    cart_item.quantity-=1
                    cart_item.save()
                    return JsonResponse({'status': 'success', 'message': 'Quantity incremented'},status=400)


            elif action=='increment':
                if cart_item.quantity <= cart_item.product.number_available :
                    if cart_item.product.number_available == cart_item.quantity:
                        return JsonResponse({'status': 'error', 'message': 'product number exceeeded'}, status=400)
                    cart_item.quantity+=1
                    cart_item.save()
                    return JsonResponse({'status': 'success', 'message': 'Quantity incremented'},status=400)
                else:
                    return JsonResponse({'status': 'error', 'message': 'product number exceeeded'}, status=400)
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

        except CartItems.DoesNotExist:

            return HttpResponse(request,"cart not found")

            
    
    if cart :
            cart_items =cart.cartItems.all()

            total_price=cart.total_price
            cart_id=cart.id

            
            context ={"total_price":total_price,'cart_items':cart_items,"cart_id":cart_id}
            return render(request,"onlineStore/cart.html",context)
       

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


def register_user(request):
    if request.method=='POST':
        username = request.POST.get('username').upper()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        if password2==password:
            try:
                created = MyUsers.objects.get(email=email)
                if created:
                    messages.success(request, ' EMAIL IS NO LONGER AVAILABLE ENTER ANOTHER EMAIL')
                    return redirect('onlinestore:register')
            
            except:
                user= MyUsers.objects.create_user(username=username,email=email,password=password,is_staff=True,is_active=True)
                if user:
                    messages.success(request, 'User registered successfully! PLEASE LOGIN NOW')

                    return redirect('onlinestore:login_user')
            else:
                 messages.success(request, 'ERROR OCCURED SIGNUP FAILED')
                 return redirect('onlinestore:register')


        else:
            messages.success(request, 'PASSWORD MISMATCH')
            return redirect('onlinestore:register')

    return render (request,'userform.html')


@csrf_protect # Enable CSRF protection
def clear_cart(request):
    if request.method == 'POST':
        cart = get_cart(request)
        if cart:
            cart_items = cart.cartItems.all()
            cart_items.delete()
            return redirect('onlinestore:cart') # Redirect to the cart page
        else:
            return redirect('onlinestore:home') #Cart not found, redirect to home.
    return redirect('onlinestore:cart') #if not a post request, redirect to cart


def login_user(request):
    if request.method=='POST':
        password = request.POST.get('password')
        email = request.POST.get('username')
        if password and email: 
            try:
                user=MyUsers.objects.get(email=email)
            except MyUsers.DoesNotExist:
                 messages.success(request,'User not found')
                 return redirect('onlinestore:login_user')
            
            if user.check_password(password):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend') #specify the backend.
                merge_carts(request, user)
                messages.success(request,'you are logged in')
                return redirect('onlinestore:home')
            else:
                messages.error(request, 'Invalid email or password.') # Generic error for security
                return redirect('onlinestore:login_user')
        else:
            messages.error(request, 'Please provide both email and password.')
            return redirect('onlinestore:login_user')
                
    debug_check = settings.DEBUG   
    return render (request,'userform.html',{"debug_check":debug_check})


def logout_user(request):
    logout(request)
    messages.success(request,'you are logged out')
    return redirect('onlinestore:home')

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .manager import  CustomUserManager
from django.utils.translation import gettext_lazy as _
import uuid
from django.db import transaction



class MyUsers(AbstractBaseUser,PermissionsMixin):
    username = models.CharField(max_length=255,null=True,unique=True)
    email = models.EmailField(_("email address"), unique=True)
    created_at  = models.DateTimeField(default=timezone.now)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    objects =  CustomUserManager()

    USERNAME_FIELD = "email"  
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        if self.username:
            return self.username
        else:
            return self.email

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category =models.ForeignKey(Category,related_name="products", on_delete=models.DO_NOTHING)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True,blank=True)
    rating = models.IntegerField(default=0,blank=True)
    number_of_reviews =  models.IntegerField(default=0,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # Local file field
    image_url = models.URLField(blank=True, null=True)  # URL of the image on Google Drive
    is_available = models.BooleanField(default=True)
   
    def __str__(self):
        return self.name

    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"



class Cart(models.Model):
    user = models.OneToOneField(MyUsers, on_delete=models.CASCADE,blank=True,null=True) #one cart per user
    cart_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) #add a cart_id
    created_at = models.DateTimeField(auto_now_add=True)
        
    def __str__(self):
        return str(self.cart_id)


     
    @property
    def total_price(self):
        cartItems=self.cartItems.all()
        total = sum(item.sum_price for item in cartItems)
        return total
    
    @property
    def items_count(self):
        cartItems=self.cartItems.all()
        if cartItems:
            total = sum(item.quantity for item in cartItems)
            return total
        zero=0
        return zero
    
    
    

class CartItems(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cartItems') #related name is important
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='products')
    quantity = models.PositiveIntegerField(default=1)
    
    @property
    def sum_price(self):
        return self.product.price * self.quantity

    
    
class Order(models.Model):
    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, null=True, blank=True) # Optional: For logged-in users
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,related_name='orders')
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_reference = models.CharField(max_length=255, unique=True, blank=True, null=True) # Transaction reference from the payment gateway
    status = models.CharField(max_length=20, default='pending')  # pending, paid,
    created_at = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=3, default='NGN') # or whatever currency you are using
    payment_method = models.CharField(max_length=20, null=True) # or whatever payment method you are using
    package_detail =  models.ForeignKey("PackageForm",on_delete=models.CASCADE,related_name='orders',null=True)


    def __str__(self):
        return str(self.order_id)
    
    def confirm_payment(self,transaction_id):
       with transaction.atomic():
            cart_items = self.cart.cartItems.all() # get cart items from the order

            for cart_item in cart_items:
                if cart_item.quantity > 0:
                    OrderItem.objects.create(order=self, product=cart_item.product, quantity=cart_item.quantity, price=cart_item.product.price)
                else:
                    cart_item.delete()
            # Clear the cart after confirming payment
            cart_items.delete()
            self.status = 'paid'
            self.transaction_reference=transaction_id
            self.save()
            return True
            
class OrderItem(models.Model):  # New model
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Store the price at the time of order



class PackageForm(models.Model):
    customer_name =  models.CharField(max_length=200, ) 
    email = models.EmailField(_("email address"),)
    address = models.CharField(max_length=226, )
    country = models.CharField(max_length=20, ) 
    state = models.CharField(max_length=20, ) 
    phone_number =  models.CharField(max_length=11, ) 
    description = models.TextField(max_length=256, null=True, blank=True)  




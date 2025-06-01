from .models import Cart, CartItems  # Replace with your actual models
from django.shortcuts import get_object_or_404

def cart_item_count(request):
    count = 0
    cart = get_cart(request)
    if cart:
        count = CartItems.objects.filter(cart=cart).count()
    return {'cart_item_count': count}



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
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = str(cart.cart_id)
    return cart
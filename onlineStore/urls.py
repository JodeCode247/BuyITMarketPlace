from django.urls import path,include
from . import views 

app_name = "onlinestore"

urlpatterns = [
    
    path('',views.index,name='home'),
    path('add_to_cart/',views.add_to_cart,name='add_to_cart'),
    path('cart/',views.viewCart,name='cart'),
    path('get_cart_count/',views.get_cart_count,name='get_cart_count'),
    path('delete_cart_item/',views.delete_cart_item,name='delete_cart_item'),
     path('clear_cart/',views.clear_cart,name='clear_cart'),
    path('initialize_payment/',views.checkout,name='initialize_payment'),
    path('orders/',views.orders,name='orders'),
    path('products_create/', views.create_product, name='create_product'),
    

    path('confirm_order_payment/<str:transaction_id>',views.confirm_order_payment,name='confirm_order_payment'),
    
    path('product_detail/<int:id>',views.products_description,name='products_description'),


    
    path('register_user/',views.register_user,name='register'),
    path('login_user/',views.login_user,name='login_user'),
    path('logout/',views.logout_user,name='logout_user'),

    path('ela/', views.ela_upload_view, name='ela_upload'),


]

from django.contrib import admin
from .models import Cart,Category,CartItems,MyUsers,Product

admin.site.register(MyUsers)
admin.site.register(Category)
admin.site.register(Product)

admin.site.register(Cart)
admin.site.register(CartItems)
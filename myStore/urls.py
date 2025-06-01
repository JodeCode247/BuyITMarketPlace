
from django.contrib import admin
from django.urls import path,include
from django.contrib.auth import views as auth_views #for logout


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('onlineStore.urls')),
    path('accounts/', include('social_django.urls', namespace='social')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

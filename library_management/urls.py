from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from library import views  # <-- import your index view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('library.urls')),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    path('', views.index, name='home'), 
]

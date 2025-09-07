from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

# Router for ViewSets
router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book')
router.register(r'checkouts', views.CheckoutViewSet, basename='checkout')

urlpatterns = [
    # API endpoints from routers
    path('', include(router.urls)),

    # Authentication
    path('auth/register/', views.register_user, name='register'),
    path('auth/login/', views.login_user, name='login'),
    path('auth/logout/', views.logout_user, name='logout'),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/profile/', views.user_profile, name='user_profile'),

    # Checkout-related endpoints
    path('checkouts/my/', views.my_checkouts, name='my_checkouts'),
    path('checkouts/history/', views.checkout_history, name='checkout_history'),

    # Statistics endpoint
    path('stats/', views.library_stats, name='library_stats'),

    # Utility endpoints
    path('health/', views.health_check, name='health_check'),
    path('index/', views.index, name='index'),
]
# library/views.py

from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import filters
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from .models import Book, UserProfile, Checkout
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    BookSerializer, BookListSerializer, BookSearchSerializer,
    CheckoutSerializer, CheckoutCreateSerializer, CheckoutReturnSerializer,
    MyCheckoutsSerializer, LibraryStatsSerializer
)

# AUTHENTICATION VIEWS


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'error': 'Token not found'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    profile = request.user.profile
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully', 'profile': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# BOOK VIEWSET
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('title')
    serializer_class = BookSerializer
    lookup_field = 'book_id'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['list', 'search']:
            return BookListSerializer
        return BookSerializer

    @action(detail=False, methods=['get'], url_path='search', permission_classes=[AllowAny])
    def search(self, request):
        """
        Example request:
        /books/search/?search=Harry%20Potter&author=Rowling&genre=Fantasy&available_only=true
        """
        search_term = request.query_params.get('search', None)
        author = request.query_params.get('author', None)
        genre = request.query_params.get('genre', None)
        available_only = request.query_params.get('available_only', None)

        queryset = Book.objects.all()

        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(author__icontains=search_term) |
                Q(isbn__icontains=search_term)
            )
        if author:
            queryset = queryset.filter(author__icontains=author)
        if genre:
            queryset = queryset.filter(genre__icontains=genre)
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(available_copies__gt=0)

        serializer = BookListSerializer(queryset.order_by('title'), many=True)
        return Response({'count': queryset.count(), 'results': serializer.data})
    
# CHECKOUT VIEWS


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_checkouts(request):
    checkouts = Checkout.objects.filter(user=request.user, is_returned=False).order_by('-checkout_date')
    serializer = MyCheckoutsSerializer(checkouts, many=True)
    return Response({'count': checkouts.count(), 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def checkout_history(request):
    checkouts = Checkout.objects.filter(user=request.user).order_by('-checkout_date')
    page_size = int(request.query_params.get('page_size', 10))
    page = int(request.query_params.get('page', 1))
    start = (page - 1) * page_size
    end = start + page_size
    serializer = CheckoutSerializer(checkouts[start:end], many=True)
    return Response({
        'count': checkouts.count(),
        'results': serializer.data,
        'page': page,
        'page_size': page_size,
        'total_pages': (checkouts.count() + page_size - 1) // page_size
    })


class CheckoutViewSet(viewsets.ModelViewSet):
    queryset = Checkout.objects.all().order_by('-checkout_date')
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'checkout_id'

    def get_permissions(self):
        if self.request.user.is_staff:
            return [IsAuthenticated()]
        return [permissions.DjangoModelPermissions()]

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        overdue_checkouts = Checkout.objects.filter(is_returned=False, due_date__lt=timezone.now()).order_by('due_date')
        serializer = CheckoutSerializer(overdue_checkouts, many=True)
        return Response({'count': overdue_checkouts.count(), 'results': serializer.data})


# STATISTICS VIEW

from django.utils import timezone
from django.db.models import Count, Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Book, Checkout, UserProfile
from django.contrib.auth.models import User
from .serializers import LibraryStatsSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def library_stats(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

    # Basic counts
    total_books = Book.objects.count()
    total_copies = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0
    checked_out_copies = total_copies - available_copies
    total_users = User.objects.count()
    active_users = UserProfile.objects.filter(is_active=True).count()
    total_checkouts = Checkout.objects.count()
    current_checkouts = Checkout.objects.filter(is_returned=False).count()
    overdue_checkouts = Checkout.objects.filter(is_returned=False, due_date__lt=timezone.now()).count()

    # Popular books (most checked out)
    # Use 'checkouts' as Count() to match your model field
    popular_books = Book.objects.annotate(total_checkouts=Count('checkouts')).order_by('-total_checkouts')[:5]
    popular_books_data = [
        {
            'title': book.title,
            'author': book.author,
            'checkout_count': book.total_checkouts # Map annotated field to output
        }
        for book in popular_books
    ]

    # Recent checkouts
    recent_checkouts = Checkout.objects.select_related('user', 'book').order_by('-checkout_date')[:10]
    recent_checkouts_data = [
        {
            'user': checkout.user.username,
            'book': checkout.book.title,
            'checkout_date': checkout.checkout_date,
            'is_returned': checkout.is_returned
        }
        for checkout in recent_checkouts
    ]

    # Combine stats
    stats_data = {
        'total_books': total_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'checked_out_copies': checked_out_copies,
        'total_users': total_users,
        'active_users': active_users,
        'total_checkouts': total_checkouts,
        'current_checkouts': current_checkouts,
        'overdue_checkouts': overdue_checkouts,
        'popular_books': popular_books_data,
        'recent_checkouts': recent_checkouts_data
    }

    serializer = LibraryStatsSerializer(data=stats_data)
    if serializer.is_valid():
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# UTILITY VIEWS

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'message': 'Library Management System API is running',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    return Response({
        'message': 'Welcome to the Library Management System API',
        'status': 'ok',
        'timestamp': timezone.now().isoformat()
    })
from django_filters.rest_framework import DjangoFilterBackend

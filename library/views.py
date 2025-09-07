# library/views.py

from django.db.models import Sum, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from datetime import timedelta

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Book, UserProfile, Checkout
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    BookSerializer, BookListSerializer, CheckoutSerializer,
    MyCheckoutsSerializer
)


# PAGINATION

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# AUTH VIEWS

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
    Token.objects.filter(user=request.user).delete()
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully', 'profile': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# BOOKS VIEWSET

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('title')
    serializer_class = BookSerializer
    lookup_field = 'book_id'
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'genre']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'author', 'published_date']
    ordering = ['title']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search', 'available']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['list', 'search', 'available']:
            return BookListSerializer
        return BookSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available(self, request):
        available_books = Book.objects.filter(available_copies__gt=0).order_by('title')
        page = self.paginate_queryset(available_books)
        if page is not None:
            serializer = BookListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BookListSerializer(available_books, many=True)
        return Response({'count': available_books.count(), 'results': serializer.data})

    @action(detail=False, methods=['get'], url_path='search', permission_classes=[AllowAny])
    def search(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        available_only = request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(available_copies__gt=0)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BookListSerializer(queryset, many=True)
        return Response({'count': queryset.count(), 'results': serializer.data})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def checkout(self, request, book_id=None):
        book = get_object_or_404(Book, book_id=book_id)
        user = request.user

        if book.available_copies < 1:
            return Response({'error': 'No copies available'}, status=status.HTTP_400_BAD_REQUEST)

        if Checkout.objects.filter(user=user, book=book, is_returned=False).exists():
            return Response({'error': 'Already checked out'}, status=status.HTTP_400_BAD_REQUEST)

        checkout = Checkout.objects.create(
            user=user,
            book=book,
            due_date=timezone.now() + timedelta(days=14)
        )
        book.available_copies -= 1
        book.save()

        serializer = CheckoutSerializer(checkout)
        return Response({'message': 'Book checked out', 'checkout': serializer.data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def return_book(self, request, book_id=None):
        book = get_object_or_404(Book, book_id=book_id)
        user = request.user

        checkout = Checkout.objects.filter(user=user, book=book, is_returned=False).first()
        if not checkout:
            return Response({'error': 'You did not checkout this book'}, status=status.HTTP_400_BAD_REQUEST)

        checkout.is_returned = True
        checkout.return_date = timezone.now()
        checkout.save()

        book.available_copies += 1
        book.save()

        serializer = CheckoutSerializer(checkout)
        return Response({'message': 'Book returned', 'checkout': serializer.data}, status=status.HTTP_200_OK)


# CHECKOUTS VIEWSET


class CheckoutViewSet(viewsets.ModelViewSet):
    queryset = Checkout.objects.all().order_by('-checkout_date')
    serializer_class = CheckoutSerializer
    lookup_field = 'checkout_id'
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def my(self, request):
        checkouts = Checkout.objects.filter(user=request.user, is_returned=False).order_by('-checkout_date')
        serializer = MyCheckoutsSerializer(checkouts, many=True)
        return Response({'count': checkouts.count(), 'results': serializer.data})

    @action(detail=False, methods=['get'])
    def history(self, request):
        checkouts = Checkout.objects.filter(user=request.user).order_by('-checkout_date')
        page = self.paginate_queryset(checkouts)
        if page is not None:
            serializer = CheckoutSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CheckoutSerializer(checkouts, many=True)
        return Response({'count': checkouts.count(), 'results': serializer.data})

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        overdue_checkouts = Checkout.objects.filter(is_returned=False, due_date__lt=timezone.now()).order_by('due_date')
        page = self.paginate_queryset(overdue_checkouts)
        if page is not None:
            serializer = CheckoutSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CheckoutSerializer(overdue_checkouts, many=True)
        return Response({'count': overdue_checkouts.count(), 'results': serializer.data})


# FUNCTION-BASED VIEWS FOR URLS.PY


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
    page = StandardResultsSetPagination().paginate_queryset(checkouts, request)
    serializer = CheckoutSerializer(page, many=True)
    return StandardResultsSetPagination().get_paginated_response(serializer.data)


# STATS


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def library_stats(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    total_books = Book.objects.count()
    total_copies = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0
    checked_out_copies = total_copies - available_copies
    total_users = User.objects.count()
    active_users = UserProfile.objects.filter(is_active=True).count()
    total_checkouts = Checkout.objects.count()
    current_checkouts = Checkout.objects.filter(is_returned=False).count()
    overdue_checkouts = Checkout.objects.filter(is_returned=False, due_date__lt=timezone.now()).count()

    popular_books = Book.objects.annotate(total_checkouts=Count('checkouts')).order_by('-total_checkouts')[:5]
    popular_books_data = [
        {'title': book.title, 'author': book.author, 'checkout_count': book.total_checkouts}
        for book in popular_books
    ]

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

    return Response({
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
    })


# UTILITY


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

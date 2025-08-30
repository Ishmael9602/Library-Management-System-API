from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, UserProfile, Checkout
from django.contrib.auth import authenticate

# Book Serializers


class BookSerializer(serializers.ModelSerializer):
    book_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "book_id",
            "title",
            "author",
            "isbn",
            "publisher",
            "published_date",
            "genre",
            "total_copies",
            "available_copies",
            "description",
            "is_available",
            "checkout_count",
            "date_added",
            "date_updated",
        ]
        read_only_fields = ["is_available", "checkout_count", "date_added", "date_updated"]

    def validate_isbn(self, value):
        if not (len(value) == 10 or len(value) == 13) or not value.isdigit():
            raise serializers.ValidationError("ISBN must be exactly 10 or 13 digits.")
        return value

    def validate_available_copies(self, value):
        total = self.initial_data.get('total_copies')
        if total is not None and int(value) > int(total):
            raise serializers.ValidationError("Available copies cannot exceed total copies.")
        return value


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["book_id", "title", "author", "available_copies"]


# Book Search Serializer (for /books/search/)
class BookSearchSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    author = serializers.CharField(required=False)
    isbn = serializers.CharField(required=False)
    genre = serializers.CharField(required=False)
    available_only = serializers.BooleanField(required=False)

# User Serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    current_checkouts = serializers.IntegerField(source='current_checkouts.count', read_only=True)
    total_checkouts = serializers.IntegerField(source='total_checkouts', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "date_of_membership",
            "is_active",
            "phone_number",
            "address",
            "current_checkouts",
            "total_checkouts",
            "date_created",
            "date_updated",
        ]


# Checkout Serializers

class CheckoutSerializer(serializers.ModelSerializer):
    checkout_id = serializers.UUIDField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    is_overdue = serializers.BooleanField(source='is_overdue', read_only=True)
    days_overdue = serializers.IntegerField(source='days_overdue', read_only=True)

    class Meta:
        model = Checkout
        fields = [
            "checkout_id",
            "user",
            "book",
            "checkout_date",
            "due_date",
            "return_date",
            "is_returned",
            "late_fee",
            "notes",
            "is_overdue",
            "days_overdue",
        ]
        read_only_fields = ["checkout_date", "late_fee", "is_overdue", "days_overdue"]

    def validate(self, attrs):
        user = attrs.get("user")
        book = attrs.get("book")
        is_returned = attrs.get("is_returned", False)
        return_date = attrs.get("return_date")

        if not is_returned:
            existing = Checkout.objects.filter(user=user, book=book, is_returned=False)
            if existing.exists():
                raise serializers.ValidationError("User already has this book checked out.")

        if return_date and return_date < attrs.get("checkout_date", None):
            raise serializers.ValidationError("Return date cannot be before checkout date.")

        return attrs


class CheckoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkout
        fields = ["user", "book", "due_date", "notes"]


class CheckoutReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkout
        fields = ["return_date", "is_returned", "notes"]

    def validate(self, attrs):
        checkout = self.instance
        return_date = attrs.get("return_date")
        if return_date and checkout and return_date < checkout.checkout_date:
            raise serializers.ValidationError("Return date cannot be before checkout date.")
        return attrs


class MyCheckoutsSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Checkout
        fields = [
            "id",
            "book",
            "checkout_date",
            "due_date",
            "return_date",
            "is_returned",
        ]


# User Authentication Serializers

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                data["user"] = user
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'.")
        return data

# Library Stats Serializer

class LibraryStatsSerializer(serializers.Serializer):
    total_books = serializers.IntegerField()
    total_checkouts = serializers.IntegerField()
    total_users = serializers.IntegerField()

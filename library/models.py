from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone

class Book(models.Model):
    """
    Model representing a book in the library
    """
    title = models.CharField(max_length=200, help_text="Book title")
    author = models.CharField(max_length=100, help_text="Book author")
    isbn = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{10}(\d{3})?$',
                message='ISBN must be 10 or 13 digits'
            )
        ],
        help_text="ISBN number (10 or 13 digits)"
    )
    publisher = models.CharField(max_length=100, blank=True, help_text="Publisher name")
    published_date = models.DateField(help_text="Publication date")
    genre = models.CharField(max_length=50, blank=True, help_text="Book genre")
    total_copies = models.PositiveIntegerField(default=1, help_text="Total number of copies")
    available_copies = models.PositiveIntegerField(default=1, help_text="Available copies")
    description = models.TextField(blank=True, help_text="Book description")
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['isbn']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError
        
        if self.available_copies > self.total_copies:
            raise ValidationError(
                'Available copies cannot be greater than total copies.'
            )
        
        if self.total_copies < 1:
            raise ValidationError('Total copies must be at least 1.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        """Check if book is available for checkout"""
        return self.available_copies > 0

    @property
    def checkout_count(self):
        """Number of times this book has been checked out"""
        return self.checkouts.count()

class UserProfile(models.Model):
    """
    Extended user profile for library members
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_membership = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: "+999999999"'
            )
        ]
    )
    address = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_of_membership']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Member"

    @property
    def current_checkouts(self):
        """Get current active checkouts for this user"""
        return Checkout.objects.filter(user=self.user, return_date__isnull=True)

    @property
    def total_checkouts(self):
        """Total number of books ever checked out by this user"""
        return Checkout.objects.filter(user=self.user).count()

class Checkout(models.Model):
    """
    Model representing a book checkout transaction
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkouts')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='checkouts')
    checkout_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    late_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-checkout_date']
        unique_together = ['user', 'book', 'is_returned']
        indexes = [
            models.Index(fields=['user', 'is_returned']),
            models.Index(fields=['book', 'is_returned']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        status = "Returned" if self.is_returned else "Checked Out"
        return f"{self.user.username} - {self.book.title} ({status})"

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError
        
        # Check if user already has this book checked out
        if not self.is_returned:
            existing_checkout = Checkout.objects.filter(
                user=self.user,
                book=self.book,
                is_returned=False
            ).exclude(pk=self.pk)
            
            if existing_checkout.exists():
                raise ValidationError(
                    'User already has this book checked out.'
                )

        # Validate return date
        if self.return_date and self.return_date < self.checkout_date:
            raise ValidationError(
                'Return date cannot be before checkout date.'
            )

    def save(self, *args, **kwargs):
        # Set due date if not provided (default 14 days)
        if not self.due_date:
            from datetime import timedelta
            self.due_date = timezone.now() + timedelta(days=14)
        
        # Calculate late fee if returning after due date
        if self.return_date and self.return_date > self.due_date and not self.is_returned:
            days_late = (self.return_date - self.due_date).days
            self.late_fee = max(0, days_late * 1.00)  # $1.00 per day late
        
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if this checkout is overdue"""
        if self.is_returned:
            return False
        return timezone.now() > self.due_date

    @property
    def days_overdue(self):
        """Number of days this checkout is overdue"""
        if not self.is_overdue:
            return 0
        return (timezone.now() - self.due_date).days

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Book, UserProfile, Checkout

# Unregister the default User admin
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_membership_date')
    list_filter = UserAdmin.list_filter + ('profile__is_active',)

    def get_membership_date(self, obj):
        return obj.profile.date_of_membership if hasattr(obj, 'profile') else None
    get_membership_date.short_description = 'Membership Date'

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'total_copies', 'available_copies', 'is_available')
    list_filter = ('genre', 'published_date', 'date_added')
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('date_added', 'date_updated', 'checkout_count')
    ordering = ('title',)
    
    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'author', 'isbn', 'publisher', 'published_date', 'genre')
        }),
        ('Copies', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('date_added', 'date_updated', 'checkout_count'),
            'classes': ('collapse',)
        })
    )

@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'checkout_date', 'due_date', 'return_date', 'is_returned', 'is_overdue')
    list_filter = ('is_returned', 'checkout_date', 'due_date')
    search_fields = ('user__username', 'book__title', 'book__author')
    readonly_fields = ('checkout_date', 'is_overdue', 'days_overdue')
    date_hierarchy = 'checkout_date'
    
    fieldsets = (
        ('Checkout Information', {
            'fields': ('user', 'book', 'checkout_date', 'due_date')
        }),
        ('Return Information', {
            'fields': ('return_date', 'is_returned', 'late_fee')
        }),
        ('Status', {
            'fields': ('is_overdue', 'days_overdue'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )

admin.site.register(User, CustomUserAdmin)

admin.site.site_header = "Library Management System"
admin.site.site_title = "Library Admin"
admin.site.index_title = "Welcome to Library Management System"
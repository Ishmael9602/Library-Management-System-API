from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Checkout

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Checkout)
def update_book_availability_on_checkout(sender, instance, created, **kwargs):
    """Update book availability when checkout is created or returned"""
    if created and not instance.is_returned:
        # Book checked out - decrease available copies
        book = instance.book
        if book.available_copies > 0:
            book.available_copies -= 1
            book.save(update_fields=['available_copies'])

@receiver(post_save, sender=Checkout)
def update_book_availability_on_return(sender, instance, **kwargs):
    """Update book availability when book is returned"""
    if instance.is_returned and instance.return_date:
        # Book returned - increase available copies
        book = instance.book
        if book.available_copies < book.total_copies:
            book.available_copies += 1
            book.save(update_fields=['available_copies'])

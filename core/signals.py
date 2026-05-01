from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)

from django.conf import settings
from django.db import models


class UserRole(models.TextChoices):
    """CRM role choices for UserProfile."""
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    SALES = "sales", "Sales"


class UserProfile(models.Model):
    """
    UserProfile extends Django's built-in User with CRM-specific fields.

    Linked via OneToOneField to avoid touching existing migrations.
    Authentication, email, names, and is_active remain on the User model.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user.username} — {self.role or 'no role'}"

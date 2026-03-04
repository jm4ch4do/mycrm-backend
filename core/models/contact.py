import uuid

from django.conf import settings
from django.db import models


class ContactRole(models.TextChoices):
    """Role choices for Contact."""

    DECISION_MAKER = "decision_maker", "Decision Maker"
    INFLUENCER = "influencer", "Influencer"
    USER = "user", "User"


class ContactSeniority(models.TextChoices):
    """Seniority choices for Contact."""

    JUNIOR = "junior", "Junior"
    SENIOR = "senior", "Senior"
    EXECUTIVE = "executive", "Executive"


class PreferredChannel(models.TextChoices):
    """Preferred communication channel choices for Contact."""

    EMAIL = "email", "Email"
    PHONE = "phone", "Phone"
    NONE = "none", "None"


class Contact(models.Model):
    """
    Contact entity represents an individual person working at an Account.

    Contacts are the actual human relationships within a customer organization.
    They belong to one Account and can participate in multiple Deals.
    """

    # Core Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)

    # Professional Info
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(
        max_length=20, choices=ContactRole.choices, blank=True, null=True
    )
    seniority = models.CharField(
        max_length=20, choices=ContactSeniority.choices, blank=True, null=True
    )

    # Association
    account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,  # can't delete account if it has contacts
        related_name="contacts",
    )
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # can't delete user if it has contacts
        null=True,
        blank=True,
        related_name="owned_contacts",
    )
    primary_contact = models.BooleanField(default=False)

    # Communication Preferences
    preferred_channel = models.CharField(
        max_length=20, choices=PreferredChannel.choices, blank=True, null=True
    )
    opt_in_email = models.BooleanField(default=True)
    opt_in_sms = models.BooleanField(default=False)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts_updated",
    )
    is_invalid = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account"]),
            models.Index(fields=["owner_user"]),
            models.Index(fields=["role"]),
            models.Index(fields=["seniority"]),
            models.Index(fields=["is_invalid"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "email"],
                name="unique_contact_email_per_account",
                condition=models.Q(email__isnull=False),
            ),
        ]

    @property
    def full_name(self) -> str:
        """Return the full name of the contact."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def __str__(self) -> str:
        return self.full_name

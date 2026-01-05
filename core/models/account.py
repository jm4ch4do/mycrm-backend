import uuid

from django.conf import settings
from django.db import models

from core.managers import AccountManager


class AccountStatus(models.TextChoices):
    """Status choices for Account."""
    PROSPECT = "prospect", "Prospect"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    LOST = "lost", "Lost"


class AccountType(models.TextChoices):
    """Type choices for Account."""
    CUSTOMER = "customer", "Customer"
    PARTNER = "partner", "Partner"
    VENDOR = "vendor", "Vendor"


class CompanySize(models.TextChoices):
    """Company size choices."""
    SIZE_1_10 = "1-10", "1–10"
    SIZE_11_50 = "11-50", "11–50"
    SIZE_51_200 = "51-200", "51–200"
    SIZE_200_PLUS = "200+", "200+"


class Account(models.Model):
    """
    Account entity represents a company or organization.
    
    Acts as the top-level customer object in the CRM and serves as the
    aggregation point for contacts, deals, and historical interactions.
    """

    # Core Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    account_number = models.CharField(
        max_length=50, unique=True, blank=True, null=True
    )
    status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.PROSPECT,
        null=True,
        blank=True,
    )
    type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CUSTOMER,
        null=True,
        blank=True,
    )

    # Business Metadata
    industry = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.CharField(
        max_length=20, choices=CompanySize.choices, blank=True, null=True
    )
    annual_revenue = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Ownership & Audit
    # owner_user: identifies who owns/manages this account
    # on_delete=PROTECT prevents deleting a user if they own accounts (data integrity)
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_accounts",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_updated",
    )
    is_invalid = models.BooleanField(default=False, null=True, blank=True)

    # Billing Address
    billing_street = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_state = models.CharField(max_length=100, blank=True, null=True)
    billing_country = models.CharField(max_length=100, blank=True, null=True)
    billing_postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Shipping Address
    shipping_street = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_country = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Custom Manager
    objects = AccountManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner_user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_invalid"]),
        ]

    def __str__(self) -> str:
        return str(self.name)

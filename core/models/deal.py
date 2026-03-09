import uuid

from django.conf import settings
from django.db import models


class DealStage(models.TextChoices):
    """Pipeline stage choices for Deal."""

    LEAD = "lead", "Lead"
    QUALIFIED = "qualified", "Qualified"
    PROPOSAL = "proposal", "Proposal"
    NEGOTIATION = "negotiation", "Negotiation"
    WON = "won", "Won"
    LOST = "lost", "Lost"


class DealStatus(models.TextChoices):
    """Status choices for Deal."""

    OPEN = "open", "Open"
    WON = "won", "Won"
    LOST = "lost", "Lost"


class LeadSource(models.TextChoices):
    """Lead source choices for Deal."""

    INBOUND = "inbound", "Inbound"
    OUTBOUND = "outbound", "Outbound"
    REFERRAL = "referral", "Referral"


class Currency(models.TextChoices):
    """Currency choices for Deal."""

    USD = "usd", "USD"
    EUR = "eur", "EUR"
    GBP = "gbp", "GBP"
    OTHER = "other", "Other"


class Deal(models.Model):
    """
    Deal entity represents a revenue opportunity in the sales pipeline.

    Deals track the commercial lifecycle from qualification to closing and are
    the core unit for revenue forecasting. A Deal always belongs to an Account
    and can be associated with multiple Contacts via DealContactAssoc.
    """

    # Core Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="deals",
    )

    # Financial
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=Currency.choices, blank=True, null=True
    )
    expected_close_date = models.DateField(blank=True, null=True)
    probability = models.IntegerField(blank=True, null=True)

    # Pipeline
    stage = models.CharField(
        max_length=20, choices=DealStage.choices, blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=DealStatus.choices, blank=True, null=True
    )
    loss_reason = models.CharField(max_length=255, blank=True, null=True)

    # Source
    lead_source = models.CharField(
        max_length=20, choices=LeadSource.choices, blank=True, null=True
    )

    # Ownership & Audit
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_deals",
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
        related_name="deals_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals_updated",
    )
    closed_at = models.DateTimeField(blank=True, null=True)
    is_invalid = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account"]),
            models.Index(fields=["owner_user"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_invalid"]),
        ]

    def __str__(self) -> str:
        return str(self.name)


class DealContactAssoc(models.Model):
    """
    Explicit join table linking Deals and Contacts.

    Tracks which Contacts are involved in a Deal.
    """

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name="contact_assocs",
    )
    contact = models.ForeignKey(
        "Contact",
        on_delete=models.CASCADE,
        related_name="deal_assocs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["deal", "contact"],
                name="unique_deal_contact",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.deal} - {self.contact}"

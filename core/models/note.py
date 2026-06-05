"""Note model for standalone CRM notes."""

import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class NoteVisibility(models.TextChoices):
    """Visibility levels for notes."""

    PRIVATE = "private", "Private"
    TEAM = "team", "Team"
    PUBLIC = "public", "Public"


class Note(models.Model):
    """
    Note entity for capturing customer interactions and observations.

    Unlike Task, Meeting, and Call, Note is a standalone entity with no
    dependency on Activity. Notes can be linked to Accounts, Contacts, or
    Deals, and support visibility control and pinning.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()

    # Author and entity relationships
    author = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="notes"
    )
    account = models.ForeignKey(
        "Account", on_delete=models.PROTECT, null=True, blank=True
    )
    contact = models.ForeignKey(
        "Contact", on_delete=models.PROTECT, null=True, blank=True
    )
    deal = models.ForeignKey(
        "Deal", on_delete=models.PROTECT, null=True, blank=True
    )

    # Note-specific attributes
    visibility = models.CharField(
        max_length=20,
        choices=NoteVisibility.choices,
        default=NoteVisibility.PRIVATE,
    )
    is_pinned = models.BooleanField(default=False)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    # Soft delete
    is_invalid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["is_pinned"]),
            models.Index(fields=["account"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["deal"]),
        ]

    def __str__(self):
        return f"{self.title or 'Note'} by {self.author}"

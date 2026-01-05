"""Custom manager for Account model."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django.db import models

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User


class AccountQuerySet(models.QuerySet):
    """Custom QuerySet for Account model enabling method chaining."""

    def active(self) -> AccountQuerySet:
        """Return all non-deleted (active) accounts."""
        return self.filter(is_invalid=False)

    def by_owner(self, user: User) -> AccountQuerySet:
        """Return accounts owned by the given user."""
        return self.filter(owner_user=user)

    def filter_by_params(
        self,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[User] = None,
    ) -> AccountQuerySet:
        """Filter accounts dynamically based on provided parameters."""
        queryset = self

        if industry is not None:
            queryset = queryset.filter(industry=industry)

        if company_size is not None:
            queryset = queryset.filter(company_size=company_size)

        if status is not None:
            queryset = queryset.filter(status=status)

        if owner is not None:
            queryset = queryset.filter(owner_user=owner)

        return queryset


class AccountManager(models.Manager):
    """Custom manager for Account model with filtering and chaining support."""

    def get_queryset(self) -> AccountQuerySet:
        """Return custom QuerySet for method chaining."""
        return AccountQuerySet(self.model, using=self._db)

    def active(self) -> AccountQuerySet:
        """Return all non-deleted (active) accounts."""
        return self.get_queryset().active()

    def by_owner(self, user: User) -> AccountQuerySet:
        """Return accounts owned by the given user."""
        return self.get_queryset().by_owner(user)

    def filter_by_params(
        self,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[User] = None,
    ) -> AccountQuerySet:
        """Filter accounts dynamically based on provided parameters."""
        return self.get_queryset().filter_by_params(
            industry=industry,
            company_size=company_size,
            status=status,
            owner=owner,
        )

"""Business logic service for User/UserProfile."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import UserProfile

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

UserModel = get_user_model()


class UserService:
    """Service layer for User/UserProfile business logic."""

    @staticmethod
    def list_users():
        """Retrieve all users with their profiles."""
        return UserModel.objects.select_related("profile").order_by("id")

    @staticmethod
    def get_user(user_id: int) -> User:
        """Retrieve a single user by ID."""
        return get_object_or_404(UserModel.objects.select_related("profile"), id=user_id)

    @staticmethod
    @transaction.atomic
    def update_user_role(user: User, role: str) -> UserProfile:
        """Update the CRM role on the user's profile."""
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()
        return profile

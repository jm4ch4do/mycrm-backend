"""API tests for Task endpoints."""

from datetime import timedelta
from typing import Optional
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Account,
    AccountStatus,
    AccountType,
    ActivityStatus,
    Task,
    TaskState,
)
from core.services.domain.task_service import TaskService

UserModel = get_user_model()
TASKS_URL = "/tasks/"


def task_url(pk):
    """Return the detail URL for a task by primary key."""
    return f"/tasks/{pk}/"


def complete_url(pk):
    """Return the complete action URL for a task by primary key."""
    return f"/tasks/{pk}/complete/"


@pytest.mark.django_db
class TestTaskCreate:
    """Tests for POST /tasks/."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        """Set up API client, authenticated user, and default account."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="owner", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Acme",
            status=AccountStatus.PROSPECT,
            type=AccountType.CUSTOMER,
            owner_user=self.user,
        )

    def test_create_task_returns_201(self):
        """POST /tasks/ returns HTTP 201 Created."""
        payload = {"title": "Follow up", "account": str(self.account.id)}
        response = self.client.post(TASKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_task_response_includes_title(self):
        """POST /tasks/ response body contains the task title."""
        payload = {"title": "Call client", "account": str(self.account.id)}
        response = self.client.post(TASKS_URL, payload, format="json")
        assert response.data["title"] == "Call client"

    def test_create_task_sets_status_open(self):
        """POST /tasks/ creates a task with state 'open'."""
        payload = {"title": "New task", "account": str(self.account.id)}
        response = self.client.post(TASKS_URL, payload, format="json")
        assert response.data["state"] == TaskState.OPEN

    def test_create_task_without_entity_reference_returns_400(self):
        """POST /tasks/ without an entity FK returns HTTP 400."""
        payload = {"title": "Orphan"}
        response = self.client.post(TASKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_task_unauthenticated_returns_403(self):
        """POST /tasks/ without auth returns HTTP 401 or 403."""
        self.client.force_authenticate(user=None)
        payload = {"title": "Task", "account": str(self.account.id)}
        response = self.client.post(TASKS_URL, payload, format="json")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_task_with_priority_and_category(self):
        """POST /tasks/ with priority and category stores both fields."""
        payload = {
            "title": "Admin task",
            "account": str(self.account.id),
            "priority": "high",
            "category": "admin",
        }
        response = self.client.post(TASKS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["priority"] == "high"
        assert response.data["category"] == "admin"


@pytest.mark.django_db
class TestTaskList:
    """Tests for GET /tasks/."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        """Set up API client, authenticated user, and default account."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="owner", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Acme",
            status=AccountStatus.PROSPECT,
            type=AccountType.CUSTOMER,
            owner_user=self.user,
        )

    def test_list_returns_200(self):
        """GET /tasks/ returns HTTP 200 OK."""
        response = self.client.get(TASKS_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_list_returns_only_active_tasks(self):
        """GET /tasks/ excludes soft-deleted tasks."""
        task = TaskService.create_task(
            {"title": "Active", "account": self.account}, self.user
        )
        deleted = TaskService.create_task(
            {"title": "Deleted", "account": self.account}, self.user
        )
        TaskService.soft_delete_task(deleted, self.user)

        response = self.client.get(TASKS_URL)
        ids = [r["id"] for r in response.data["results"]]
        assert str(task.id) in ids
        assert str(deleted.id) not in ids

    def test_list_is_paginated(self):
        """GET /tasks/ response includes pagination keys."""
        response = self.client.get(TASKS_URL)
        assert "results" in response.data
        assert "count" in response.data

    def test_filter_by_status(self):
        """GET /tasks/?state=open returns only open tasks."""
        open_task = TaskService.create_task(
            {"title": "Open", "account": self.account}, self.user
        )
        TaskService.create_task(
            {"title": "To be completed", "account": self.account}, self.user
        )
        # Complete the second task via service
        second = Task.objects.filter(activity__title="To be completed").first()
        TaskService.complete_task(second, self.user)

        response = self.client.get(TASKS_URL, {"state": "open"})
        ids = [r["id"] for r in response.data["results"]]
        assert str(open_task.id) in ids
        for r in response.data["results"]:
            assert r["state"] == "open"


@pytest.mark.django_db
class TestTaskRetrieve:
    """Tests for GET /tasks/{id}/."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        """Set up API client, authenticated user, and default account."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="owner", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Acme",
            status=AccountStatus.PROSPECT,
            type=AccountType.CUSTOMER,
            owner_user=self.user,
        )

    def test_retrieve_returns_200(self):
        """GET /tasks/{id}/ returns HTTP 200 OK."""
        task = TaskService.create_task(
            {"title": "Fetch me", "account": self.account}, self.user
        )
        response = self.client.get(task_url(task.id))
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_returns_correct_task(self):
        """GET /tasks/{id}/ returns the expected id and title."""
        task = TaskService.create_task(
            {"title": "Specific task", "account": self.account}, self.user
        )
        response = self.client.get(task_url(task.id))
        assert response.data["id"] == str(task.id)
        assert response.data["title"] == "Specific task"

    def test_retrieve_nonexistent_returns_404(self):
        """GET /tasks/{id}/ with unknown id returns HTTP 404."""
        response = self.client.get(task_url(uuid.uuid4()))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_includes_is_overdue(self):
        """GET /tasks/{id}/ response includes the is_overdue field."""
        task = TaskService.create_task(
            {"title": "Check overdue", "account": self.account}, self.user
        )
        response = self.client.get(task_url(task.id))
        assert "is_overdue" in response.data


@pytest.mark.django_db
class TestTaskUpdate:
    """Tests for PUT/PATCH /tasks/{id}/."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        """Set up API client, authenticated user, and default account."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="owner", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Acme",
            status=AccountStatus.PROSPECT,
            type=AccountType.CUSTOMER,
            owner_user=self.user,
        )

    def test_patch_updates_priority(self):
        """PATCH /tasks/{id}/ updates the priority field."""
        task = TaskService.create_task(
            {"title": "Task", "account": self.account, "priority": "low"}, self.user
        )
        response = self.client.patch(
            task_url(task.id), {"priority": "high"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["priority"] == "high"

    def test_patch_updates_title(self):
        """PATCH /tasks/{id}/ updates the task title."""
        task = TaskService.create_task(
            {"title": "Old title", "account": self.account}, self.user
        )
        response = self.client.patch(
            task_url(task.id), {"title": "New title"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "New title"

    def test_non_owner_cannot_patch(self):
        """PATCH /tasks/{id}/ by non-owner returns HTTP 403."""
        other_user = UserModel.objects.create_user(username="other", password="pass")
        task = TaskService.create_task(
            {"title": "Owner's task", "account": self.account}, self.user
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(
            task_url(task.id), {"priority": "high"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskSoftDelete:
    """Tests for DELETE /tasks/{id}/."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        """Set up API client, authenticated user, and default account."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="owner", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Acme",
            status=AccountStatus.PROSPECT,
            type=AccountType.CUSTOMER,
            owner_user=self.user,
        )

    def test_delete_returns_204(self):
        """DELETE /tasks/{id}/ returns HTTP 204 No Content."""
        task = TaskService.create_task(
            {"title": "Delete me", "account": self.account}, self.user
        )
        response = self.client.delete(task_url(task.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_soft_deletes_activity(self):
        """DELETE /tasks/{id}/ sets activity.is_invalid = True."""
        task = TaskService.create_task(
            {"title": "Soft delete me", "account": self.account}, self.user
        )
        self.client.delete(task_url(task.id))
        task.activity.refresh_from_db()
        assert task.activity.is_invalid is True

    def test_deleted_task_not_in_list(self):
        """Soft-deleted task is excluded from GET /tasks/."""
        task = TaskService.create_task(
            {"title": "Gone", "account": self.account}, self.user
        )
        self.client.delete(task_url(task.id))
        response = self.client.get(TASKS_URL)
        ids = [r["id"] for r in response.data["results"]]
        assert str(task.id) not in ids

    def test_non_owner_cannot_delete(self):
        """DELETE /tasks/{id}/ by non-owner returns HTTP 403."""
        other_user = UserModel.objects.create_user(username="other2", password="pass")
        task = TaskService.create_task(
            {"title": "Protected", "account": self.account}, self.user
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(task_url(task.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskComplete:
    """Tests for POST /tasks/{id}/complete/."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        """Set up API client, authenticated user, and default account."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="owner", password="pass", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Acme",
            status=AccountStatus.PROSPECT,
            type=AccountType.CUSTOMER,
            owner_user=self.user,
        )

    def test_complete_returns_200(self):
        """POST /tasks/{id}/complete/ returns HTTP 200 OK."""
        task = TaskService.create_task(
            {"title": "Do it", "account": self.account}, self.user
        )
        response = self.client.post(complete_url(task.id))
        assert response.status_code == status.HTTP_200_OK

    def test_complete_sets_task_status_completed(self):
        """POST /tasks/{id}/complete/ sets task state to 'completed'."""
        task = TaskService.create_task(
            {"title": "Finish me", "account": self.account}, self.user
        )
        response = self.client.post(complete_url(task.id))
        assert response.data["state"] == TaskState.COMPLETED

    def test_complete_sets_activity_status_completed(self):
        """POST /tasks/{id}/complete/ sets activity_status to 'completed'."""
        task = TaskService.create_task(
            {"title": "Finish me", "account": self.account}, self.user
        )
        response = self.client.post(complete_url(task.id))
        assert response.data["activity_status"] == ActivityStatus.COMPLETED

    def test_complete_sets_is_overdue_false(self):
        """POST /tasks/{id}/complete/ on overdue task sets is_overdue to False."""
        past = timezone.now() - timedelta(days=1)
        task = TaskService.create_task(
            {"title": "Late", "account": self.account, "due_at": past}, self.user
        )
        response = self.client.post(complete_url(task.id))
        assert response.data["is_overdue"] is False

import uuid

from django.db import models
from django.utils import timezone

from core.models.activity import Activity


class TaskPriority(models.TextChoices):
    """Priority choices for Task."""

    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class TaskCategory(models.TextChoices):
    """Category choices for Task."""

    FOLLOW_UP = "follow_up", "Follow Up"
    ADMIN = "admin", "Admin"
    CUSTOMER = "customer", "Customer"


class TaskState(models.TextChoices):
    """Completion state choices for Task."""

    OPEN = "open", "Open"
    COMPLETED = "completed", "Completed"


class Task(models.Model):
    """
    Task entity represents an actionable to-do item in the CRM.

    Extends Activity via OneToOneField composition. Creating a Task requires
    a parent Activity with type='task'. Soft deletion propagates by setting
    activity.is_invalid=True rather than removing the Task row.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.OneToOneField(
        Activity,
        on_delete=models.CASCADE,
        related_name="task_detail",
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        blank=True,
        null=True,
    )
    category = models.CharField(
        max_length=20,
        choices=TaskCategory.choices,
        blank=True,
        null=True,
    )
    estimated_duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    state = models.CharField(
        max_length=20,
        choices=TaskState.choices,
        default=TaskState.OPEN,
    )

    class Meta:
        ordering = ["-activity__created_at"]

    @property
    def is_overdue(self) -> bool:
        """True if the task is still open and its due date has passed."""
        if self.state != TaskState.OPEN:
            return False
        due_at = self.activity.due_at
        if due_at is None:
            return False
        return due_at < timezone.now()

    def __str__(self) -> str:
        return str(self.activity.title)

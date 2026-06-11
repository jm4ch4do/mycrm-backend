"""Action model stub for workflow step orchestration.

This is a placeholder for KAN-22. The real implementation will expand this
to include action types, parameters, and execution logic.
"""

import uuid

from django.db import models


class Action(models.Model):
    """Atomic operation that a Workflow step executes."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        pass

    def __str__(self) -> str:
        return self.name

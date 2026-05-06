"""API schema examples for Activity endpoints."""

from drf_spectacular.utils import OpenApiExample

CREATE_ACTIVITY_EXAMPLES = [
    OpenApiExample(
        "minimal",
        value={
            "type": "task",
            "title": "Follow up with Acme Corp",
            "account": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
        description="Minimal payload with required fields",
    ),
    OpenApiExample(
        "complete",
        value={
            "type": "call",
            "title": "Discovery call",
            "description": "Initial discovery call to understand needs",
            "account": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "contact": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
            "deal": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
            "status": "planned",
            "due_at": "2026-06-01T10:00:00Z",
        },
        description="Complete payload with all fields",
    ),
]

UPDATE_ACTIVITY_EXAMPLES = [
    OpenApiExample(
        "update",
        value={
            "title": "Updated title",
            "status": "in_progress",
        },
        description="Update specific fields",
    ),
]

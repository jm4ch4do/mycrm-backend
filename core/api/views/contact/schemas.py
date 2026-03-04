"""API schema examples for Contact endpoints."""

from drf_spectacular.utils import OpenApiExample


CREATE_CONTACT_EXAMPLES = [
    OpenApiExample(
        "minimal",
        value={
            "first_name": "John",
            "account": "123e4567-e89b-12d3-a456-426614174000",
        },
        description="Minimal payload with required fields",
    ),
    OpenApiExample(
        "complete",
        value={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "phone": "+1-555-0100",
            "mobile": "+1-555-0101",
            "job_title": "VP of Sales",
            "department": "Sales",
            "role": "decision_maker",
            "seniority": "executive",
            "account": "123e4567-e89b-12d3-a456-426614174000",
            "primary_contact": True,
            "preferred_channel": "email",
            "opt_in_email": True,
            "opt_in_sms": False,
        },
        description="Complete payload with all fields",
    ),
]

UPDATE_CONTACT_EXAMPLES = [
    OpenApiExample(
        "update",
        value={
            "job_title": "SVP of Sales",
            "seniority": "executive",
            "primary_contact": True,
        },
        description="Update specific fields",
    ),
]

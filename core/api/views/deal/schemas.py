"""API schema examples for Deal endpoints."""

from drf_spectacular.utils import OpenApiExample


CREATE_DEAL_EXAMPLES = [
    OpenApiExample(
        "minimal",
        value={
            "name": "Enterprise License Deal",
            "account": "uuid-of-account",
        },
        description="Minimal payload with required fields",
    ),
    OpenApiExample(
        "complete",
        value={
            "name": "Enterprise License Deal",
            "account": "uuid-of-account",
            "amount": "50000.00",
            "currency": "usd",
            "expected_close_date": "2026-06-30",
            "probability": 75,
            "stage": "proposal",
            "status": "open",
            "lead_source": "inbound",
        },
        description="Complete payload with all fields",
    ),
]

UPDATE_DEAL_EXAMPLES = [
    OpenApiExample(
        "update",
        value={
            "name": "Updated Deal Name",
            "stage": "negotiation",
            "amount": "75000.00",
        },
        description="Update specific fields",
    ),
]

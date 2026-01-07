"""API schema examples for Account endpoints."""
from drf_spectacular.utils import OpenApiExample


CREATE_ACCOUNT_EXAMPLES = [
    OpenApiExample(
        'minimal',
        value={
            'name': 'Acme Corporation',
            'status': 'prospect',
            'type': 'customer',
        },
        description='Minimal payload with required fields'
    ),
    OpenApiExample(
        'complete',
        value={
            'name': 'Acme Corporation',
            'account_number': 'ACC-001',
            'status': 'prospect',
            'type': 'customer',
            'industry': 'Technology',
            'company_size': '200+',
            'annual_revenue': '5000000.00',
            'website': 'https://acme.com',
        },
        description='Complete payload with all fields'
    ),
]

UPDATE_ACCOUNT_EXAMPLES = [
    OpenApiExample(
        'update',
        value={
            'name': 'Updated Name',
            'status': 'active',
            'annual_revenue': '7500000.00',
        },
        description='Update specific fields'
    ),
]

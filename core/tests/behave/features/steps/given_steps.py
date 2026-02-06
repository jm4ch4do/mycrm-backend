"""
Given steps for creating entities through the API.
"""

import json
from behave import given
from django.contrib.auth import get_user_model

User = get_user_model()


@given("I create accounts through the API")
def step_create_accounts(context):
    """Create accounts through the Django test client."""
    if not hasattr(context, "created_accounts"):
        context.created_accounts = []

    for row in context.table:
        # Use owner_username if specified, otherwise use default test_user
        if "owner_username" in row.headings:
            username = row["owner_username"]
            if username not in context.users:
                # Create a new user for this specific scenario
                # No password needed since we use force_login
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password=None,  # Sets unusable password
                    is_staff=True,
                )
                context.users[username] = user
            else:
                user = context.users[username]
        else:
            # Use the default test_user from environment
            user = context.test_user

        # Create account
        account_data = {
            "name": row["name"],
            "status": row["status"],
            "type": row["type"],
        }

        # Add optional fields if present
        if "industry" in row.headings:
            account_data["industry"] = row.get("industry", "")
        if "website" in row.headings:
            account_data["website"] = row.get("website", "")

        # Authenticate as the owner user
        context.client.force_login(user)

        response = context.client.post(
            "/accounts/",
            data=json.dumps(account_data),
            content_type="application/json",
        )

        assert (
            response.status_code == 201
        ), f"Failed to create account: {response.content}"
        context.created_accounts.append(response.json())

    context.response = response

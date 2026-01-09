"""
Behave environment configuration for Django integration.

This file sets up the Django test environment for behave BDD tests.
"""

# Initialize Django before importing models
import setup  # pylint: disable=unused-import

from django.apps import apps
from django.contrib.auth import get_user_model


def clear_test_data():
    """
    Clear all test data before each scenario except preserved models.
    Add models that should NOT be cleared to "preserved".
    Everything else will be automatically cleared.
    """
    to_preserve = [
        "Group",
        "Permission",
        "ContentType",
        "LogEntry",
        "Session",
        "MigrationRecorder",
    ]

    # Get all models from all apps
    all_models = apps.get_models()

    for model in all_models:
        model_name = model.__name__
        if model_name not in to_preserve and model_name != "User":
            model.objects.all().delete()

    # Second pass: Now clear Users after all dependent objects are deleted
    user_model = get_user_model()
    user_model.objects.all().delete()


def before_scenario(context, scenario):
    """
    Set up before each scenario.
    Called before each scenario is run.
    """
    clear_test_data()


def after_scenario(context, scenario):
    """
    Clean up after each scenario.
    Called after each scenario is run.
    """

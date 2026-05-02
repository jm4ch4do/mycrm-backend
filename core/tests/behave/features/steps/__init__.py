"""
Step definitions package.

Behave only scans *.py files directly inside this directory, not subdirectories.
Domain step modules that live in steps/domain/ are imported below so their
@given/@when/@then decorators get registered with Behave on startup.
"""

from steps.domain import contact_steps, user_steps  # noqa: F401

"""
Step definitions package.

Behave only scans *.py files directly inside this directory, not subdirectories.
Domain step modules that live in steps/domain/ are imported below so their
@given/@when/@then decorators get registered with Behave on startup.
"""

import steps.domain.action_steps  # noqa: F401
import steps.domain.contact_steps  # noqa: F401
import steps.domain.execution_log_steps  # noqa: F401
import steps.domain.timeline_steps  # noqa: F401
import steps.domain.user_steps  # noqa: F401
import steps.domain.workflow_steps  # noqa: F401

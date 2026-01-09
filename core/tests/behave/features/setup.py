"""
Django setup for behave tests.
"""

import os
import django

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mycrm.settings")
django.setup()

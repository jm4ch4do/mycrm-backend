"""Pagination configuration for Trigger API."""

from rest_framework.pagination import PageNumberPagination


class TriggerPagination(PageNumberPagination):
    """Pagination class for Trigger list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

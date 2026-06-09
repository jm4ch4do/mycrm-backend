"""Pagination configuration for Event API."""

from rest_framework.pagination import PageNumberPagination


class EventPagination(PageNumberPagination):
    """Pagination class for Event list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

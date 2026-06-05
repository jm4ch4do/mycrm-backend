"""Pagination configuration for Timeline API."""

from rest_framework.pagination import PageNumberPagination


class TimelinePagination(PageNumberPagination):
    """Pagination class for Timeline list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

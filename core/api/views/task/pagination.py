"""Pagination configuration for Task API."""

from rest_framework.pagination import PageNumberPagination


class TaskPagination(PageNumberPagination):
    """Pagination class for Task list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

"""Pagination configuration for ExecutionLog API."""

from rest_framework.pagination import PageNumberPagination


class ExecutionLogPagination(PageNumberPagination):
    """Pagination class for execution log list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
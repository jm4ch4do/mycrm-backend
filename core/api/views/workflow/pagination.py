"""Pagination configuration for Workflow API."""

from rest_framework.pagination import PageNumberPagination


class WorkflowPagination(PageNumberPagination):
    """Pagination class for Workflow list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

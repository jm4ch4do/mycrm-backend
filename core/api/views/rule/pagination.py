"""Pagination configuration for Rule API."""

from rest_framework.pagination import PageNumberPagination


class RulePagination(PageNumberPagination):
    """Pagination class for Rule list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

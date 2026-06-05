"""Pagination configuration for Call API."""

from rest_framework.pagination import PageNumberPagination


class CallPagination(PageNumberPagination):
    """Pagination class for Call list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

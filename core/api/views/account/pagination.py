"""Pagination configuration for Account API."""
from rest_framework.pagination import PageNumberPagination


class AccountPagination(PageNumberPagination):
    """Pagination class for Account list views."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

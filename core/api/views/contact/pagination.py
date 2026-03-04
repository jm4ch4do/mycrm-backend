"""Pagination configuration for Contact API."""

from rest_framework.pagination import PageNumberPagination


class ContactPagination(PageNumberPagination):
    """Pagination class for Contact list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

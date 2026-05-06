"""Pagination configuration for Activity API."""

from rest_framework.pagination import PageNumberPagination


class ActivityPagination(PageNumberPagination):
    """Pagination class for Activity list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

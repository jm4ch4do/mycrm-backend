"""Pagination configuration for Meeting API."""

from rest_framework.pagination import PageNumberPagination


class MeetingPagination(PageNumberPagination):
    """Pagination class for Meeting list views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

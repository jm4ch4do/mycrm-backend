"""
HTTP Request Timing Middleware for performance monitoring.

Captures request start time and measures the elapsed time for each request,
logging the HTTP method, path, status code, and execution time.
"""

import logging
import time

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    """
    Middleware to measure and log HTTP request processing time.

    This middleware intercepts all requests and responses, capturing the start
    time on each request and calculating the elapsed time when responding.
    Logs are formatted as:
    METHOD PATH - Status: CODE - Time: XXXms
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request and response.

        Args:
            request: The incoming HTTP request

        Returns:
            The HTTP response
        """
        # Capture start time at the beginning of request processing
        request.start_time = time.time()

        # Call the next middleware/view
        response = self.get_response(request)

        # Calculate elapsed time
        try:
            elapsed_time = time.time() - request.start_time
            elapsed_ms = elapsed_time * 1000  # Convert to milliseconds

            # Log timing information using lazy % formatting
            logger.info(
                "%s %s - Status: %s - Time: %.0fms",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
            )
        except AttributeError:
            # Handle case where start_time was not set (shouldn't happen in normal flow)
            logger.warning(
                "%s %s - Status: %s - Time: Unable to calculate",
                request.method,
                request.path,
                response.status_code,
            )

        return response

"""Tests for request timing middleware."""

import logging
import time

from django.test import TestCase, RequestFactory
from django.http import HttpResponse

from core.middleware import RequestTimingMiddleware


class RequestTimingMiddlewareTests(TestCase):
    """Test RequestTimingMiddleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = RequestTimingMiddleware(self.get_response)
        self.logger = logging.getLogger("core.middleware")

    def get_response(self, request):
        """Mock get_response callable."""
        return HttpResponse(status=200)

    def test_middleware_captures_start_time(self):
        """Test that middleware captures start time on request."""
        request = self.factory.get("/api/accounts")

        # Verify start_time is set after middleware processes request
        self.middleware(request)
        self.assertTrue(hasattr(request, "start_time"))
        self.assertIsInstance(request.start_time, float)

    def test_middleware_logs_request_timing(self):
        """Test that middleware logs request timing information."""
        request = self.factory.get("/api/accounts")

        with self.assertLogs("core.middleware", level=logging.INFO) as cm:
            self.middleware(request)

        # Verify log message contains expected format
        log_message = cm.output[0]
        self.assertIn("GET", log_message)
        self.assertIn("/api/accounts", log_message)
        self.assertIn("Status: 200", log_message)
        self.assertIn("Time:", log_message)
        self.assertIn("ms", log_message)

    def test_middleware_logs_post_request(self):
        """Test that middleware logs POST requests."""
        request = self.factory.post("/api/accounts")

        with self.assertLogs("core.middleware", level=logging.INFO) as cm:
            self.middleware(request)

        log_message = cm.output[0]
        self.assertIn("POST", log_message)
        self.assertIn("/api/accounts", log_message)

    def test_middleware_logs_status_code(self):
        """Test that middleware logs correct status code."""

        def get_response_with_status(request):
            return HttpResponse(status=201)

        middleware = RequestTimingMiddleware(get_response_with_status)
        request = self.factory.post("/api/accounts")

        with self.assertLogs("core.middleware", level=logging.INFO) as cm:
            middleware(request)

        log_message = cm.output[0]
        self.assertIn("Status: 201", log_message)

    def test_middleware_calculates_elapsed_time(self):
        """Test that middleware calculates elapsed time correctly."""

        def slow_response(request):
            # Simulate slow request
            time.sleep(0.05)  # 50ms
            return HttpResponse(status=200)

        middleware = RequestTimingMiddleware(slow_response)
        request = self.factory.get("/api/accounts")

        with self.assertLogs("core.middleware", level=logging.INFO) as cm:
            middleware(request)

        log_message = cm.output[0]
        # Verify that elapsed time is logged and is at least 50ms
        self.assertIn("Time:", log_message)
        # Extract the time value (format: "Time: XXms")
        time_str = log_message.split("Time: ")[1].split("ms")[0]
        elapsed_ms = float(time_str)
        self.assertGreaterEqual(elapsed_ms, 50)

    def test_middleware_handles_different_paths(self):
        """Test that middleware logs different paths correctly."""
        paths = [
            "/api/accounts",
            "/api/accounts/123",
            "/api/accounts/123/contacts",
        ]

        for path in paths:
            request = self.factory.get(path)

            with self.assertLogs("core.middleware", level=logging.INFO) as cm:
                self.middleware(request)

            log_message = cm.output[0]
            self.assertIn(path, log_message)

    def test_middleware_handles_different_methods(self):
        """Test that middleware logs different HTTP methods."""
        methods = [
            ("GET", self.factory.get),
            ("POST", self.factory.post),
            ("PUT", self.factory.put),
            ("DELETE", self.factory.delete),
            ("PATCH", self.factory.patch),
        ]

        for method, factory_method in methods:
            request = factory_method("/api/accounts")

            with self.assertLogs("core.middleware", level=logging.INFO) as cm:
                self.middleware(request)

            log_message = cm.output[0]
            self.assertIn(method, log_message)

    def test_middleware_handles_error_status_codes(self):
        """Test that middleware logs error status codes."""

        def error_response(request):
            return HttpResponse(status=404)

        middleware = RequestTimingMiddleware(error_response)
        request = self.factory.get("/api/accounts/nonexistent")

        with self.assertLogs("core.middleware", level=logging.INFO) as cm:
            middleware(request)

        log_message = cm.output[0]
        self.assertIn("Status: 404", log_message)

    def test_middleware_returns_response(self):
        """Test that middleware returns the response from get_response."""

        def test_response(request):
            return HttpResponse("Test content", status=200)

        middleware = RequestTimingMiddleware(test_response)
        request = self.factory.get("/api/accounts")

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Test content")

    def test_middleware_is_transparent(self):
        """Test that middleware doesn't modify request or response."""
        original_method = "GET"
        original_path = "/api/accounts"

        def transparent_response(request):
            # Verify request attributes haven't been modified
            self.assertEqual(request.method, original_method)
            self.assertEqual(request.path, original_path)
            return HttpResponse(status=200)

        middleware = RequestTimingMiddleware(transparent_response)
        request = self.factory.get(original_path)

        response = middleware(request)
        self.assertEqual(response.status_code, 200)

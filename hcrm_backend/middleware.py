# hcrm_backend/middleware.py
from django.http import JsonResponse
import logging

logger = logging.getLogger('django')

class SecurityHeadersMiddleware:
    """Add basic security headers to all responses."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        return response

class SanitizeErrorMiddleware:
    """
    When DEBUG=False, capture uncaught exceptions and return a safe JSON response
    while logging full exception details server-side.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.error("Unhandled exception (caught by middleware): %s", exception, exc_info=True)
        from django.conf import settings
        if not getattr(settings, "DEBUG", False):
            return JsonResponse({'error': 'An error occurred processing your request'}, status=500)
        # if DEBUG True, let default behavior show the stacktrace (useful locally)
        return None

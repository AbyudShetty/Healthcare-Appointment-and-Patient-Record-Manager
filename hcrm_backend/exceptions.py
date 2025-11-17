# hcrm_backend/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF:
      - lets DRF handle known exceptions (ValidationError, NotFound, etc.)
      - logs unexpected exceptions server-side with full traceback
      - returns a safe generic message to clients for unhandled exceptions
    """
    # First, call DRF's default exception handler to get standard error responses.
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # Unhandled exception: log full details for debugging
    logger.error("Unhandled exception in request", exc_info=True)

    # Return safe generic error to client (no stacktrace)
    return Response(
        {
            "error": "An unexpected error occurred. Please try again later."
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

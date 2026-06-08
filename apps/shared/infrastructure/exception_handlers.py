from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

from apps.shared.domain.exceptions import WmsDomainException

logger = logging.getLogger(__name__)

def wms_exception_handler(exc: Exception, context: dict) -> Response:
    """
    Custom exception handler for Django REST Framework views.
    Catches pure WmsDomainExceptions and formats them as standard HTTP 400 JSON responses.
    Allows all other standard Django/DRF exceptions to be handled by the framework.
    """
    # Try getting the default DRF response
    response = exception_handler(exc, context)

    if isinstance(exc, WmsDomainException):
        logger.warning(
            f"Domain Exception triggered: Code={exc.code}, Message='{exc.message}'"
        )
        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Log unexpected server errors
    if response is None:
        logger.exception("An unhandled exception occurred in the API presentation layer.")
        return Response(
            {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please contact support."
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response

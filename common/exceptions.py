from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.status_code
        response.data['success'] = False
    else:
        logger.error(f"Unhandled Exception: {exc}", exc_info=True)
        return Response(
            {
                'success': False,
                'message': 'An internal server error occurred.',
                'status_code': 500
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return response

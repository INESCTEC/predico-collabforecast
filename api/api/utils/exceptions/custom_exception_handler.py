import structlog

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response


# init logger:
logger = structlog.get_logger("api_error500_logger")


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is None:
        error_message = "An unexpected error occurred. " \
                        "If the problem persists please " \
                        "contact the developers."
        logger.exception(event="request_error", error_code="unexpected",
                         error_detail=error_message)
        return Response(data={"detail": error_message},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.error(event="request_error",
                     error_code=exc.default_code,
                     error_detail=exc.default_detail)
        return response

import structlog

from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import ErrorDetail

# init logger:
logger = structlog.get_logger(__name__)

def error_detail_to_dict(error_detail):
    if isinstance(error_detail, ErrorDetail):
        return {error_detail.code: str(error_detail)}
    elif isinstance(error_detail, list):
        return [error_detail_to_dict(item) for item in error_detail]
    elif isinstance(error_detail, dict):
        return {key: error_detail_to_dict(value) for key, value in error_detail.items()}
    return error_detail


class CustomRenderer(JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        :param data:
        :param accepted_media_type:
        :param renderer_context:
        :return:
        """
        status_code = renderer_context['response'].status_code
        response = {
            "code": status_code,
            "data": data,
        }

        if not str(status_code).startswith('2'):
            response["status"] = "error"
            response["data"] = None

            try:
                response["message"] = data["detail"]
            except KeyError:
                response["data"] = data
            except TypeError:
                response["data"] = data

        if status_code == 400:
            response["message"] = "Validation error. Please re-check " \
                                  "your request parameters or body fields " \
                                  "and fix the errors mentioned in this " \
                                  "response 'data' field."
            logger.warning(event="request_error",
                           error_code="validation_error",
                           error_detail=error_detail_to_dict(response["data"]))

        return super().render(response, accepted_media_type, renderer_context)

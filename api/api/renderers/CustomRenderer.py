import structlog

from rest_framework.renderers import JSONRenderer


# init logger:
logger = structlog.get_logger("api_logger")


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

        return super().render(response, accepted_media_type, renderer_context)

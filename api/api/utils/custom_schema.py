from django.conf import settings

from drf_yasg.utils import swagger_auto_schema


def conditional_swagger_auto_schema(*args, **kwargs):
    """
    Apply swagger_auto_schema only if ENABLE_SWAGGER_DECORATORS is True.
    """
    def decorator(view_func):
        # Apply swagger_auto_schema if the flag is enabled
        if not settings.DISABLE_ADMIN_SCHEMAS:
            return swagger_auto_schema(*args, **kwargs)(view_func)
        else:
            return swagger_auto_schema(auto_schema=None, *args, **kwargs)(view_func)
    return decorator
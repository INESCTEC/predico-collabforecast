from drf_yasg import openapi


def create_schema(type=None, format=None, description=None, enum=None):
    """
    Generic schema creator for the Swagger/Redoc documentation.
    """
    return openapi.Schema(
        type=type,
        format=format,
        description=description,
        enum=enum,
    )

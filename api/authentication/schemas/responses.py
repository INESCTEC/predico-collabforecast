from drf_yasg import openapi
from .util import create_schema


###############################
# UserResourcesView
###############################
PostLogin = \
    openapi.Response(
        description="Success",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "access": create_schema(
                    type=openapi.TYPE_STRING,
                    description="JWT access token"
                ),
                "refresh": create_schema(
                    type=openapi.TYPE_STRING,
                    description="JWT refresh token"
                ),
            },
        ),
        examples={
            "application/json": {
                "access": "jwt_access_token",
                "refresh": "jwt_refresh_token"
            },
        }
    )


LoginResponse = {
    "POST": PostLogin,
}


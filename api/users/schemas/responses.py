from drf_yasg import openapi
from .util import create_schema


# Response for when a valid token is needed and not given in the request
NotAuthenticatedResponse = openapi.Response(
    description="Unauthorized",
    schema=openapi.Schema(
        title="Not Authenticated schema",
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[401],
                description="Response status code.",
            ),
            "data": create_schema(
                type=openapi.TYPE_OBJECT,
                description="Null field in case of error response.",
            ),
            "status": create_schema(
                type=openapi.TYPE_STRING,
                enum=["error"],
                description="Response status info.",
            ),
            "message": create_schema(
                type=openapi.TYPE_STRING,
                enum=["Authentication credentials were not provided."],
                description="Error message.",
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 401,
            "data": None,
            "status": "error",
            "message": "Given token not valid for any token type",
        },
    },
)

ForbiddenAccessResponse = openapi.Response(
    description="Forbidden",
    schema=openapi.Schema(
        title="Forbidden access schema",
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[403],
                description="Response status code.",
            ),
            "data": create_schema(
                type=openapi.TYPE_OBJECT,
                description="Null field in case of error response.",
            ),
            "status": create_schema(
                type=openapi.TYPE_STRING,
                enum=["error"],
                description="Response status info.",
            ),
            "message": create_schema(
                type=openapi.TYPE_STRING,
                enum=["You do not have permission to perform this action."],
                description="Error message.",
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 403,
            "data": None,
            "status": "error",
            "message": "You do not have permission to perform this action.",
        },
    },
)


###############################
# UserResourcesView
###############################
GetUserResourcesResponse = openapi.Response(
    description="Success",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[200],
                description="Response status code.",
            ),
            "data": create_schema(
                type=openapi.TYPE_OBJECT, description="Response data."
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 200,
            "data": [
                {
                    "id": "ba7203df-0618-4001-a2e9-b0a11cc477f9",
                    "name": "wind_farm_x",
                    "timezone": "Europe/Brussels",
                    "registered_at": "2024-09-18T15:16:29.749186Z",
                    "updated_at": "2024-09-18T15:16:29.749213Z",
                    "user": "9fa9849e-35b0-4151-a6de-f1e3757f790e",
                }
            ],
        },
    },
)


UserResourcesResponse = {
    "GET": GetUserResourcesResponse,
}

###############################
# UserListView
###############################
GetUserListResponse = openapi.Response(
    description="Success",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[200],
                description="Response status code.",
            ),
            "data": create_schema(
                type=openapi.TYPE_OBJECT, description="Response data."
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 200,
            "data": [
                {
                    "id": "f8b7a790-6fa3-4d71-89fc-9ddbf927fb36",
                    "last_login": "2024-09-20T08:21:57.913244Z",
                    "is_superuser": False,
                    "first_name": "User",
                    "last_name": "Name",
                    "is_active": True,
                    "date_joined": "2024-09-20T07:55:59.835111Z",
                    "email": "user@email.com",
                    "is_verified": True,
                }
            ],
        },
    },
)


UserListResponse = {
    "GET": GetUserListResponse,
}


###############################
# UserRegisterView
###############################
PostUserRegisterResponse = openapi.Response(
    description="Success",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[201],
                description="Response status code.",
            ),
            "data": create_schema(
                type=openapi.TYPE_OBJECT, description="Response data."
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 201,
            "data": {"email": "user@email.com"},
        },
    },
)

PostUserRegisterResponseConflict = openapi.Response(
    description="Success",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[409],
                description="Response status code.",
            ),
            "data": create_schema(
                type=openapi.TYPE_OBJECT, description="Response data."
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 409,
            "data": None,
            "status": "error",
            "message": "The email 'user@email.com' already exists!",
        },
    },
)


UserRegisterResponse = {
    "POST": PostUserRegisterResponse,
    "POST_conflict": PostUserRegisterResponseConflict,
}

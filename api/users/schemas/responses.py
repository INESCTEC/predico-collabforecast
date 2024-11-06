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
                    "id": "c02f6644-2e65-4931-8a86-fa694b481a4a",
                    "name": "wind_farm_elia",
                    "timezone": "Europe/Brussels",
                    "registered_at": "2024-11-03T23:35:43.285606Z",
                    "updated_at": "2024-11-03T23:35:43.285624Z",
                    "user": "04103cca-6079-4c93-83f0-ef90bffb3a73",
                    "measurements_metadata": {
                        "n_samples": 5565,
                        "start_datetime": "2024-09-02T23:45:00Z",
                        "end_datetime": "2024-10-30T22:45:00Z",
                        "last_update_datetime": "2024-11-03T23:39:55.285225Z"
                    }
                }
            ]
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

from drf_yasg import openapi
from .util import create_schema


# Response for when a valid token is needed and not given in the request
NotAuthenticatedResponse = \
    openapi.Response(
        description="Unauthorized",
        schema=openapi.Schema(
            title="Not Authenticated schema",
            type=openapi.TYPE_OBJECT,
            properties={
                "code": create_schema(
                    type=openapi.TYPE_INTEGER,
                    enum=[401],
                    description="Response status code."
                ),
                "data": create_schema(
                    type=openapi.TYPE_OBJECT,
                    description="Null field in case of error response."
                ),
                "status": create_schema(
                    type=openapi.TYPE_STRING,
                    enum=["error"],
                    description="Response status info."
                ),
                "message": create_schema(
                    type=openapi.TYPE_STRING,
                    enum=["Authentication credentials were not provided."],
                    description="Error message."
                ),
            },
        ),
        examples={
            "application/json": {
                "code": 401,
                "data": None,
                "status": "error",
                "message": "Given token not valid for any token type"
            },
        }
    )

ForbiddenAccessResponse = \
    openapi.Response(
        description="Forbidden",
        schema=openapi.Schema(
            title="Forbidden access schema",
            type=openapi.TYPE_OBJECT,
            properties={
                "code": create_schema(
                    type=openapi.TYPE_INTEGER,
                    enum=[403],
                    description="Response status code."
                ),
                "data": create_schema(
                    type=openapi.TYPE_OBJECT,
                    description="Null field in case of error response."
                ),
                "status": create_schema(
                    type=openapi.TYPE_STRING,
                    enum=["error"],
                    description="Response status info."
                ),
                "message": create_schema(
                    type=openapi.TYPE_STRING,
                    enum=["You do not have permission to perform this action."],  # noqa
                    description="Error message."
                ),
            },
        ),
        examples={
            "application/json": {
                "code": 403,
                "data": None,
                "status": "error",
                "message": "You do not have permission to perform this action."
            },
        }
    )


ConflictResponse = openapi.Response(
    description="Conflict",
    schema=openapi.Schema(
        title="Conflict schema",
        type=openapi.TYPE_OBJECT,
        properties={
            "code": create_schema(
                type=openapi.TYPE_INTEGER,
                enum=[409],
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
                enum=["Self-explanatory message about the problem."],
                description="Error message.",
            ),
        },
    ),
    examples={
        "application/json": {
            "code": 409,
            "data": None,
            "status": "error",
            "message": "Self-explanatory message about the problem.",
        },
    },
)

###############################
# RawDataView
###############################
GetRawDataResponse = \
    openapi.Response(
        description="Success",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": create_schema(
                    type=openapi.TYPE_INTEGER,
                    enum=[200],
                    description="Response status code."
                ),
                "data": create_schema(
                    type=openapi.TYPE_OBJECT,
                    description="Response data."
                ),
            },
        ),
        examples={
            "application/json": {
                "code": 200,
                "data": {
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "datetime": "2024-05-20T09:15:00Z",
                            "value": 0.182,
                            "units": "mw",
                            "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
                            "registered_at": "2024-06-24T09:19:19.428512Z",
                            "resource_name": "wind_farm_1"
                        },
                        {
                            "datetime": "2024-05-20T09:30:00Z",
                            "value": 0.772,
                            "units": "mw",
                            "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
                            "registered_at": "2024-06-24T09:19:19.428512Z",
                            "resource_name": "wind_farm_1"
                        }
                    ]
                }
            },
        }
    )


RawDataResponse = {
    "GET": GetRawDataResponse,
}


###############################
# MarketForecastsView
###############################
GetMarketForecastsResponse = \
    openapi.Response(
        description="Success",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": create_schema(
                    type=openapi.TYPE_INTEGER,
                    enum=[200],
                    description="Response status code."
                ),
                "data": create_schema(
                    type=openapi.TYPE_OBJECT,
                    description="Response data."
                ),
            },
        ),
        examples={
            "application/json": {
                "code": 200,
                "data": [
                    {
                        "market_session": 1,
                        "datetime": "2022-10-01T10:00:00Z",
                        "request": "2022-10-01T00:34:58Z",
                        "value": 0.9661258461978153,
                        "units": "kw",
                        "resource": 1,
                        "registered_at": "2022-10-01T11:34:58.131623Z",
                        "resource_name": "park-1"
                    }
                ]
            },
        }
    )


MarketForecastsResponse = {
    "GET": GetMarketForecastsResponse,
}

###############################
# IndividualForecasters
###############################
GetIndividualForecastsResponse = \
    openapi.Response(
        description="Success",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": create_schema(
                    type=openapi.TYPE_INTEGER,
                    enum=[200],
                    description="Response status code."
                ),
                "data": create_schema(
                    type=openapi.TYPE_OBJECT,
                    description="Response data."
                ),
            },
        ),
        examples={
            "application/json": {
                "code": 200,
                "data": {
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "datetime": "2024-06-20T22:00:00Z",
                            "variable": "q10",
                            "value": 0.806,
                            "market_session": 1,
                            "challenge": "c206ff25-1ef0-4f31-9beb-d6626bddb5f6",
                            "registered_at": "2024-06-20T13:19:46.838347Z"
                        },
                        {
                            "datetime": "2024-06-20T22:00:00Z",
                            "variable": "q90",
                            "value": 0.806,
                            "market_session": 1,
                            "challenge": "c206ff25-1ef0-4f31-9beb-d6626bddb5f6",
                            "registered_at": "2024-06-20T13:19:48.490980Z"
                        }
                    ]
                }
            },
        }
    )


IndividualForecastsResponse = {
    "GET": GetIndividualForecastsResponse,
}


###############################
# HistoricalIndividualForecasters
###############################
GetHistoricalIndividualForecastsResponse = \
    openapi.Response(
        description="Success",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": create_schema(
                    type=openapi.TYPE_INTEGER,
                    enum=[200],
                    description="Response status code."
                ),
                "data": create_schema(
                    type=openapi.TYPE_OBJECT,
                    description="Response data."
                ),
            },
        ),
        examples={
            "application/json": {
                "code": 200,
                "data": {
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "datetime": "2024-06-20T00:00:00Z",
                            "launch_time": "2024-06-24T09:00:00Z",
                            "variable": "q90",
                            "value": 0.101,
                            "registered_at": "2024-06-24T09:00:43.430995Z"
                        },
                        {
                            "datetime": "2024-06-20T00:00:00Z",
                            "launch_time": "2024-06-24T12:15:00Z",
                            "variable": "q10",
                            "value": 0.776,
                            "registered_at": "2024-06-24T12:17:54.804330Z"
                        }
                    ]
                }
            },
        }
    )


HistoricalIndividualForecastsResponse = {
    "GET": GetHistoricalIndividualForecastsResponse,
}

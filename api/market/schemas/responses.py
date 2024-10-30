# ruff: noqa

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
# MarketSessionView
###############################
GetMarketSessionResponse = openapi.Response(
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
                    "id": 1,
                    "open_ts": "2024-06-24T09:19:23.251536Z",
                    "close_ts": "2024-06-24T09:38:50.647985Z",
                    "launch_ts": "2024-06-24T09:38:52.732830Z",
                    "finish_ts": "2024-06-24T09:39:24.465670Z",
                    "status": "finished",
                },
                {
                    "id": 2,
                    "open_ts": "2024-06-24T09:39:28.565151Z",
                    "close_ts": "2024-06-24T09:40:17.751655Z",
                    "launch_ts": None,
                    "finish_ts": "2024-06-24T09:51:48.906903Z",
                    "status": "finished",
                },
            ],
        }
    },
)


MarketSessionResponse = {
    "GET": GetMarketSessionResponse,
}


###############################
# MarketSessionChallengeView
###############################
GetMarketSessionChallengeResponse = openapi.Response(
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
                    "id": "ef3a473f-0fcf-4880-8b42-93f6bf732e3a",
                    "use_case": "wind_power_ramp",
                    "start_datetime": "2024-06-24T22:00:00Z",
                    "end_datetime": "2024-06-25T21:45:00Z",
                    "target_day": "2024-06-25",
                    "registered_at": "2024-06-24T09:19:33.990638Z",
                    "updated_at": "2024-06-24T09:19:33.990638Z",
                    "user": "3ca74375-2ac0-46f4-b4bf-7cf013d0c28f",
                    "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
                    "market_session": 1,
                    "resource_name": "wind_farm_x",
                }
            ],
        }
    },
)


MarketSessionChallengeResponse = {
    "GET": GetMarketSessionChallengeResponse,
}


###################################
# MarketSessionListSubmissionView
###################################
GetMarketSessionListSubmissionResponse = openapi.Response(
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
                    "id": "53002afd-8f7d-47be-8e3b-80652a75885c",
                    "market_session_challenge_resource_id": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
                    "variable": "q10",
                    "registered_at": "2024-06-24T15:31:10.681823Z",
                    "market_session_challenge": "313bfbe1-6f2c-4e58-8ac3-09b78e862a58",
                    "user": "9cbc6d35-6010-406b-8549-1de3a94668e8",
                }
            ],
        }
    },
)


MarketSessionListSubmissionResponse = {
    "GET": GetMarketSessionListSubmissionResponse,
}


###########################################
# MarketSessionListSubmissionForecastsView
###########################################
GetMarketSessionListSubmissionForecastsResponse = openapi.Response(
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
                    "submission": "36ddd808-e43c-4ece-9159-e5b1a65f530c",
                    "resource": "ba7203df-0618-4001-a2e9-b0a11cc477f9",
                    "variable": "q50",
                    "datetime": "2024-09-24T22:00:00Z",
                    "registered_at": "2024-09-24T15:35:04.643234Z",
                    "value": 850.4,
                    "user": "6a71b254-8a52-4dd8-a345-32c02af3ebb0",
                },
            ],
        }
    },
)


MarketSessionListSubmissionForecastsResponse = {
    "GET": GetMarketSessionListSubmissionForecastsResponse,
}


######################################
# MarketSessionEnsembleForecastsView
######################################
GetMarketSessionEnsembleForecastsResponse = openapi.Response(
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
                    "challenge": "52c89469-219c-4d0b-aeb9-c7ecbb1ac644",
                    "resource": "ba7203df-0618-4001-a2e9-b0a11cc477f9",
                    "variable": "q10",
                    "datetime": "2024-09-24T22:00:00Z",
                    "registered_at": "2024-09-24T15:40:53.294800Z",
                    "value": 274.993589,
                }
            ],
        }
    },
)


MarketSessionEnsembleForecastsResponse = {
    "GET": GetMarketSessionEnsembleForecastsResponse,
}


######################################
# MarketSessionEnsembleWeightsView
######################################
GetMarketSessionEnsembleWeightsResponse = openapi.Response(
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
                    "challenge": "a3200cce-d169-4fbd-b4a5-fa6b0afa3263",
                    "use_case": "wind_power_ramp",
                    "start_datetime": "2024-06-27T22:00:00Z",
                    "end_datetime": "2024-06-28T21:45:00Z",
                    "resource": "b92c96d1-f5ee-4f96-a4cc-216a92acb10b",
                    "ensemble_data": [
                        {
                            "id": "0ce29243-b8eb-4f3f-8723-aa7204b1de53",
                            "model": "LR",
                            "variable": "q10",
                            "weights": None,
                        },
                        {
                            "id": "fe4431a0-00c1-4598-91f4-58a80a73a7b1",
                            "model": "LR",
                            "variable": "q90",
                            "weights": None,
                        },
                        {
                            "id": "8f8a49e5-dcb3-467a-ac1f-e46a981182ca",
                            "model": "LR",
                            "variable": "q50",
                            "weights": None,
                        },
                    ],
                }
            ],
        }
    },
)


MarketSessionEnsembleWeightsResponse = {
    "GET": GetMarketSessionEnsembleWeightsResponse,
}



######################################
# MarketSessionRampAlertsView
######################################
GetMarketSessionRampAlertsResponse = openapi.Response(
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
                    "variability_quantiles": "q10",
                    "datetime": "2024-09-24T22:00:00Z",
                    "registered_at": "2024-09-24T15:40:53.294800Z",
                }
            ],
        }
    },
)


MarketSessionRampAlertsResponse = {
    "GET": GetMarketSessionRampAlertsResponse,
}
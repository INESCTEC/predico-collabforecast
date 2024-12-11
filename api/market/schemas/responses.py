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
                    "code": 200,
                    "data": [
                        {
                            "ensemble": "80f61367-4033-47fd-9ae8-8ffd638e746c",
                            "variable": "q10",
                            "rank": 1,
                            "total_participants": 3
                        },
                        {
                            "ensemble": "18042e5a-bdca-4f78-b065-1b5963890095",
                            "variable": "q90",
                            "rank": 1,
                            "total_participants": 3
                        },
                        {
                            "ensemble": "1a3fc825-f289-4351-8383-d608b70f3d4c",
                            "variable": "q50",
                            "rank": 1,
                            "total_participants": 3
                        }
                    ]
                }
            ],
        }
    },
)


MarketSessionEnsembleWeightsResponse = {
    "GET": GetMarketSessionEnsembleWeightsResponse,
}


###########################################
# MarketSessionChallengeSolutionView
###########################################
GetMarketSessionChallengeSolutionResponse = openapi.Response(
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
            "data": {
                "challenge": {
                    "id": "d2a77ef7-2179-4493-99fb-19dd35464496",
                    "use_case": "wind_power",
                    "start_datetime": "2024-10-09T22:00:00Z",
                    "end_datetime": "2024-10-10T21:45:00Z",
                    "target_day": "2024-10-10",
                    "registered_at": "2024-10-09T14:00:52.728633Z",
                    "updated_at": "2024-10-09T14:00:52.728651Z",
                    "user": "9fa9849e-35b0-4151-a6de-f1e3757f790e",
                    "resource": "ba7203df-0618-4001-a2e9-b0a11cc477f9",
                    "market_session": 1,
                    "resource_name": "wind_farm_1"
                },
                "solution": [
                    {
                        "datetime": "2024-10-09T22:00:00Z",
                        "value": 1000.05,
                        "units": "mw",
                        "resource": "ba7203df-0618-4001-a2e9-b0a11cc477f9",
                        "registered_at": "2024-10-28T14:00:39.526810Z",
                        "resource_name": "wind_farm_1"
                    }
                ]
            }
        }
    },
)


MarketSessionChallengeSolutionResponse = {
    "GET": GetMarketSessionChallengeSolutionResponse,
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
                    "variability_quantiles": {"q10": 0.05, "q50": 150.3, "q90": 300.5},
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



############################################
# MarketSessionSubmissionScoresRetrieveView
############################################
GetMarketSessionSubmissionScoresRetrieveResponse = openapi.Response(
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
            "data": {
                "personal_metrics": [
                    {
                        "submission": "c83b7fe4-faac-47f8-8eaa-c0a6a1ab0de2",
                        "variable": "q50",
                        "metric": "mae",
                        "value": 87.017,
                        "rank": 1,
                        "total_participants": 3
                    },
                    {
                        "submission": "c83b7fe4-faac-47f8-8eaa-c0a6a1ab0de2",
                        "variable": "q50",
                        "metric": "pinball",
                        "value": 43.508,
                        "rank": 1,
                        "total_participants": 3
                    },
                    {
                        "submission": "c83b7fe4-faac-47f8-8eaa-c0a6a1ab0de2",
                        "variable": "q50",
                        "metric": "rmse",
                        "value": 106.97,
                        "rank": 1,
                        "total_participants": 3
                    }
                ],
                "general_metrics": [
                    {
                        "submission__variable": "q50",
                        "metric": "mae",
                        "avg_value": 493.211,
                        "min_value": 87.017,
                        "max_value": 1302.641,
                        "std_value": 572.354
                    },
                    {
                        "submission__variable": "q50",
                        "metric": "pinball",
                        "avg_value": 246.606,
                        "min_value": 43.508,
                        "max_value": 651.321,
                        "std_value": 286.178
                    },
                    {
                        "submission__variable": "q50",
                        "metric": "rmse",
                        "avg_value": 543.524,
                        "min_value": 106.97,
                        "max_value": 1413.905,
                        "std_value": 615.454
                    }
                ]
            }
        }
    },
)


MarketSessionSubmissionScoresRetrieveResponse = {
    "GET": GetMarketSessionSubmissionScoresRetrieveResponse,
}


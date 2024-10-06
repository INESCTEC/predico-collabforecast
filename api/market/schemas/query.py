from drf_yasg import openapi


################################
#  Query params templates
################################
def market_balance_query_params():
    return [
        openapi.Parameter("balance__gte", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Balance filter (greater or equal than)."),

        openapi.Parameter("balance__lte", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Balance filter (lower or equal than)."),
    ]


def market_balance_transfer_out_query_params():
    return [
        openapi.Parameter("is_solid", openapi.IN_QUERY,
                          type=openapi.TYPE_BOOLEAN,
                          required=False,
                          default=False,
                          description="Filter transactions which are "
                                      "solid (confirmed) in IOTA Tangle"),
    ]


def market_session_balance_query_params():
    return [
        openapi.Parameter("balance__gte", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Balance filter (greater or equal than)."),

        openapi.Parameter("balance__lte", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Balance filter (lower or equal than)."),
        openapi.Parameter("balance_by_resource", openapi.IN_QUERY,
                          type=openapi.TYPE_BOOLEAN,
                          required=False,
                          description="If true, returns balance by individual "
                                      "resource of each user in each session. "
                                      "Else, if false, returns the sum of "
                                      "balance per user in each session."),
    ]


def market_session_query_params():
    return [
        openapi.Parameter("market_session", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER,
                          required=False,
                          description="Filter by market session identifier"),
        openapi.Parameter("status", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by market session status"),
        openapi.Parameter("latest_only", openapi.IN_QUERY,
                          type=openapi.TYPE_BOOLEAN,
                          required=False,
                          description="Return latest session only"),
    ]


def market_session_transactions_query_params():
    return [
        openapi.Parameter("market_session", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER,
                          required=False,
                          description="Filter by market session identifier"),
    ]


def market_session_challenge_query_params():
    return [
        openapi.Parameter("market_session", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER,
                          required=False,
                          description="Filter by market session identifier"),
        openapi.Parameter("resource", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by agent resource identifier"),
        openapi.Parameter("challenge", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by challenge identifier"),
        openapi.Parameter("open_only", openapi.IN_QUERY,
                          type=openapi.TYPE_BOOLEAN,
                          required=False,
                          description="Filter by open challenges only"),
        openapi.Parameter("use_case", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          enum=["wind_power", "wind_power_ramp"],
                          description="Filter by challenge use case"),
    ]


def market_session_challenge_weights_query_params():
    return [
        openapi.Parameter("challenge", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by challenge identifier"),
        openapi.Parameter("pending_only", openapi.IN_QUERY,
                          type=openapi.TYPE_BOOLEAN,
                          required=False,
                          description="Filter by challenges yet without "
                                      "weights attribution."),
    ]


def market_session_list_ensemble_query_params():
    return [
        openapi.Parameter("challenge", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by challenge identifier"),
    ]


def market_session_challenge_submission_query_params():
    return [
        openapi.Parameter("challenge", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by challenge identifier"),
        openapi.Parameter("submission", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by challenge submission "
                                      "identifier"),
    ]


def market_session_list_ensemble_weights_query_params():
    return [
        openapi.Parameter("ensemble", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by ensemble identifier"),
    ]


def market_session_challenge_solution_query_params():
    return [
        openapi.Parameter("challenge", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by challenge identifier"),
    ]
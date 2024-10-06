from drf_yasg import openapi


################################
#  Query params templates
################################
def raw_data_query_params():
    return [
        openapi.Parameter("start_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request start datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T00:00:00Z"),
        openapi.Parameter("end_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request end datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T10:00:00Z"),
        openapi.Parameter("resource", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by agent resource identifier"),
    ]


def market_forecasts_query_params():
    return [
        openapi.Parameter("start_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request start datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T00:00:00Z"),
        openapi.Parameter("end_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request end datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T10:00:00Z"),
        openapi.Parameter("resource", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER,
                          required=True,
                          description="Filter by agent resource identifier"),
        openapi.Parameter("market_session", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER,
                          required=False,
                          description="Filter by market session identifier"),
    ]


def individual_forecasts_query_params():
    return [
        openapi.Parameter("start_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request start datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T00:00:00Z"),
        openapi.Parameter("end_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request end datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T10:00:00Z"),
        openapi.Parameter("resource", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by agent resource identifier"),
        openapi.Parameter("market_session", openapi.IN_QUERY,
                          type=openapi.TYPE_INTEGER,
                          required=False,
                          description="Filter by market session identifier"),
    ]


def individual_forecasts_historical_query_params():
    return [
        openapi.Parameter("start_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request start datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T00:00:00Z"),
        openapi.Parameter("end_date", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Request end datetime "
                                      "[`'%Y-%m-%dT%H:%M:%SZ'`]. "
                                      "Example: 2021-01-01T10:00:00Z"),
        openapi.Parameter("resource", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=True,
                          description="Filter by agent resource identifier"),
    ]


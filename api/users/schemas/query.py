from drf_yasg import openapi


################################
#  Query params templates
################################
def user_resources_query_params():
    return [
        openapi.Parameter("resource", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by resource identifier (uuid)"),
        openapi.Parameter("resource_name", openapi.IN_QUERY,
                          type=openapi.TYPE_STRING,
                          required=False,
                          description="Filter by resource name"),
    ]

from rest_framework.pagination import LimitOffsetPagination


class CustomPagination(LimitOffsetPagination):
    default_limit = 1500   # default number of records to retrieve per page
    max_limit = 1500  # maximum number of records to retrieve per page
    limit_query_param = 'limit'
    offset_query_param = 'offset'

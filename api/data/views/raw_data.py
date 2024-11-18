from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from api.pagination import CustomPagination
from api.renderers.CustomRenderer import CustomRenderer
from api.utils.permissions import method_permission_classes
from api.utils.custom_schema import conditional_swagger_auto_schema

from ..schemas.query import *
from ..schemas.responses import *
from ..util.validators import validate_query_params
from ..serializers.raw_data import (
    RawDataRetrieveSerializer,
    RawDataCreateSerializer,
)
from ..models.raw_data import RawData


class RawDataView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @staticmethod
    def queryset(request):
        # Query parameters:
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        resource_id = request.query_params.get('resource', None)
        # Enforce required parameters:
        if start_date is None:
            raise exceptions.ValidationError("Query parameter 'start_date' is required.")  # noqa
        if end_date is None:
            raise exceptions.ValidationError("Query parameter 'end_date' is required.")  # noqa
        if resource_id is None:
            raise exceptions.ValidationError("Query parameter 'resource' is required.")  # noqa
        # Validate query parameters:
        validate_query_params(
            start_date=start_date,
            end_date=end_date,
            resource_id=resource_id,
        )
        # Base query:
        query = RawData.objects.all()
        # Enforce required parameters:
        if start_date is not None:
            query = query.filter(datetime__gte=start_date)
        if end_date is not None:
            query = query.filter(datetime__lte=end_date)
        if resource_id is not None:
            query = query.filter(resource_id=resource_id)
        # Order records by datetime
        query = query.order_by('datetime')
        return query

    @swagger_auto_schema(
        operation_id="get_raw_data",
        operation_description="Method to get raw data for a specific "
                              "agent resource. You can know more about the "
                              "data to be retrieved "
                              "(n_samples, start/end datetimes) via "
                              "a GET request to the /user/resource/ endpoint.",
        manual_parameters=raw_data_query_params(),
        responses={
            200: RawDataResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        address = self.queryset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(address, request)
        if page is not None:
            serializer = RawDataRetrieveSerializer(page, many=True)  # noqa
            return paginator.get_paginated_response(serializer.data)
        serializer = RawDataRetrieveSerializer(address, many=True)  # noqa
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @conditional_swagger_auto_schema(
        operation_id="post_raw_data",
        operation_description="Method for agents to post raw data "
                              "for a specific resource",
        request_body=RawDataCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    @method_permission_classes((IsAdminUser,))
    def post(self, request):
        request_data = request.data.copy()
        request_data["user"] = request.user.id
        serializer = RawDataCreateSerializer(
            data=request_data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)

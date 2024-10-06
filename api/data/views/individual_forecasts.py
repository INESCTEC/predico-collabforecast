from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.pagination import CustomPagination
from api.renderers.CustomRenderer import CustomRenderer
from market.models.market_session_submission import MarketSessionSubmissionForecasts

from ..schemas.query import *
from ..schemas.responses import *
from ..util.validators import validate_query_params
from ..models.individual_forecasts import IndividualForecasts
from ..serializers.individual_forecasts import (
    IndividualForecastsRetrieveSerializer,
    IndividualForecastsHistoricalCreateSerializer,
    IndividualForecastsHistoricalRetrieveSerializer
)


class IndividualForecastsView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @staticmethod
    def queryset(request):
        # Query parameters:
        user = request.user
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        resource_id = request.query_params.get('resource', None)
        market_session_id = request.query_params.get('market_session', None)
        challenge_id = request.query_params.get('challenge', None)
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
            market_session_id=market_session_id,
            challenge_id=challenge_id
        )
        # Perform query using Django ORM
        base_query = MarketSessionSubmissionForecasts.objects.select_related(
            'submission__market_session_challenge'
        ).all()
        if user.is_superuser:
            user_id = request.query_params.get('user', None)
            if user_id:
                query = base_query.filter(submission__user_id=user_id)
            else:
                query = base_query.all()
        else:
            query = base_query.filter(submission__user_id=user.id)
        # Filter by query dates:
        if start_date is not None:
            query = query.filter(datetime__gte=start_date)
        if end_date is not None:
            query = query.filter(datetime__lte=end_date)
        if market_session_id:
            query = query.filter(submission__market_session_challenge__market_session_id=market_session_id)  # noqa
        if resource_id:
            query = query.filter(submission__market_session_challenge__resource_id=resource_id)  # noqa
        # Order records by datetime
        query = query.order_by('datetime').all()
        return query

    @swagger_auto_schema(
        operation_id="get_individual_forecasts",
        operation_description="Method to get agents individual forecasts "
                              "for a specific resource",
        manual_parameters=individual_forecasts_query_params(),
        responses={
            200: IndividualForecastsResponse["GET"],
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
            serializer = IndividualForecastsRetrieveSerializer(page, many=True)  # noqa
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = IndividualForecastsRetrieveSerializer(address, many=True)  # noqa
            return Response(data=serializer.data, status=status.HTTP_200_OK)


class IndividualForecastsHistoricalCreateRetrieveView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @staticmethod
    def queryset(request):
        # Query parameters:
        user = request.user
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        resource_id = request.query_params.get('resource', None)
        # Enforce required parameters:
        if start_date is None:
            raise ValueError("Query parameter 'start_date' is required.")
        if end_date is None:
            raise ValueError("Query parameter 'end_date' is required.")
        if resource_id is None:
            raise ValueError("Query parameter 'resource' is required.")
        # Validate query parameters:
        validate_query_params(
            start_date=start_date,
            end_date=end_date,
            resource_id=resource_id,
        )
        # Perform query using Django ORM
        base_query = IndividualForecasts.objects.filter(
            resource_id=resource_id,
            datetime__gte=start_date,
            datetime__lte=end_date
        )
        if user.is_superuser:
            user_id = request.query_params.get('user', None)
            query = base_query.filter(user=user_id) \
                if user_id else base_query.all()
        else:
            query = base_query.filter(user=user.id)
        # Order records by datetime
        query = query.order_by('datetime').all()
        return query

    @swagger_auto_schema(
        operation_id="get_individual_forecasts_historical",
        operation_description="Method to get initial historical forecasts "
                              "upload reference, for a specific market "
                              "resource.",
        manual_parameters=individual_forecasts_historical_query_params(),
        responses={
            200: HistoricalIndividualForecastsResponse["GET"],
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
            serializer = IndividualForecastsHistoricalRetrieveSerializer(page, many=True)  # noqa
            return paginator.get_paginated_response(serializer.data)
        serializer = IndividualForecastsHistoricalRetrieveSerializer(address, many=True)  # noqa
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    @swagger_auto_schema(
        operation_id="post_individual_forecasts_historical",
        operation_description="Method for agents to post historical "
                              "forecasts for a specific market resource.",
        request_body=IndividualForecastsHistoricalCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def post(request):
        request_data = request.data.copy()
        request_data["user"] = request.user.id
        serializer = IndividualForecastsHistoricalCreateSerializer(
            data=request_data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)

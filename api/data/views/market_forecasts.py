from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from api.renderers.CustomRenderer import CustomRenderer
from market.models.market_session_ensemble_forecasts import MarketSessionEnsembleForecasts  # noqa

from ..schemas.query import *
from ..schemas.responses import *
from ..util.validators import validate_query_params
from ..serializers.market_forecasts import (
    MarketForecastsRetrieveSerializer,
)


class MarketForecastsView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAdminUser,)

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
        base_query = MarketSessionEnsembleForecasts.objects.select_related('ensemble__market_session_challenge')  # noqa
        user_id = request.query_params.get('user', None)
        query = base_query.filter(user=user_id) if user_id else base_query.all()
        if start_date is not None:
            query = query.filter(datetime__gte=start_date)
        if end_date is not None:
            query = query.filter(datetime__lte=end_date)
        if resource_id:
            query = query.filter(ensemble__market_session_challenge__resource_id=resource_id)  # noqa
        # Order records by datetime
        query = query.order_by('datetime')
        return query

    @swagger_auto_schema(
        operation_id="get_market_forecasts",
        operation_description="Method to get market forecasts "
                              "for a specific resource",
        manual_parameters=individual_forecasts_query_params(),
        responses={
            200: RawDataResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        address = self.queryset(request)
        serializer = MarketForecastsRetrieveSerializer(address, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

import structlog

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.renderers.CustomRenderer import CustomRenderer
from ..schemas.responses import *
from ..schemas.query import *
from ..util.validators import validate_query_params
from ..models.market_session_ensemble_forecasts import MarketSessionEnsemble
from ..serializers.market_session_ensemble_weights import (
    MarketSessionEnsembleWeightsCreateSerializer,
    MarketSessionChallengesWeightsRetrieveSerializer
)

# init logger:
logger = structlog.get_logger("api_logger")


class MarketSessionChallengeWeightsCreateUpdateView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    @swagger_auto_schema(
        operation_id="post_market_session_ensemble_weights",
        operation_description="Method for market maker to submit weights "
                              "for a challenge ensemble forecast",
        request_body=MarketSessionEnsembleWeightsCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def post(request, challenge_id):
        serializer = MarketSessionEnsembleWeightsCreateSerializer(
            data=request.data,
            context={'request': request, 'challenge_id': challenge_id},
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)


class MarketSessionChallengesWeightsRetrieveView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        pending_only = request.query_params.get('pending_only', None)
        challenge_id = request.query_params.get('challenge', None)
        validate_query_params(
            challenge_id=challenge_id,
            pending_only=pending_only
        )
        # Construct query filters using Q objects for conditional filtering
        query_filters = Q()
        if challenge_id:
            query_filters &= Q(market_session_challenge_id=challenge_id)
        # Default latest_only query param to False if not declared
        pending_only = 'false' if pending_only is None else pending_only.lower()
        if pending_only != "false":
            challenge = MarketSessionEnsemble.objects.filter(
                query_filters,
                weights__isnull=True
            ).select_related('market_session_challenge')
        else:
            challenge = MarketSessionEnsemble.objects.select_related(
                'market_session_challenge'
            ).filter(query_filters).all()  # noqa
        return challenge

    @swagger_auto_schema(
        operation_id="get_market_session_challenge_weights",
        operation_description="Method for market maker to list challenges "
                              "and respective weights attribution",
        manual_parameters=market_session_challenge_weights_query_params(),
        responses={
            200: MarketSessionEnsembleWeightsResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        from itertools import groupby
        challenge = self.queryset(request)
        serializer = MarketSessionChallengesWeightsRetrieveSerializer(challenge, many=True)  # noqa
        data = serializer.data

        # Group the data by 'challenge'
        data.sort(key=lambda x: x['challenge'])
        grouped_data = []
        for key, group in groupby(data, key=lambda x: x['challenge']):
            group_list = list(group)
            grouped_data.append({
                'challenge': key,
                'use_case': group_list[0]['use_case'],
                'start_datetime': group_list[0]['start_datetime'],
                'end_datetime': group_list[0]['end_datetime'],
                'resource': group_list[0]['resource'],
                'ensemble_data': [item['data_fields'] for item in group_list]
            })

        return Response(grouped_data)


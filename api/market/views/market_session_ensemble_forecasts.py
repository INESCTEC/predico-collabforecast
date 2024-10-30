import structlog

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.renderers.CustomRenderer import CustomRenderer
from ..schemas.responses import *
from ..schemas.query import *
from ..models.market_session_ensemble_forecasts import (
    MarketSessionEnsembleForecasts,
    MarketSessionEnsemble,
    MarketSessionRampAlerts
)
from ..serializers.market_session_ensemble_forecasts import (
    MarketSessionEnsembleRetrieveSerializer,
    MarketSessionEnsembleCreateSerializer,
    MarketSessionEnsembleMetaRetrieveSerializer,
    MarketSessionRampAlertsRetrieveSerializer,
    MarketSessionRampAlertsCreateSerializer
)
from ..util.validators import validate_query_params

# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionListEnsembleForecastsView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        # Query params:
        user_id = request.user.id
        challenge_id = request.query_params.get('challenge')
        # Enforce query params:
        if challenge_id is None:
            raise exceptions.ValidationError("Query parameter 'challenge' is required.")  # noqa
        # Validate query params:
        validate_query_params(challenge_id=challenge_id)
        # Construct query filters using Q objects for conditional filtering
        # Filter by this market maker user challenges only:
        query_filters = Q(ensemble__market_session_challenge__user_id=user_id)
        if challenge_id:
            query_filters &= Q(ensemble__market_session_challenge_id=challenge_id)  # noqa
        # Perform query using Django ORM
        ensemble = MarketSessionEnsembleForecasts.objects.filter(query_filters).select_related('ensemble__market_session_challenge').all()  # noqa
        return ensemble

    @swagger_auto_schema(
        operation_id="get_market_session_ensemble_forecasts",
        operation_description="Method for agents to list submissions for "
                              "current or previous challenges",
        manual_parameters=market_session_list_ensemble_query_params(),
        responses={
            200: MarketSessionEnsembleForecastsResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        """
        Get all session participants
        :param request:
        :return:
        """
        challenge = self.queryset(request)
        serializer = MarketSessionEnsembleRetrieveSerializer(challenge, many=True)
        return Response(serializer.data)


class MarketSessionCreateEnsembleForecastsView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    @swagger_auto_schema(
        operation_id="post_market_session_ensemble_forecasts",
        operation_description="Method for agents to submit forecasts "
                              "for an open challenge",
        request_body=MarketSessionEnsembleCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def post(request, challenge_id):
        """
        Post a submission for a challenge
        :param request:
        :param challenge_id:
        :return:
        """
        user_id = request.user.id
        serializer = MarketSessionEnsembleCreateSerializer(
            data=request.data,
            context={'request': request, 'challenge_id': challenge_id,
                     'user_id': user_id},
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)


class MarketSessionListEnsembleForecastsMetaView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        # Query params:
        user_id = request.user.id
        challenge_id = request.query_params.get('challenge')
        # Enforce query params:
        if challenge_id is None:
            raise exceptions.ValidationError("Query parameter 'challenge' is required.")  # noqa
        # Validate query params:
        validate_query_params(challenge_id=challenge_id)
        # Construct query filters using Q objects for conditional filtering
        query_filters = Q(market_session_challenge__user_id=user_id)
        if challenge_id:
            query_filters &= Q(market_session_challenge_id=challenge_id)  # noqa
        # Perform query using Django ORM
        ensemble = MarketSessionEnsemble.objects.filter(query_filters).select_related('market_session_challenge').all()  # noqa
        return ensemble

    @swagger_auto_schema(
        operation_id="get_market_session_ensemble_forecasts_meta",
        operation_description="Method for agents to list submissions metadata "
                              "for current or previous challenges",
        manual_parameters=market_session_list_ensemble_query_params(),
        responses={
            # 200: MarketSessionEnsembleForecastsResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        """
        Get all session participants
        :param request:
        :return:
        """
        challenge = self.queryset(request)
        serializer = MarketSessionEnsembleMetaRetrieveSerializer(challenge,
                                                                 many=True)
        return Response(serializer.data)


class MarketSessionListRampAlertsView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        # Query params:
        user_id = request.user.id
        challenge_id = request.query_params.get('challenge')
        # Enforce query params:
        if challenge_id is None:
            raise exceptions.ValidationError("Query parameter 'challenge' is required.")  # noqa
        # Validate query params:
        validate_query_params(challenge_id=challenge_id)
        # Construct query filters using Q objects for conditional filtering
        # Filter by this market maker user challenges only:
        query_filters = Q(challenge__user_id=user_id)
        if challenge_id:
            query_filters &= Q(challenge_id=challenge_id)  # noqa
        # Perform query using Django ORM
        ensemble = MarketSessionRampAlerts.objects.filter(query_filters).all()  # noqa
        return ensemble

    @swagger_auto_schema(
        operation_id="get_market_session_ramp_alerts",
        operation_description="Method for agents to list ramp alerts for "
                              "current or previous challenges",
        manual_parameters=market_session_list_ensemble_query_params(),
        responses={
            200: MarketSessionRampAlertsResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        """
        Get all session participants
        :param request:
        :return:
        """
        challenge = self.queryset(request)
        serializer = MarketSessionRampAlertsRetrieveSerializer(challenge, many=True)
        return Response(serializer.data)


class MarketSessionCreateRampAlertsView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    @swagger_auto_schema(
        operation_id="post_market_session_ramp_alerts",
        operation_description="Method for agents to submit ramp alerts "
                              "for an open challenge",
        request_body=MarketSessionRampAlertsCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def post(request, challenge_id):
        user_id = request.user.id
        serializer = MarketSessionRampAlertsCreateSerializer(
            data=request.data,
            context={'request': request, 'challenge_id': challenge_id,
                     'user_id': user_id},
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)

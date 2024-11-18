import structlog

from django.conf import settings
from django.db.models import Q

from drf_yasg.utils import swagger_auto_schema

from rest_framework import status, exceptions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.utils.custom_schema import conditional_swagger_auto_schema
from api.utils.permissions import method_permission_classes
from api.email.utils.email_utils import send_email_as_thread
from api.renderers.CustomRenderer import CustomRenderer
from data.models import RawData
from data.serializers.raw_data import RawDataRetrieveSerializer
from ..models.market_session_challenge import MarketSessionChallenge
from ..schemas.responses import *
from ..schemas.query import *
from ..util.validators import validate_query_params
from ..serializers.market_session_challenge import (
    MarketSessionChallengeCreateSerializer,
    MarketSessionChallengeUpdateSerializer,
    MarketSessionChallengeRetrieveSerializer,
)

# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionChallengeView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        # Query parameters:
        market_session_id = request.query_params.get('market_session', None)
        resource_id = request.query_params.get('resource', None)
        challenge_id = request.query_params.get('challenge', None)
        open_only = request.query_params.get('open_only', None)
        challenge_use_case = request.query_params.get('use_case', None)
        # Validate query parameters:
        validate_query_params(
            challenge_id=challenge_id,
            resource_id=resource_id,
            market_session_id=market_session_id,
            open_only=open_only,
            challenge_use_case=challenge_use_case
        )
        # Construct query filters using Q objects for conditional filtering
        query_filters = Q()
        if challenge_id:
            query_filters &= Q(id=challenge_id)
        if market_session_id:
            query_filters &= Q(market_session_id=market_session_id)
        if resource_id:
            query_filters &= Q(resource_id=resource_id)
        # Default latest_only query param to False if not declared
        open_only = 'false' if open_only is None else open_only.lower()
        if open_only != "false":
            challenge = MarketSessionChallenge.objects.filter(
                query_filters,
                market_session__status='open'  # Add this line
            ).select_related('market_session')
        else:
            challenge = MarketSessionChallenge.objects.filter(
                query_filters
            ).select_related('market_session').all()  # noqa
        return challenge

    @swagger_auto_schema(
        operation_id="get_market_session_challenge",
        operation_description="List market session(s) challenge(s).",
        manual_parameters=market_session_challenge_query_params(),
        responses={
            200: MarketSessionChallengeResponse["GET"],
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
        serializer = MarketSessionChallengeRetrieveSerializer(
            challenge,
            many=True,
            context={'request': request})
        return Response(serializer.data)

    @conditional_swagger_auto_schema(
        operation_id="post_market_session_challenge",
        operation_description="Method for market makers to register challenge "
                              "to obtain forecasts for a given resource "
                              "in their portfolio and a specific "
                              "market session.",
        request_body=MarketSessionChallengeCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    @method_permission_classes((IsAdminUser,))
    def post(self, request):
        serializer = MarketSessionChallengeCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        if settings.ENVIRONMENT == "production":
            email = request.user.email
            send_email_as_thread(
                destination=[email],
                email_opt_key="email-challenge-confirmation",
                format_args=serializer.validated_data,
                fail_silently=False
            )

        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)


class MarketSessionChallengeUpdateView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    @conditional_swagger_auto_schema(
        operation_id="put_market_session_challenge",
        operation_description="Method for agents to update a posted challenge",
        request_body=MarketSessionChallengeUpdateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def put(request, challenge_id=None):
        if challenge_id is None:
            raise exceptions.ValidationError("Missing 'challenge_id' "
                                             "url parameter.")

        try:
            challenge = MarketSessionChallenge.objects.get(id=challenge_id,
                                                           user=request.user.id)
            serializer = MarketSessionChallengeUpdateSerializer(
                challenge,
                data=request.data,
                partial=True,
                context={'request': request, "challenge_id": challenge_id})
            serializer.is_valid(raise_exception=True)
            updated_challenge = serializer.update(challenge,
                                                  serializer.validated_data)

            # Serialize the updated challenge
            response_serializer = MarketSessionChallengeRetrieveSerializer(
                updated_challenge
            )
            return Response(data=response_serializer.data,
                            status=status.HTTP_200_OK)

        except MarketSessionChallenge.DoesNotExist:
            return Response(data=f"Challenge '{challenge_id}' does not exist "
                                 f"for this user.",
                            status=status.HTTP_400_BAD_REQUEST)


class MarketSessionChallengeSolutionView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        # Query parameters:
        challenge_id = request.query_params.get('challenge')
        # Enforce required parameters:
        if not challenge_id:
            raise exceptions.ValidationError("Missing 'challenge' query parameter.")  # noqa
        # Validate query parameters:
        validate_query_params(challenge_id=challenge_id)
        try:
            # Query challenge data
            challenge = MarketSessionChallenge.objects.get(id=challenge_id)
        except MarketSessionChallenge.DoesNotExist as ex:
            raise exceptions.ValidationError(
                f"Challenge '{challenge_id}' does not exist."
            ) from ex

        return challenge

    @swagger_auto_schema(
        operation_id="get_market_session_challenge_solution",
        operation_description="Method for agents to get observed data (solution) "
                              "for a given challenge",
        manual_parameters=market_session_challenge_solution_query_params(),
        responses={
            200: MarketSessionChallengeSolutionResponse["GET"],
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
        challenge_serializer = MarketSessionChallengeRetrieveSerializer(
            challenge,
        )
        # Query raw data
        data = RawData.objects.filter(
            datetime__gte=challenge.start_datetime,
            datetime__lte=challenge.end_datetime,
            resource_id=challenge.resource_id
        ).order_by('datetime').all()
        data_serializer = RawDataRetrieveSerializer(data, many=True)
        return Response({
            'challenge': challenge_serializer.data,
            'solution': data_serializer.data
        })

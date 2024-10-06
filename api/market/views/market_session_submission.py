import structlog
from django.conf import settings
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import exceptions

from api.email.utils.email_utils import send_email_as_thread
from api.renderers.CustomRenderer import CustomRenderer
from ..schemas.responses import *
from ..schemas.query import *
from ..util.validators import validate_query_params
from ..models.market_session_submission import (
    MarketSessionSubmission,
    MarketSessionSubmissionForecasts
)
from ..serializers.market_session_submission import (
    MarketSessionSubmissionForecastsRetrieveSerializer,
    MarketSessionSubmissionRetrieveSerializer,
    MarketSessionSubmissionCreateUpdateSerializer,
)

# init logger:
logger = structlog.get_logger("api_logger")


class MarketSessionListSubmissionForecastsView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        user = request.user
        challenge_id = request.query_params.get('challenge')
        submission_id = request.query_params.get('submission')

        # Enforce required parameters:
        if challenge_id is None:
            raise exceptions.ValidationError("Query parameter 'challenge' is required.")
        
        # Validate query parameters:
        validate_query_params(
            challenge_id=challenge_id,
            submission_id=submission_id
        )
        
        # If user is not superuser, filter by user_id else give the superuser
        # the ability to filter by user_id
        user_id = request.query_params.get('user') if user.is_superuser else user.id  # noqa

        # Construct query filters using Q objects for conditional filtering
        query_filters = Q()
        if user.is_superuser:
            # Market Maker X should not be able to list submissions for
            # challenges of Market Maker Y
            query_filters &= Q(submission__market_session_challenge__user_id=user.id)
        if challenge_id:
            query_filters &= Q(submission__market_session_challenge_id=challenge_id)  # noqa
        if submission_id:
            query_filters &= Q(submission__id=submission_id)
        if user_id:
            query_filters &= Q(submission__user_id=user_id)

        # Perform query using Django ORM
        submission = (MarketSessionSubmissionForecasts.objects.filter(query_filters)
                      .select_related('submission')
                      .all())  # noqa

        return submission

    @swagger_auto_schema(
        operation_id="get_market_session_submission_forecasts",
        operation_description="Method for agents to list submission "
                              "forecasts for market challenges",
        manual_parameters=market_session_challenge_submission_query_params(),
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
        serializer = MarketSessionSubmissionForecastsRetrieveSerializer(
            challenge,
            many=True
        )
        return Response(serializer.data)


class MarketSessionListSubmissionView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        user = request.user
        challenge_id = request.query_params.get('challenge')

        # Enforce required parameters:
        if challenge_id is None:
            raise exceptions.ValidationError("Query parameter 'challenge' is required.")

        # Validate query parameters:
        validate_query_params(
            challenge_id=challenge_id
        )
        
        # If user is not superuser, filter by user_id else give the superuser
        # the ability to filter by user_id
        user_id = request.query_params.get('user') if user.is_superuser else user.id  # noqa

        # Construct query filters using Q objects for conditional filtering
        query_filters = Q()

        if user.is_superuser:
            # Market Maker X should not be able to list submissions for
            # challenges of Market Maker Y
            query_filters &= Q(market_session_challenge__user_id=user.id)
        if challenge_id:
            query_filters &= Q(market_session_challenge_id=challenge_id)
        if user_id:
            query_filters &= Q(user_id=user_id)

        # Perform query using Django ORM
        submission = MarketSessionSubmission.objects.filter(query_filters).select_related('market_session_challenge').all()  # noqa

        return submission

    @swagger_auto_schema(
        operation_id="get_market_session_submission",
        operation_description="Method for agents to list submissions for "
                              "current or previous challenges",
        manual_parameters=market_session_challenge_submission_query_params(),
        responses={
            200: MarketSessionListSubmissionResponse["GET"],
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
        serializer = MarketSessionSubmissionRetrieveSerializer(challenge,
                                                               many=True)
        return Response(serializer.data)


class MarketSessionCreateUpdateSubmissionView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    @swagger_auto_schema(
        operation_id="post_market_session_submission",
        operation_description="Method for agents to submit forecasts "
                              "for an open challenge",
        request_body=MarketSessionSubmissionCreateUpdateSerializer,
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
        serializer = MarketSessionSubmissionCreateUpdateSerializer(
            data=request.data,
            context={'request': request, 'challenge_id': challenge_id},
        )
        serializer.is_valid(raise_exception=True)

        if settings.ENVIRONMENT == "production":
            email = request.user.email
            send_email_as_thread(
                destination=[email],
                email_opt_key="email-challenge-submission-confirmation",
                format_args=serializer.validated_data,
                fail_silently=False
            )

        response = serializer.save()
        return Response(data=response, status=status.HTTP_201_CREATED)

    @staticmethod
    @swagger_auto_schema(
        operation_id="put_market_session_submission",
        operation_description="Method for agents to submit forecasts "
                              "for an open challenge",
        request_body=MarketSessionSubmissionCreateUpdateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def put(request, challenge_id):
        if challenge_id is None:
            raise exceptions.ValidationError("Missing 'challenge_id' "
                                             "url parameter.")
        try:
            challenge = MarketSessionSubmission.objects.select_related(
                'market_session_challenge'
            ).filter(market_session_challenge__id=challenge_id).first()
            serializer = MarketSessionSubmissionCreateUpdateSerializer(
                challenge,
                data=request.data,
                partial=True,
                context={'request': request, "challenge_id": challenge_id})
            serializer.is_valid(raise_exception=True)
            updated_challenge = serializer.update(challenge,serializer.validated_data)
            return Response(data=updated_challenge, status=status.HTTP_200_OK)
        except MarketSessionSubmission.DoesNotExist as ex:
            raise exceptions.NotFound("Challenge not found.") from ex

import structlog
import pandas as pd

from django.db.models import Q, Avg, Min, Count, Max, F, Window, StdDev
from django.db.models.functions import Rank, Round
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.renderers.CustomRenderer import CustomRenderer
from api.utils.custom_schema import conditional_swagger_auto_schema

from ..models import MarketSessionSubmissionScores
from ..schemas.responses import *
from ..schemas.query import *
from ..util.validators import validate_query_params
from ..serializers.market_session_submission_scores import (
    MarketSessionSubmissionScoresCreateSerializer,
    MarketSessionSubmissionScoresRetrieveSerializer
)

# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionSubmissionScoresCreateView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]
    @staticmethod
    @conditional_swagger_auto_schema(
        operation_id="post_market_session_submission_scores",
        operation_description="Method for market maker to publish submission "
                              "scores for a challenge,",
        request_body=MarketSessionSubmissionScoresCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def post(request, challenge_id):
        serializer = MarketSessionSubmissionScoresCreateSerializer(
            data=request.data,
            context={'request': request, 'challenge_id': challenge_id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class MarketSessionSubmissionScoresRetrieveView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    def queryset(request):
        user = request.user
        challenge_id = request.query_params.get('challenge')
        # Enforce required parameters:
        if challenge_id is None:
            raise exceptions.ValidationError("Query parameter 'challenge' is required.")
        # If user is not superuser, filter by user_id else give the superuser
        # the ability to filter by user_id
        user_id = request.query_params.get('user') if user.is_superuser else user.id  # noqa
        validate_query_params(
            challenge_id=challenge_id,
            user_id=user_id
        )
        ##########################
        # Query personal metrics #
        ##########################
        # Construct query filters using Q objects for conditional filtering
        query_filters = Q()
        query_filters &= Q(submission__market_session_challenge_id=challenge_id)
        if user.is_superuser and (not user.is_session_manager):
            # Market Maker X should not be able to list submissions scores for
            # challenges of Market Maker Y
            query_filters &= Q(submission__market_session_challenge__user_id=user.id)  # noqa
        if user_id:
            query_filters &= Q(submission__user_id=user_id)
        # Perform query using Django ORM
        scores = MarketSessionSubmissionScores.objects.filter(query_filters).all()  # noqa

        ######################################
        # Query general (aggregated) metrics #
        ######################################
        query_filters = Q()
        query_filters &= Q(submission__market_session_challenge_id=challenge_id)
        if user.is_superuser and (not user.is_session_manager):
            # Market Maker X should not be able to list submissions scores for
            # challenges of Market Maker Y
            query_filters &= Q(submission__market_session_challenge__user_id=user.id)  # noqa
        # Query aggregated metrics:
        aggregated_data = MarketSessionSubmissionScores.objects.filter(
            query_filters
        ).values(
            'submission__variable',
            'metric'
        ).annotate(
            avg_value=Round(Avg('value'), 3),
            min_value=Round(Min('value'), 3),
            max_value=Round(Max('value'), 3),
            std_value=Round(StdDev('value'), 3),
        )
        ###############################
        # Get the ranked submissions  #
        ###############################
        # Get ranks of all submissions:
        query_filters = Q()
        query_filters &= Q(submission__market_session_challenge_id=challenge_id)
        if user.is_superuser and (not user.is_session_manager):
            # Market Maker X should not be able to list submissions scores for
            # challenges of Market Maker Y
            query_filters &= Q(submission__market_session_challenge__user_id=user.id)  # noqa
        ranked_submissions = MarketSessionSubmissionScores.objects.filter(
            query_filters
        ).annotate(
            rank=Window(
                expression=Rank(),
                partition_by='metric',  # Rank within each metric
                order_by=F('value').asc()  # Ascending order for ranking
            ),
            total_participants=Window(
                expression=Count('id'),
                partition_by='metric'
                # Count the total number of participants for each metric
            ),
        ).values(
            'submission',
            'submission__user_id',
            'metric',
            'rank',
            'total_participants'
        )
        # Filter to show only the current user's results
        if user_id is not None:
            user_ranked_submissions = [
                {k: v for k, v in x.items() if k != "submission__user_id"}
                for x in ranked_submissions if x['submission__user_id'] == user.id
            ]
        else:
            user_ranked_submissions = [
                {k: v for k, v in x.items() if k != "submission__user_id"}
                for x in ranked_submissions
            ]
        return scores, user_ranked_submissions, aggregated_data

    @swagger_auto_schema(
        operation_id="get_market_session_submission_scores",
        operation_description="List forecast skill scores for a challenge.",
        manual_parameters=market_session_submission_scores_query_params(),
        responses={
            200: MarketSessionSubmissionScoresRetrieveResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        # Get data:
        personal_submissions, ranked_submissions, aggregated_data = self.queryset(request)  # noqa
        serializer = MarketSessionSubmissionScoresRetrieveSerializer(personal_submissions, many=True)  # noqa
        # Convert to DF to facilitate join:
        df_personal = pd.DataFrame(serializer.data)
        df_ranked = pd.DataFrame(ranked_submissions)
        if not df_personal.empty and not df_ranked.empty:
            # Merge DataFrames on 'submission_id' and 'metric'
            merged_df = pd.merge(df_personal, df_ranked, on=['submission', 'metric'], how='inner')  # noqa
            merged_df.sort_values(by=["variable", "metric"], inplace=True)
            personal_metrics = merged_df.to_dict(orient="records")
            # Prepare Response payload:
            response = {
                "personal_metrics": personal_metrics,
                "general_metrics": aggregated_data
            }
        else:
            response = {
                "personal_metrics": [],
                "general_metrics": aggregated_data
            }
        return Response(data=response, status=status.HTTP_200_OK)



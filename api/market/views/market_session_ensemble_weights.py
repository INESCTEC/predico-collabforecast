import structlog
import pandas as pd

from django.db.models import Q, Count, F, Window
from django.db.models.functions import Rank
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.renderers.CustomRenderer import CustomRenderer
from api.utils.custom_schema import conditional_swagger_auto_schema

from ..schemas.responses import *
from ..schemas.query import *
from ..util.validators import validate_query_params
from ..models.market_session_ensemble_weights import MarketSessionEnsembleWeights
from ..serializers.market_session_ensemble_weights import (
    MarketSessionEnsembleWeightsCreateSerializer,
    MarketSessionEnsembleWeightsRetrieveSerializer,
)

# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionEnsembleWeightsCreateUpdateView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]

    @staticmethod
    @conditional_swagger_auto_schema(
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
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class MarketSessionEnsembleWeightsRetrieveView(APIView):
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
        ################################
        # Query personal contributions #
        ################################
        # Construct query filters using Q objects for conditional filtering
        query_filters = Q(ensemble__market_session_challenge_id=challenge_id)
        if user.is_superuser:
            # Market Maker X should not be able to list submissions scores for
            # challenges of Market Maker Y
            # (note that in this case user.id is the superuser ID)
            query_filters &= Q(ensemble__market_session_challenge__user_id=user.id)  # noqa
        if user_id:
            query_filters &= Q(user_id=user_id)
        # Perform query using Django ORM
        contributions = MarketSessionEnsembleWeights.objects.filter(query_filters).all()  # noqa
        ###############################
        # Get the ranked submissions  #
        ###############################
        # Get ranks of all submissions:
        query_filters = Q(ensemble__market_session_challenge_id=challenge_id)
        if user.is_superuser:
            # Market Maker X should not be able to list submissions scores for
            # challenges of Market Maker Y
            query_filters &= Q(ensemble__market_session_challenge__user_id=user.id)  # noqa

        ranked_contributions = MarketSessionEnsembleWeights.objects.filter(
            query_filters
        ).annotate(
            rank=Window(
                expression=Rank(),
                partition_by='ensemble_id',  # Rank within each metric
                order_by=F('value').desc()  # Ascending order for ranking
            ),
            total_participants=Window(
                expression=Count('id'),
                partition_by='ensemble_id'
                # Count the total number of participants for each metric
            ),
        ).values(
            'ensemble',
            'user',
            'rank',
            'total_participants'
        )
        # Filter to show only the current user's results
        if user_id is not None:
            ranked_contributions = [x
                for x in ranked_contributions if
                x['user'] == user.id
            ]
        return  contributions, ranked_contributions

    @swagger_auto_schema(
        operation_id="get_market_session_ensemble_weights",
        operation_description="List challenge details and respective "
                              "forecaster(s) contribution "
                              "for each ensemble forecast (1 per ensemble "
                              "quantile forecast).",
        manual_parameters=market_session_submission_scores_query_params(),
        responses={
            200: MarketSessionEnsembleWeightsResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        # Get data:
        contributions, ranked_contributions = self.queryset(request)
        contrib_serializer = MarketSessionEnsembleWeightsRetrieveSerializer(contributions, many=True)  # noqa
        # Convert to DF to facilitate join:
        df_contrib = pd.DataFrame(contrib_serializer.data)
        df_ranked = pd.DataFrame(ranked_contributions)
        # Merge DataFrames on 'ensemble' and 'user'
        if not df_contrib.empty and not df_ranked.empty:
            merged_df = pd.merge(df_contrib, df_ranked, on=['ensemble', 'user'], how='inner')  # noqa
            if not request.user.is_superuser:
                merged_df.drop(columns=["user", "value"], inplace=True)
            # Convert to dict for serialization:
            contributions = merged_df.to_dict(orient="records")
        else:
            contributions = []
        return Response(data=contributions, status=status.HTTP_200_OK)

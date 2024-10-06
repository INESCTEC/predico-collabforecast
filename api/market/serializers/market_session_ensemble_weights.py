import structlog
import pandas as pd

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from .. import exceptions as market_exceptions
from ..models.market_session import (
    MarketSession
)
from ..models.market_session_challenge import (
    MarketSessionChallenge,
)
from ..models.market_session_submission import (
    MarketSessionSubmission,
)
from ..models.market_session_ensemble_forecasts import (
    MarketSessionEnsemble,
    MarketSessionEnsembleForecasts
)


# init logger:
logger = structlog.get_logger("api_logger")


class MarketSessionEnsembleWeightsCreateSerializer(serializers.Serializer):

    ensemble_id = serializers.UUIDField(
        required=True,
        allow_null=False,
    )
    weights = serializers.JSONField(required=True)

    def validate(self, attrs):
        ensemble_id = attrs["ensemble_id"]
        # Check if this ensemble ID exists (should be created once
        # an ensemble forecast is issued):
        if not MarketSessionEnsemble.objects.filter(id=ensemble_id).exists():  # noqa
            raise market_exceptions.EnsembleNotFound(ensemble_id=ensemble_id)
        return attrs

    def create(self, validated_data):
        ensemble_id = validated_data["ensemble_id"]
        weights = validated_data["weights"]

        # Get ensemble ID:
        ensemble = MarketSessionEnsemble.objects.get(id=ensemble_id)
        # If weights already set, raise exception:
        if ensemble.weights is not None:
            raise market_exceptions.EnsembleWeightsAlreadySet(
                ensemble_id=ensemble_id
            )
        else:
            # Update Weights cell:
            ensemble.weights = weights
            ensemble.save()
            return {
                "ensemble": ensemble.id,
                "weights": weights,
            }


class EnsembleDataSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    ensemble = serializers.ReadOnlyField()
    model = serializers.ReadOnlyField()
    variable = serializers.ReadOnlyField()
    weights = serializers.JSONField()


class MarketSessionChallengesWeightsRetrieveSerializer(serializers.ModelSerializer):
    challenge = serializers.ReadOnlyField(
        source='market_session_challenge.id'
    )
    start_datetime = serializers.ReadOnlyField(
        source='market_session_challenge.start_datetime'
    )
    end_datetime = serializers.ReadOnlyField(
        source='market_session_challenge.end_datetime'
    )
    resource = serializers.ReadOnlyField(
        source='market_session_challenge.resource.id'
    )
    use_case = serializers.ReadOnlyField(
        source='market_session_challenge.use_case'
    )
    data_fields = EnsembleDataSerializer(
        source='*'
    )
    class Meta:
        model = MarketSessionEnsemble
        fields = ["challenge", "use_case", "start_datetime", "end_datetime",
                  "resource", "data_fields"]
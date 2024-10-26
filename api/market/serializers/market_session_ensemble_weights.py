import structlog

from rest_framework import serializers

from ..models.market_session_submission import (
    MarketSessionSubmission,
)
from ..models.market_session_ensemble_forecasts import (
    MarketSessionEnsemble,
)
from ..models.market_session_ensemble_weights import (
    MarketSessionEnsembleWeights,
)


# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionEnsembleWeightsCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MarketSessionEnsembleWeights
        exclude = []
        extra_kwargs = {
            'ensemble': {'required': True},
            'user': {'required': True},
            'value': {'required': True},
        }

    def validate(self, attrs):
        challenge_id = self.context.get("challenge_id")
        if not MarketSessionEnsemble.objects.filter(
                id=attrs["ensemble"].id,
                market_session_challenge_id=challenge_id).exists():
            raise serializers.ValidationError(
                f"Ensemble {attrs["ensemble"].id} does not belong "
                f"to this challenge"
            )
        if not MarketSessionSubmission.objects.filter(
                user=attrs["user"].id,
                market_session_challenge_id=challenge_id).exists():
            raise serializers.ValidationError(
                f"Submission {attrs["submission"].id} does not belong "
                f"to this challenge"
            )
        return attrs


class MarketSessionEnsembleWeightsRetrieveSerializer(serializers.ModelSerializer):
    variable = serializers.ReadOnlyField(
        source='ensemble.variable'
    )
    class Meta:
        model = MarketSessionEnsembleWeights
        fields = ["ensemble", "user", "variable", "value"]

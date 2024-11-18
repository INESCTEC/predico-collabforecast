import structlog
from rest_framework import serializers

from ..models.market_session_submission import MarketSessionSubmission
from ..models.market_session_submission_scores import (
    MarketSessionSubmissionScores,
)


# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionSubmissionScoresCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MarketSessionSubmissionScores
        exclude = []
        extra_kwargs = {
            'submission': {'required': True},
            'metric': {'required': True},
            'value': {'required': True},
        }

    def validate(self, attrs):
        challenge_id = self.context.get("challenge_id")
        if not MarketSessionSubmission.objects.filter(
                id=attrs["submission"].id,
                market_session_challenge_id=challenge_id).exists():
            raise serializers.ValidationError(
                "Submission does not belong to this challenge"
            )
        return attrs


class MarketSessionSubmissionScoresRetrieveSerializer(serializers.ModelSerializer):
    variable = serializers.ReadOnlyField(
        source='submission.variable'
    )
    class Meta:
        model = MarketSessionSubmissionScores
        fields = ["submission", "variable", "metric", "value"]

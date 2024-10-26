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
from ..models.market_session_ensemble_forecasts import (
    MarketSessionEnsemble,
    MarketSessionEnsembleForecasts
)


# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionEnsembleRetrieveSerializer(serializers.ModelSerializer):
    variable = serializers.ReadOnlyField(
        source='ensemble.variable'
    )
    resource = serializers.ReadOnlyField(
        source='ensemble.market_session_challenge.resource_id'
    )
    challenge = serializers.ReadOnlyField(
        source='ensemble.market_session_challenge.id'
    )
    class Meta:
        model = MarketSessionEnsembleForecasts
        fields = ["challenge", "resource",
                  "variable", "datetime",
                  "registered_at", "value"]


class MarketSessionEnsembleMetaRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSessionEnsemble
        fields = "__all__"


class MarketSessionEnsembleCreateSerializer(serializers.Serializer):
    model = serializers.ChoiceField(
        choices=MarketSessionEnsemble.EnsembleModel.choices,
        required=True,
        allow_null=False,
    )
    variable = serializers.ChoiceField(
        choices=MarketSessionEnsemble.ForecastsVariable.choices,
        required=True,
        allow_null=False,
    )

    class EnsembleForecastsTsSerializer(serializers.Serializer):
        datetime = serializers.DateTimeField(
            required=True,
            allow_null=False
        )
        value = serializers.FloatField(
            required=True,
            allow_null=False,
        )

    forecasts = EnsembleForecastsTsSerializer(many=True,
                                              required=True,
                                              allow_null=False)

    def validate(self, attrs):
        challenge_id = self.context.get('challenge_id')
        user_id = self.context.get('user_id')
        variable = attrs["variable"]

        # 1) Check if user is sending forecasts for an existing challenge
        try:
            # Check if this resource belongs to user:
            challenge = (MarketSessionChallenge.objects.
                         select_related('market_session').
                         get(id=challenge_id, user_id=user_id))
        except MarketSessionChallenge.DoesNotExist as ex:
            raise market_exceptions.ChallengeNotRegistered(
                challenge_id=challenge_id,
            ) from ex

        # 2) Check if admin is sending forecasts for an running challenge
        if challenge.market_session.status != MarketSession.MarketStatus.RUNNING:
            raise market_exceptions.ChallengeNotRunning(
                challenge_id=challenge_id,
            )

        # 3) Check if admin is sending forecasts for expected dates
        # in forecast horizon
        expected_leadtimes = pd.date_range(
            start=challenge.start_datetime,
            end=challenge.end_datetime,
            freq=f'{settings.FORECAST_TIME_RESOLUTION_MINUTES}T', tz="utc"
        )
        expected_leadtimes = [x.strftime("%Y-%m-%dT%H:%M:%SZ")
                              for x in expected_leadtimes]
        current_leadtimes = [x["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")
                             for x in attrs["forecasts"]]
        missing_leadtimes = [x for x in expected_leadtimes
                             if x not in current_leadtimes]
        incorrect_leadtimes = [x for x in current_leadtimes
                               if x not in expected_leadtimes]
        if len(missing_leadtimes) > 0:
            raise market_exceptions.IncompleteSubmission(
                missing_leadtimes=missing_leadtimes,
                f_variable=variable
            )
        # Check for incorrect leadtimes:
        if len(incorrect_leadtimes) > 0:
            raise market_exceptions.IncorrectSubmission(
                incorrect_leadtimes=incorrect_leadtimes,
                f_variable=variable
            )
        return attrs

    def create(self, validated_data):
        challenge_id = self.context.get('challenge_id')
        model_id = validated_data["model"]
        forecasts_data = validated_data["forecasts"]
        variable_id = validated_data["variable"]

        # Check if a submission for this challenge and model already exists:
        if MarketSessionEnsemble.objects.filter(
                market_session_challenge_id=challenge_id,
                model=model_id,
                variable=variable_id,
        ).exists():
            raise market_exceptions.SubmissionAlreadyExists(
                f_variable=variable_id,
            )

        try:
            # Prepare atomic transaction (all or nothing)
            with transaction.atomic():
                # Register submission:
                ensemble = MarketSessionEnsemble.objects.create(
                    market_session_challenge_id=challenge_id,
                    model=model_id,
                    variable=variable_id,
                )
                # Register forecasts
                for forecast in forecasts_data:
                    MarketSessionEnsembleForecasts.objects.create(
                        ensemble=ensemble,
                        datetime=forecast["datetime"],
                        value=forecast["value"]
                    )
            return {
                "challenge_id": challenge_id,
                "ensemble_id": ensemble.id,
            }
        except Exception as e:
            logger.exception("Failed to insert submission.")
            raise market_exceptions.FailedToInsertSubmission() from e



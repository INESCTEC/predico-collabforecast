import pytz
import structlog
import pandas as pd
import datetime as dt

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
    MarketSessionSubmissionForecasts
)
from data.models.individual_forecasts import IndividualForecasts


# init logger:
logger = structlog.get_logger(__name__)


class MarketSessionSubmissionRetrieveSerializer(serializers.ModelSerializer):
    market_session_challenge_resource_id = serializers.ReadOnlyField(
        source='market_session_challenge.resource_id'
    )

    class Meta:
        model = MarketSessionSubmission
        fields = '__all__'


class MarketSessionSubmissionForecastsRetrieveSerializer(serializers.ModelSerializer):
    variable = serializers.ReadOnlyField(
        source='submission.variable'
    )
    user = serializers.ReadOnlyField(
        source='submission.user.id'
    )
    resource = serializers.ReadOnlyField(
        source='submission.market_session_challenge.resource_id'
    )
    class Meta:
        model = MarketSessionSubmissionForecasts
        fields = ["submission", "resource",
                  "variable", "datetime",
                  "registered_at",
                  "value", "user"]


class MarketSessionSubmissionCreateUpdateSerializer(serializers.Serializer):
    variable = serializers.ChoiceField(
        choices=MarketSessionSubmission.ForecastsVariable.choices,
        required=True,
        allow_null=False,
    )

    class SubmissionForecastsTsSerializer(serializers.Serializer):
        datetime = serializers.DateTimeField(
            required=True,
            allow_null=False
        )
        value = serializers.FloatField(
            required=True,
            allow_null=False,
        )

    forecasts = SubmissionForecastsTsSerializer(many=True,
                                                required=True,
                                                allow_null=False)

    def validate(self, attrs):
        user_id = self.context.get('request').user.id
        challenge_id = self.context.get('challenge_id')
        variable_id = attrs["variable"]
        attrs["challenge_id"] = challenge_id
        # ---------------------------------------------------------------
        # 0) Check if quantile reference is valid:
        if str(variable_id).lower() not in settings.FORECAST_VARIABLES:
            raise serializers.ValidationError(
                {"variable": f"Invalid value. Must be one of: {settings.FORECAST_VARIABLES}"}  # noqa
            )
        # ---------------------------------------------------------------
        # 1) Check if user is sending forecasts for an existing challenge
        try:
            # Check if this resource belongs to user:
            challenge = MarketSessionChallenge.objects.select_related(
                'market_session'
            ).get(
                id=challenge_id,
            )
        except MarketSessionChallenge.DoesNotExist as ex:
            raise market_exceptions.ChallengeNotRegistered(
                challenge_id=challenge_id,
            ) from ex
        # ---------------------------------------------------------------
        # 2) Check if user is sending forecasts for an open challenge
        if challenge.market_session.status != MarketSession.MarketStatus.OPEN:
            raise market_exceptions.ChallengeNotOpen(
                challenge_id=challenge_id,
            )
        # ---------------------------------------------------------------
        # 3) If the user is submitting a forecast for any quantile other than
        # Q50, ensure Q50 forecasts exist first:
        if variable_id != MarketSessionSubmission.ForecastsVariable.Q50 and (
                not MarketSessionSubmissionForecasts.objects.filter(
                submission__user_id=user_id,
                submission__variable=MarketSessionSubmission.ForecastsVariable.Q50,
                submission__market_session_challenge_id=challenge_id
            ).exists()):
                raise market_exceptions.MissingQ50Forecasts()
        # ---------------------------------------------------------------
        # 4) Check if user is sending forecasts for expected dates
        # in forecast horizon
        expected_leadtimes = pd.date_range(
            start=challenge.start_datetime,
            end=challenge.end_datetime,
            freq=f'{settings.FORECAST_TIME_RESOLUTION_MINUTES}T',
            tz="utc"
        )
        expected_leadtimes = [x.strftime("%Y-%m-%dT%H:%M:%SZ")
                              for x in expected_leadtimes]
        current_leadtimes = [x["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")
                             for x in attrs["forecasts"]]
        missing_leadtimes = [x for x in expected_leadtimes
                             if x not in current_leadtimes]
        incorrect_leadtimes = [x for x in current_leadtimes
                               if x not in expected_leadtimes]
        # Check for missing leadtimes:
        if len(missing_leadtimes) > 0:
            raise market_exceptions.IncompleteSubmission(
                missing_leadtimes=missing_leadtimes,
                f_variable=variable_id
            )
        # Check for incorrect leadtimes:
        if len(incorrect_leadtimes) > 0:
            raise market_exceptions.IncorrectSubmission(
                incorrect_leadtimes=incorrect_leadtimes,
                f_variable=variable_id
            )
        # ---------------------------------------------------------------
        # 5) Check if the user fulfills the minimum historical
        # forecasts data for this challenge
        # Users should have a minimum samples of historical forecasts
        # -- Past submissions historical data:
        last_date_ = challenge.start_datetime
        first_date_ = last_date_ - pd.Timedelta(days=40)
        data_count_1 = MarketSessionSubmissionForecasts.objects.filter(
            submission__user_id=self.context.get('request').user.id,
            submission__variable=variable_id,
            submission__market_session_challenge__resource_id=challenge.resource_id,
            submission__market_session_challenge__start_datetime__gte=first_date_,
            submission__market_session_challenge__end_datetime__lte=last_date_,
        ).values_list('datetime', flat=True)

        # -- Historical Forecast data upload data:
        data_count_2 = IndividualForecasts.objects.filter(
            user_id=self.context.get('request').user.id,
            variable=variable_id,
            resource_id=challenge.resource_id,
            datetime__gte=first_date_,
            datetime__lte=last_date_
        ).values_list('datetime', flat=True)

        # -- Combine queried samples datetimes and remove duplicates:
        combined_datetimes = list(set(data_count_1) | set(data_count_2))

        # Check if there are sufficient historical forecast samples to
        # be able to run the ML ensemble models (and accept this submission):
        if len(combined_datetimes) < settings.MIN_RAW_DATA_COUNT_TO_CHALLENGE:
            raise market_exceptions.NotEnoughDataToSubmit(
                resource_id=challenge.resource_id,
                min_data_count=settings.MIN_RAW_DATA_COUNT_TO_CHALLENGE
            )
        # ---------------------------------------------------------------
        # Necessary for email:
        attrs["resource"] = challenge.resource_id
        return attrs

    def create(self, validated_data):
        user_id = self.context.get('request').user.id
        challenge_id = validated_data["challenge_id"]
        forecasts_data = validated_data["forecasts"]
        variable_id = validated_data["variable"]

        # Check if a submission for this challenge (w/ same variable) exists:
        if MarketSessionSubmission.objects.filter(
                user_id=user_id,
                variable=variable_id,
                market_session_challenge_id=challenge_id
        ).exists():
            raise market_exceptions.SubmissionAlreadyExists(
                f_variable=variable_id,
            )

        try:
            # Prepare atomic transaction (all or nothing)
            with transaction.atomic():
                # Register submission:
                submission = MarketSessionSubmission.objects.create(
                    user_id=user_id,
                    variable=variable_id,
                    market_session_challenge_id=challenge_id,
                )
                # Register forecasts
                for forecast in forecasts_data:
                    MarketSessionSubmissionForecasts.objects.create(
                        submission=submission,
                        datetime=forecast["datetime"],
                        value=forecast["value"]
                    )
            return {
                "challenge_id": challenge_id,
                "submission_id": submission.id,
            }
        except Exception as e:
            logger.exception("Failed to insert submission.")
            raise market_exceptions.FailedToInsertSubmission() from e

    def update(self, instance, validated_data):
        user_id = self.context.get('request').user.id
        challenge_id = validated_data["challenge_id"]
        forecasts_data = validated_data["forecasts"]
        variable_id = validated_data["variable"]

        # Check if a submission for this challenge (w/ same variable) exists:
        if not MarketSessionSubmission.objects.filter(
                user_id=user_id,
                variable=variable_id,
                market_session_challenge_id=challenge_id
        ).exists():
            # If not, raise error - should POST first to submit
            raise market_exceptions.SubmissionNotFound(
                user_id=user_id,
                f_variable=variable_id,
                challenge_id=challenge_id
            )

        try:
            # Prepare atomic transaction (all or nothing)
            with transaction.atomic():
                # Get existing submission submission:
                submission = MarketSessionSubmission.objects.get(
                    user_id=user_id,
                    variable=variable_id,
                    market_session_challenge_id=challenge_id,
                )
                submission.registered_at = dt.datetime.now()
                submission.save()
                # Update forecast values in submission
                # 1. Delete existing submission
                MarketSessionSubmissionForecasts.objects.filter(
                    submission=submission
                ).delete()
                # 2. Add new submission:
                for forecast in forecasts_data:
                    MarketSessionSubmissionForecasts.objects.create(
                        submission=submission,
                        datetime=forecast["datetime"],
                        value=forecast["value"]
                    )
            return {
                "challenge_id": challenge_id,
                "submission_id": submission.id,
            }
        except Exception as e:
            logger.exception("Failed to insert submission.")
            raise market_exceptions.FailedToInsertSubmission() from e


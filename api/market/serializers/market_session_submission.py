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
logger = structlog.get_logger("api_logger")


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
        challenge_id = self.context.get('challenge_id')
        variable_id = attrs["variable"]
        attrs["challenge_id"] = challenge_id
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
        # 3) Check if user is sending forecasts for expected dates
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
        # 4) Check if the user fulfills the minimum historical
        # forecasts data for this challenge
        # 4.1) Users should have a minimum samples of historical forecasts
        # -- Past submissions historical data count:
        data_count_1 = MarketSessionSubmissionForecasts.objects.filter(
            submission__user_id=self.context.get('request').user.id,
            submission__variable=variable_id,
            submission__market_session_challenge__resource_id=challenge.resource_id,
        ).count()
        # -- Initial historical data count:
        data_count_2 = IndividualForecasts.objects.filter(
            user_id=self.context.get('request').user.id,
            variable=variable_id,
            resource_id=challenge.resource_id,
        ).count()
        if (
                data_count_1 + data_count_2) < settings.MIN_RAW_DATA_COUNT_TO_CHALLENGE:
            raise market_exceptions.NotEnoughDataToSubmit(
                resource_id=challenge.resource_id,
                min_data_count=settings.MIN_RAW_DATA_COUNT_TO_CHALLENGE
            )

        # 4.2) Users should have forecasts for all the timestamps of the
        #  previous day:
        # -- Get the previous day:
        previous_day = challenge.target_day - pd.Timedelta(days=1)
        # Prev day start / end datetimes:
        # Create start / end datetime for the forecast (local tz):
        start_datetime = dt.datetime.combine(previous_day, dt.time(0, 0, 0))  # noqa
        if settings.FORECAST_TIME_RESOLUTION_MINUTES == 15:
            end_datetime = dt.datetime.combine(previous_day, dt.time(23, 45, 0))  # noqa
        elif settings.FORECAST_TIME_RESOLUTION_MINUTES == 60:
            end_datetime = dt.datetime.combine(previous_day, dt.time(23, 0, 0))  # noqa
        else:
            raise ValueError("Invalid FORECAST_TIME_RESOLUTION_MINUTES value. "
                             "Please contact the developers.")
        # Localize to resource timezone:
        resource_tz = pytz.timezone(challenge.resource.timezone)
        start_datetime = resource_tz.localize(start_datetime)
        end_datetime = resource_tz.localize(end_datetime)
        # Convert localized dt objects to UTC:
        start_datetime = start_datetime.astimezone(pytz.utc)
        end_datetime = end_datetime.astimezone(pytz.utc)
        # Get range of expected timestamps:
        expected_prev_day_ts = pd.date_range(
            start=start_datetime,
            end=end_datetime,
            freq=f'{settings.FORECAST_TIME_RESOLUTION_MINUTES}T',
            tz="utc"
        )
        expected_prev_day_ts = [x.strftime("%Y-%m-%dT%H:%M:%SZ")
                                for x in expected_prev_day_ts]
        # -- Attempt to get prev day forecasts from previous challenge
        prev_day_ts_1 = MarketSessionSubmissionForecasts.objects.filter(
            submission__user_id=self.context.get('request').user.id,
            submission__variable=variable_id,
            submission__market_session_challenge__target_day=previous_day,
        ).values_list('datetime', flat=True)

        prev_day_ts_2 = []
        if len(prev_day_ts_1) < len(expected_prev_day_ts):
            # -- Attempt to get the count of previous day forecasts from
            # initial historical upload table
            prev_day_ts_2 = IndividualForecasts.objects.filter(
                user_id=self.context.get('request').user.id,
                variable=variable_id,
                resource_id=challenge.resource_id,
                datetime__gte=start_datetime,
                datetime__lte=end_datetime,
            ).values_list('datetime', flat=True)
        # -- Concatenate both lists:
        prev_day_ts = list(set(list(prev_day_ts_1) + list(prev_day_ts_2)))
        prev_day_ts = [x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in prev_day_ts]
        # -- Check if expected dates exist on DB:
        missing_leadtimes = [x for x in expected_prev_day_ts
                             if x not in prev_day_ts]
        if len(missing_leadtimes) > 0:
            raise market_exceptions.NotEnoughPreviousDayDataToSubmit(
                resource_id=challenge.resource_id,
                time_resolution=settings.FORECAST_TIME_RESOLUTION_MINUTES
            )
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


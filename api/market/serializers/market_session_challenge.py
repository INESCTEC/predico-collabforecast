import pytz
import datetime as dt

from django.conf import settings
from rest_framework import serializers

from users.models import (
    UserResources,
)
from data.models import (
    RawData,
)
from .. import exceptions as market_exceptions
from ..models.market_session import (
    MarketSession,
)
from ..models.market_session_challenge import (
    MarketSessionChallenge,
)


class MarketSessionChallengeRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSessionChallenge
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['resource_name'] = instance.resource.name  # noqa
        return rep


class MarketSessionChallengeCreateSerializer(serializers.Serializer):
    market_session = serializers.IntegerField(
        required=True,
        allow_null=False,
    )
    resource = serializers.UUIDField(
        required=True,
        allow_null=False,
    )
    use_case = serializers.ChoiceField(
        choices=MarketSessionChallenge.UseCase,
        required=True,
        allow_null=False,
        allow_blank=False
    )

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        resource_id = attrs["resource"]
        market_session_id = attrs["market_session"]

        try:
            # Get resource data:
            resource = UserResources.objects.get(id=resource_id,
                                                 user_id=user.id)
            attrs["resource_data"] = resource
        except UserResources.DoesNotExist as ex:
            raise market_exceptions.UserResourceNotRegistered(
                user=user,
                resource_id=resource_id,
            ) from ex

        try:
            # Get market session data:
            market_session = MarketSession.objects.get(id=market_session_id)
        except MarketSession.DoesNotExist as ex:
            raise market_exceptions.NoMarketSession(
                market_session_id=market_session_id
            ) from ex

        # Session status must be OPEN to accept bids:
        if market_session.status != MarketSession.MarketStatus.OPEN:
            raise market_exceptions.SessionNotOpenForChallenges(
                market_session_id=market_session_id
            )
        else:
            attrs["market_session_open_ts"] = market_session.open_ts

        # Check if a challenge for this user_id/market_session_id/resource_id
        # already exists:
        if MarketSessionChallenge.objects.filter(
                user_id=user.id,
                market_session_id=market_session_id,
                resource_id=resource_id,
        ):
            raise market_exceptions.ChallengeAlreadyExists(
                market_session_id=market_session_id,
                resource_id=resource_id
            )

        # Check if this resource has more than 1 month of raw data available:
        data_count = RawData.objects.filter(
            user_id=user.id,
            resource_id=resource_id,
        ).count()

        if data_count < settings.MIN_RAW_DATA_COUNT_TO_CHALLENGE:
            raise market_exceptions.NotEnoughDataToChallenge(
                resource_id=resource_id,
                min_data_count=settings.MIN_RAW_DATA_COUNT_TO_CHALLENGE
            )

        return attrs

    def create(self, validated_data):
        # user info:
        user = self.context.get('request').user
        # session info:
        user_id = user.id
        market_session_id = validated_data["market_session"]
        resource_id = validated_data["resource"]
        use_case = validated_data["use_case"]
        resource_tz = pytz.timezone(validated_data["resource_data"].timezone)
        open_date = validated_data["market_session_open_ts"].date()
        day_ahead = open_date + dt.timedelta(days=1)

        # Create start / end datetime for the forecast (local tz):
        start_datetime = dt.datetime.combine(day_ahead, dt.time(0, 0, 0))
        if settings.FORECAST_TIME_RESOLUTION_MINUTES == 15:
            end_datetime = dt.datetime.combine(day_ahead, dt.time(23, 45, 0))
        elif settings.FORECAST_TIME_RESOLUTION_MINUTES == 60:
            end_datetime = dt.datetime.combine(day_ahead, dt.time(23, 0, 0))
        else:
            raise ValueError("Invalid FORECAST_TIME_RESOLUTION_MINUTES value. "
                             "Please contact the developers.")
        # Localize to resource timezone:
        start_datetime = resource_tz.localize(start_datetime)
        end_datetime = resource_tz.localize(end_datetime)
        # Convert localized dt objects to UTC:
        start_datetime = start_datetime.astimezone(pytz.utc)
        end_datetime = end_datetime.astimezone(pytz.utc)

        # Register Challenge:
        challenge = MarketSessionChallenge.objects.create(
            user_id=user_id,
            market_session_id=market_session_id,
            resource_id=resource_id,
            use_case=use_case,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            target_day=day_ahead,
        )

        return {
            "id": challenge.id,
            "user": user_id,
            "market_session": market_session_id,
            "resource": resource_id,
            "use_case": use_case,
            "forecast_start_datetime": start_datetime,
            "forecast_end_datetime": end_datetime,
        }


class MarketSessionChallengeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSessionChallenge
        exclude = ["user"]
        extra_kwargs = {
            'resource': {'required': False},
            'use_case': {'required': False},
            'start_datetime': {'required': False},
            'end_datetime': {'required': False},
        }

    def validate(self, attrs):
        """
        Check if market session is open
        :param attrs:
        :return:
        """
        request = self.context.get('request')
        challenge_id = self.context.get('challenge_id')
        user = request.user

        # Attempt to fetch the bid and its associated market session
        # with a single query
        try:
            challenge = (MarketSessionChallenge.objects.
                         select_related('market_session').
                         get(id=challenge_id))

            # Ensure the market session is open
            if challenge.market_session.status != MarketSession.MarketStatus.OPEN:
                raise market_exceptions.SessionNotOpenForChallenges(
                    market_session_id=challenge.market_session.id
                )

        except MarketSessionChallenge.DoesNotExist as ex:
            raise market_exceptions.UserChallengeNotRegistered(
                user=user,
                challenge_id=challenge_id
            ) from ex

        return attrs

    def update(self, instance, validated_data):
        utc_now_ = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        validated_data["updated_at"] = utc_now_
        return super().update(instance, validated_data)


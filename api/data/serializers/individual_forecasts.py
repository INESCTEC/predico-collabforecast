import pandas as pd
import datetime as dt

from django.db import connection
from rest_framework import serializers

from users.models import UserResources
from market.models.market_session_submission import (
    MarketSessionSubmission,
    MarketSessionSubmissionForecasts
)
from ..models.individual_forecasts import IndividualForecasts
from ..helpers.sql import to_sql_update
from .. import exceptions as data_exceptions


class IndividualForecastsRetrieveSerializer(serializers.ModelSerializer):
    variable = serializers.ReadOnlyField(
        source='submission.variable'
    )
    market_session = serializers.ReadOnlyField(
        source='submission.market_session_challenge.market_session_id'
    )
    challenge = serializers.ReadOnlyField(
        source='submission.market_session_challenge.id'
    )

    class Meta:
        model = MarketSessionSubmissionForecasts
        fields = ["datetime", "variable", "value", "market_session",
                  "challenge", "registered_at"]


class IndividualForecastsHistoricalRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndividualForecasts
        fields = ["datetime", "launch_time", "variable", "value", "registered_at"]


class IndividualForecastsHistoricalCreateSerializer(serializers.Serializer):
    class IndividualForecastsFieldSerializer(serializers.Serializer):
        datetime = serializers.DateTimeField(required=True,
                                             allow_null=False)
        value = serializers.FloatField(required=True,
                                       allow_null=False)

    forecasts = IndividualForecastsFieldSerializer(many=True,
                                                   required=True,
                                                   allow_null=False)
    resource = serializers.UUIDField(
        required=True,
        allow_null=False,
    )
    variable = serializers.ChoiceField(
        choices=MarketSessionSubmission.ForecastsVariable.choices,
        required=True,
        allow_null=False,
    )
    launch_time = serializers.DateTimeField(required=True,
                                            allow_null=False)

    def validate(self, attrs):
        request = self.context.get('request')
        resource_id = attrs["resource"]
        if not UserResources.objects.filter(id=resource_id).exists():
            raise data_exceptions.ForecastResourceNotAssigned(
                resource_name=resource_id
            )
        attrs["user_id"] = request.user.id
        return attrs

    def create(self, validated_data):
        user_id = validated_data["user_id"]
        variable_id = validated_data["variable"]
        resource_id = validated_data["resource"]
        launch_time = validated_data["launch_time"]
        # Get timeseries info:
        data = pd.DataFrame(validated_data["forecasts"])
        # Get resource info:
        data["user_id"] = user_id
        data["resource_id"] = resource_id
        data["variable"] = variable_id
        data["launch_time"] = launch_time
        # Include new cols in timeseries:
        data["registered_at"] = dt.datetime.utcnow()
        msg = to_sql_update(
            conn=connection,
            df=data,
            table=IndividualForecasts._meta.db_table,
            constraint_columns=[
                "user_id",
                "resource_id",
                "variable",
                "datetime"
            ],
        )
        return {"status": "ok", "message": msg}

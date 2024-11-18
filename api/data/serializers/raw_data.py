import pandas as pd
import datetime as dt

from django.db import connection
from rest_framework import serializers

from users.models import UserResources

from .. import exceptions as data_exceptions
from ..models.raw_data import RawData
from ..helpers.sql import to_sql_update


class RawDataRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawData
        fields = ["datetime",
                  "value",
                  "units",
                  "resource",
                  "registered_at"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['resource_name'] = instance.resource.name
        return rep


class RawDataCreateSerializer(serializers.Serializer):
    class RawDataFieldSerializer(serializers.Serializer):
        datetime = serializers.DateTimeField(required=True,
                                             allow_null=False)
        value = serializers.FloatField(required=True,
                                       allow_null=False)

    timeseries = RawDataFieldSerializer(many=True,
                                        required=True,
                                        allow_null=False)
    resource = serializers.UUIDField(
        required=True,
        allow_null=False,
    )
    units = serializers.ChoiceField(
        required=True,
        allow_null=False,
        choices=RawData.RawDataUnits
    )

    def validate(self, attrs):
        request = self.context.get('request')
        resource_id = attrs["resource"]

        if not UserResources.objects.filter(id=resource_id, user_id=request.user.id).exists():  # noqa
            raise data_exceptions.RawResourceNotAssigned(
                resource_id=resource_id
            )
        attrs["user_id"] = request.user.id
        return attrs

    def create(self, validated_data):
        # Get timeseries info:
        data = pd.DataFrame(validated_data["timeseries"])
        # Get resource info:
        data["user_id"] = validated_data["user_id"]
        data["resource_id"] = validated_data["resource"]
        # Include new cols in timeseries:
        data["units"] = validated_data["units"]
        data["registered_at"] = dt.datetime.utcnow()
        msg = to_sql_update(
            conn=connection,
            df=data,
            table=RawData._meta.db_table,
            constraint_columns=[
                "user_id",
                "resource_id",
                "datetime"
            ],
        )
        return {"status": "ok", "message": msg}

import datetime as dt

from rest_framework import serializers

from data.models.raw_data import RawData

from ..util.validators import ResourceNameValidator
from ..models.user_resources import UserResources


class UserResourcesRetrieveSerializer(serializers.ModelSerializer):
    measurements_n_samples = serializers.IntegerField(read_only=True)
    measurements_start = serializers.DateTimeField(read_only=True)
    measurements_end = serializers.DateTimeField(read_only=True)
    measurements_last_update = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserResources
        exclude = []

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        count_measurement = RawData.objects.filter(resource_id=instance.id).count()
        first_measurement = RawData.objects.filter(resource_id=instance.id).order_by('datetime').first()
        last_measurement = RawData.objects.filter(resource_id=instance.id).order_by('datetime').last()
        last_update = RawData.objects.filter(resource_id=instance.id).order_by('registered_at').last()
        representation["measurements_metadata"] = {
            "n_samples": count_measurement,
            "start_datetime": first_measurement.datetime if first_measurement else None,
            "end_datetime": last_measurement.datetime if last_measurement else None,
            "last_update": last_update.registered_at if last_update else None,
        }
        return representation


class UserResourcesUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserResources
        exclude = []
        extra_kwargs = {
            'name': {'required': True,
                     'validators': [ResourceNameValidator]},
        }

    def validate_name(self, value):
        user_id = self.context.get('request').user.id
        if UserResources.objects.filter(user=user_id, name=value).exists():
            raise serializers.ValidationError(
                f"Resource '{value}' is already registered."
            )
        return value

    def validate(self, attrs):
        return attrs

    def update(self, instance, validated_data):
        utc_now_ = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        validated_data["updated_at"] = utc_now_
        return super().update(instance, validated_data)


class UserResourcesCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for UserResources create method.
    Note: This is used just to avoid having the "user" field as example
    in the Swagger documentation (for POST requests)
    """
    class Meta(UserResourcesUpdateSerializer.Meta):
        exclude = ['user']

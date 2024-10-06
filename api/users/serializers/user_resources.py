import datetime as dt

from rest_framework import serializers

from ..util.validators import ResourceNameValidator
from ..models.user_resources import UserResources


class UserResourcesSerializer(serializers.ModelSerializer):

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
    class Meta(UserResourcesSerializer.Meta):
        exclude = ['user']

from users.models.user_notification import (
    UserNotification,
    UserNotificationType
)
from rest_framework import serializers
from difflib import SequenceMatcher


class UserNotificationSerializer(serializers.ModelSerializer):
    notification_type_name = serializers.CharField(source='notification_type.name')

    class Meta:
        model = UserNotification
        fields = ['id', 'state', 'notification_type_name',
                  'notification_title', 'notification_description']


class UserNotificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationType
        fields = ('id', 'name')

    @staticmethod
    def validate_name(value):
        similar_events = UserNotificationType.objects.all()
        for event in similar_events:
            ratio = SequenceMatcher(None, event.name, value).ratio()
            if ratio >= 0.7:
                raise serializers.ValidationError(
                    "Similar notification event already exists")
        return value


class UserGetNotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    notification_type = serializers.StringRelatedField(source='notification_type.name')

    class Meta:
        model = UserNotification
        fields = [
            'id',
            'user',
            'notification_title',
            'notification_description',
            'notification_type',
            'state',
        ]


class UserUpdateNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = ['state']
        extra_kwargs = {
            'state': {'required': True}
        }


class UserPostNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = '__all__'

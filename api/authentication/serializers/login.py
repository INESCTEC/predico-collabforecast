from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name

        return token

    def validate(self, attrs):
        email = attrs['email'].lower().strip()
        user = authenticate(username=email, password=attrs['password'].strip())

        if not user:
            raise serializers.ValidationError('Invalid login credentials.')

        if not user.is_verified:
            raise serializers.ValidationError('Email not verified.')

        return super().validate(attrs)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

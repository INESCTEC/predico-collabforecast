
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class AdminTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Authenticate the user
        user = authenticate(request=self.context.get('request'),
                            email=email,
                            password=password)

        if not user or not user.is_active:
            raise serializers.ValidationError('Invalid credentials.')

        if not user.is_superuser:
            raise serializers.ValidationError('Access denied. '
                                              'You are not authorized to sign in.')

        # Create refresh and access tokens
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token), # noqa
        }

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
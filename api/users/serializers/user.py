import structlog
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from api.email.utils.email_utils import send_email_as_thread
from users.exceptions.Exception import EmailAlreadyExists
from users.models.user import OneTimeToken
from users.util.verification import check_one_time_token
from ..models.user import User

logger = structlog.get_logger("api_logger")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email',
                  'date_joined', 'last_login', 'is_active', 
                  'is_superuser', 'is_verified']


class LimitedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email',
                  'date_joined', 'last_login']


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(label="password", write_only=True,
                                     required=True)
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)

    @staticmethod
    def validate_email(email):
        validate_email(email)
        email = email.lower()
        email_exists = User.objects.filter(email=email).first()
        if email_exists:
            raise EmailAlreadyExists(email)
        return email

    @staticmethod
    def validate_password(password):
        validate_password(password)
        return password

    def create(self, validated_data):

        user_model = get_user_model()
        user = user_model.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name')
        )
        user.is_verified = False

        # User is not verified by default and account verification step is
        # needed -- should always be used in production mode
        if not settings.ACCOUNT_VERIFICATION:
            # User is not verified by default and account verification step is
            # needed -- can be activated or not in debug mode
            user.is_verified = True

        user.save()

        return user

    def update(self, instance, validated_data):
        pass


class SecurityLinkSerializer(serializers.Serializer):
    """
    serialize and validate new security link for
    email verification or password reset
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(label="password", write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        try:
            validate_email(email)
        except ValidationError as ex:
            raise ValidationError("Invalid email address") from ex

        user = authenticate(username=email, password=attrs['password'].strip())
        if not user:
            raise serializers.ValidationError('Invalid credentials.')

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    uidb64 = serializers.CharField(max_length=68)
    token = serializers.CharField()

    class Meta:
        fields = ['password', 'uidb64', 'token']

    def validate(self, attrs):
        try:
            uidb64 = attrs.get('uidb64')
            token = attrs.get('token')

            check_one_time_token(token)

            user_id = force_str(urlsafe_base64_decode(uidb64))
            User.objects.get(id=user_id)

            # Check the token
            UntypedToken(token)

        except (ValidationError, TokenError, User.DoesNotExist) as ex:
            raise ValidationError({'token': 'Invalid token'}) from ex

        return attrs

    def save(self):
        password = self.validated_data.get('password')
        uidb64 = self.validated_data.get('uidb64')
        token = self.validated_data.get('token')

        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=user_id)
        one_time_token = OneTimeToken.objects.get(token=token)
        user.set_password(password)
        user.save()
        one_time_token.used = True
        one_time_token.save()

        send_email_as_thread(
            destination=[user.email],
            email_opt_key="password-reset-success",
            fail_silently=True,
            format_args={}
        )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

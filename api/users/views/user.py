from datetime import timedelta

import jwt
import structlog
from django.conf import settings
# from django.contrib.auth.models import User
# from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, UntypedToken
from stronghold.decorators import public
from django.shortcuts import render

# cannot use django.conf.settings the "DEBUG" flag in settings.base is
# updated depending on the environment
from api.settings.base import DEBUG
from api.email.utils.email_utils import send_email_as_thread
from api.renderers.CustomRenderer import CustomRenderer
from users.models.user import OneTimeToken, User
from users.notifications.notification_data import create_user_notifications
from users.schemas.responses import *
from users.util.verification import (check_one_time_token,
                                     create_verification_info,
                                     send_verification_email)
from ..serializers.user import (ResetPasswordEmailRequestSerializer,
                                UserRegistrationSerializer,
                                UserSerializer,
                                PasswordResetRequestSerializer,
                                LimitedUserSerializer)

# init logger:
logger = structlog.get_logger("api_logger")


class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '100/day'


class UserRegisterView(APIView):
    renderer_classes = (CustomRenderer,)
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_summary="User registration",
        operation_id="post_user_register",
        operation_description="[Public] Method for new agent registration. "
                              "An email is issued with validation link upon "
                              "registration.",
        request_body=UserRegistrationSerializer,
        responses={
            201: UserRegisterResponse["POST"],
            400: 'Bad request',
            409: UserRegisterResponse["POST_conflict"],
            500: "Internal Server Error",
        })
    @method_decorator(public)
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Save the user
                user = serializer.save()
                # Create user notifications
                create_user_notifications(user=user)

        except Exception as e:
            logger.exception("Transaction failed while creating the user", exc_info=e)
            return Response({'message': 'An error occurred while '
                                        'registering the user. '
                                        'Contact the platform for more '
                                        'details if the problem persists'},
                            status=status.HTTP_400_BAD_REQUEST)

        if settings.ACCOUNT_VERIFICATION:
            # Prepare verification info:
            verification_link, uid = create_verification_info(request)
            email = request.data.get('email')
            send_verification_email(email, verification_link)
            response = {"email": email}
            if DEBUG:
                # Include verification link while in debug mode to
                # facilitate tests. Note that debug mode is activated
                # if environment is set to "test" or "develop"
                response["verification_link"] = verification_link
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"message": "User registered successfully."},
                status=status.HTTP_201_CREATED)


class UserListView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_summary="List user details",
        operation_id="get_user_list",
        operation_description="List registered user(s) details",
        responses={
            200: UserListResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        if request.user.is_superuser:
            users = User.objects.all()
            serializer = self.serializer_class(users, many=True)
            return Response(serializer.data)
        else:
            serializer = LimitedUserSerializer(request.user)
            return Response(serializer.data)


class UserVerifyEmailView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (AllowAny,)

    @staticmethod
    def get(request, uid, token):
        try:
            # Decode JWT:
            payload = jwt.decode(token,
                                 settings.SECRET_KEY,
                                 algorithms=['HS256'])

            # Get user by email:
            user = User.objects.get(email=payload["email"])
            # Retrieve email encoded in url (assure that user making
            # registration is the same as the one validating)
            email = force_str(urlsafe_base64_decode(uid))

            # If user exists & email is correct validate:
            if (user is not None) and (email == payload['email']):
                if user.is_verified:
                    # if user already verified, ignore
                    return Response(data={
                        'response': 'User is already verified'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Activate / verify user:
                user.is_active = True
                user.is_verified = True
                user.save()

                # Get updated auth token:
                refresh_token = RefreshToken.for_user(user)

                # Send email:
                if settings.ENVIRONMENT == "production":
                    send_email_as_thread(
                        destination=[email],
                        email_opt_key="email-verification-success",
                        format_args={"token": refresh_token},
                        fail_silently=True
                    )

                return render(request, 'email_verification_success.html')  # noqa
                # return Response(
                #     {
                #         'authentication': {
                #             'access_token': str(refresh_token.access_token),
                #             'refresh_token': str(refresh_token)
                #         },
                #         'user': UserSerializer(user).data,
                #     },
                #     status=status.HTTP_200_OK
                # )
            else:
                return Response({'message': 'Invalid activation link.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except jwt.ExpiredSignatureError:
            return Response({'message': 'Validation token has expired.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({'message': 'Validation token is invalid.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message': 'User does not exist.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError):
            return Response({'message': 'An error occurred, please retry'},
                            status=status.HTTP_400_BAD_REQUEST)


class RequestPasswordResetEmail(APIView):
    throttle_classes = [CustomAnonRateThrottle]
    serializer_class = PasswordResetRequestSerializer

    @swagger_auto_schema(
        operation_id="post_request_password_reset_email",
        operation_description="Method for user to request password reset "
                              "for their account email.",
        request_body=PasswordResetRequestSerializer,
        responses={
            400: 'Bad request',
            500: "Internal Server Error",
        })
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = self.request.data.get('email')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = str(RefreshToken.for_user(user).access_token)
            # create OneTimeToken
            OneTimeToken.objects.create(
                user=user,
                token=token,
                expiration_time=timezone.now() + timedelta(hours=1)
            )
            # current_site = get_current_site(request=request).domain
            relative_link = uidb64 + "/" + token
            reset_link = 'predico://reset/' + relative_link
            # password - reset - success
            send_email_as_thread(
                destination=[email],
                email_opt_key="password-reset-verification",
                format_args={"link": reset_link},
                fail_silently=True
            )

        return Response({'success': 'If your email exists on the '
                                    'system an email has been sent to you'},
                        status=status.HTTP_200_OK)


class PasswordTokenCheck(APIView):
    throttle_classes = [CustomAnonRateThrottle]

    @staticmethod
    def get(request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            User.objects.get(id=user_id)

            # This will raise a TokenError if the token is invalid
            UntypedToken(token)
            check_one_time_token(token)

            one_time_token = OneTimeToken.objects.get(token=token)

            if one_time_token.used:
                return Response({'error': 'Token has already been used'},
                                status=status.HTTP_400_BAD_REQUEST)
            if one_time_token.expiration_time < timezone.now():
                raise ValidationError({'token': 'Token has expired'})

            return Response({'success': True,
                             'message': 'Credentials Valid',
                             'uidb64': uidb64, 'token': token},
                            status=status.HTTP_200_OK)

        except (TokenError, User.DoesNotExist, ValidationError):
            return Response({'error': 'Token is not valid'},
                            status=status.HTTP_400_BAD_REQUEST)

        except UnicodeDecodeError:
            return Response({'error': 'Token is not valid, please request a new one'},
                            status=status.HTTP_401_UNAUTHORIZED)


class SetNewPassword(APIView):
    throttle_classes = [CustomAnonRateThrottle]
    serializer_class = ResetPasswordEmailRequestSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': True,
                         'message': 'Password reset success'},
                        status=status.HTTP_200_OK)


class TestEndpointView(APIView):

    @staticmethod
    def get(request, format=None):
        message = {'message': 'Welcome to Predico!'}
        return Response(message)

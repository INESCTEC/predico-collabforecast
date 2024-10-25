import uuid

import jwt
import structlog
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
# from django.contrib.auth.models import User
# from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, UntypedToken

from api.email.utils.email_utils import send_email_as_thread
from api.renderers.CustomRenderer import CustomRenderer
from api.settings.base import DEBUG
from users.models.user import OneTimeToken, User, OneTimeRegisterToken
from users.schemas.responses import *
# cannot use django.conf.settings the "DEBUG" flag in settings.base is
# updated depending on the environment
from users.util.verification import IsValidRegisterToken, send_registration_email
from users.util.verification import (check_one_time_token,
                                     create_verification_info,
                                     send_verification_email)
from ..serializers.user import (ResetPasswordEmailRequestSerializer,
                                UserRegistrationSerializer,
                                UserSerializer,
                                LimitedUserSerializer,
                                TokenVerifySerializer,
                                TokenVerificationResponseSerializer,
                                UserInvitationSerializer)

# init logger:
logger = structlog.get_logger("api_logger")


class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '100/day'


class UserByTokenView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):

        try:
            user = User.objects.get(email=request.user)
            serializer = self.serializer_class(user)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except OneTimeToken.DoesNotExist:
            return Response({'error': 'Invalid token.'},
                            status=status.HTTP_404_NOT_FOUND)


class GenerateRegisterTokenView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserInvitationSerializer

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        # Validate the incoming data using the serializer
        if serializer.is_valid():
            token = str(uuid.uuid4())
            expiration_time = timezone.now() + timezone.timedelta(hours=72)

            # check if the email exists in the database
            email = serializer.validated_data.get('email')
            if User.objects.filter(email=email).exists():
                return Response({'error': 'User with this email already exists'},
                                status=status.HTTP_409_CONFLICT)

            try:
                with transaction.atomic():  # Start atomic transaction
                    # Create the OneTimeRegisterToken object
                    OneTimeRegisterToken.objects.create(token=token,
                                                        expiration_time=expiration_time)

                    # Use reverse to dynamically generate the link
                    link = f"{settings.FRONTEND_URL}/signup/{token}"
                    email = serializer.validated_data.get('email')
                    # Send the registration email
                    send_registration_email(email, link)

                    # Return the link to the admin user
                    return Response({'link': link}, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Handle any exceptions that occur
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # If the data is invalid, return the validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    """
    API View for verifying user emails via token.
    """
    @swagger_auto_schema(
        operation_summary="Email verification",
        operation_id="get_verify_email",
        operation_description="[Public] Method for verifying user's email with the token.",
        responses={
            200: 'Email verified successfully',
            400: 'Bad request or token is invalid',
        })
    def get(self, request, uidb64, token):
        try:
            # Decode the user ID from the URL
            uid = urlsafe_base64_decode(uidb64).decode()

            # Fetch the user associated with the UID
            user = get_object_or_404(User, pk=uid)

            # Verify the token using Django's token generator
            if default_token_generator.check_token(user, token):
                # If the token is valid, activate the user
                user.is_active = True
                user.save()

                return Response(
                    {"message": "Email verified successfully. You can now sign in."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "Invalid or expired verification token."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"message": "Invalid or expired verification token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserRegisterView(APIView):
    renderer_classes = (CustomRenderer,)
    serializer_class = UserRegistrationSerializer
    authentication_classes = []  # No authentication for this view
    permission_classes = (IsValidRegisterToken,)

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
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Save the user
                serializer.save()
                # If all is successful, mark the token as used here
                one_time_register_token = OneTimeRegisterToken.objects.get(
                    token=request.headers.get('Authorization')[7:],
                    used=False)

                one_time_register_token.used = True
                one_time_register_token.save()

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
    def get(request):
        try:
            uid = request.query_params.get('uid')
            token = request.query_params.get('token')
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

                return Response(status=status.HTTP_200_OK)

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
    def get(request):
        message = {'message': 'Welcome to Predico!'}
        return Response(message)

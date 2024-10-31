from datetime import timedelta

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.email.utils.email_utils import send_email_as_thread
from users.models import User, PasswordResetRequest
from users.serializers.user_reset_password import PasswordResetSerializer


class PasswordResetRequestView(APIView):
    schema = None  # This removes the endpoint from Swagger and other docs

    @staticmethod
    def post(request):
        email = request.data.get('email')

        # Check rate limiting: limit to 3 requests per day
        # (or whatever is set in settings)
        one_day_ago = timezone.now() - timedelta(days=1)
        recent_requests = PasswordResetRequest.objects.filter(
            email=email,
            created_at__gte=one_day_ago  # Only count requests from the last 24 hours
        ).count()

        if recent_requests >= settings.PASSWORD_RESET_RATE_LIMIT:
            return Response({'detail': 'Too many requests. Please try again later.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Do not reveal if the email exists or not
        user = User.objects.filter(email=email).first()
        if user:
            # Generate password reset token
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)

            # Save the password reset request to prevent too many requests
            PasswordResetRequest.objects.create(email=email, token=token)

            # Send password reset email with secure token
            reset_link = f"{settings.FRONTEND_URL}/set-password/{token}"
            send_email_as_thread(
                destination=[email],
                email_opt_key="password-reset-verification",
                format_args={'link': reset_link}
            )

        # Always respond with the same message to avoid disclosing email existence
        return Response({'detail': 'If the email is registered, '
                                   'you will receive a password reset link.'},
                        status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    schema = None
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            # Find the password reset request
            reset_request = PasswordResetRequest.objects.filter(token=token).first()
            if not reset_request:
                return Response({'detail': 'Invalid or expired token'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Get the user
            user = User.objects.filter(email=reset_request.email).first()
            if user:
                token_generator = PasswordResetTokenGenerator()
                if token_generator.check_token(user, token):
                    user.set_password(new_password)
                    user.save()
                    # Invalidate the token by deleting the reset request
                    reset_request.delete()
                    return Response({'detail': 'Password has been reset successfully.'},
                                    status=status.HTTP_200_OK)

            return Response({'detail': 'User not found or invalid token'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            # Return the validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

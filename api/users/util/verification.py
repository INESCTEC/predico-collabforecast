import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

import jwt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.permissions import BasePermission

from api.email.utils.email_utils import send_email_as_thread
from users.models.user import OneTimeToken, OneTimeRegisterToken


class IsValidRegisterToken(BasePermission):

    def has_permission(self, request, view):

        token = request.headers.get('Authorization')
        if not token:
            return False

        if token.startswith("Bearer "):
            token = token[7:]

        try:
            # Try fetching the token from the database
            one_time_token = OneTimeRegisterToken.objects.get(token=token, used=False)
        except OneTimeRegisterToken.DoesNotExist:
            return False

        # Check if the token has expired
        if one_time_token.expiration_time < timezone.now():
            return False

        return True


def check_one_time_token(token):
    try:
        one_time_token = OneTimeToken.objects.get(token=token)

        if one_time_token.used:
            raise ValidationError({'token': 'Token has already been used'})

        if one_time_token.expiration_time < timezone.now():
            raise ValidationError({'token': 'Token has expired'})

        return one_time_token.user

    except (ValidationError, ValueError, OverflowError, OneTimeToken.DoesNotExist) as ex:  # noqa
        raise ValidationError({'token': 'Invalid token'}) from ex

def send_registration_email(email, registration_link):
    if settings.ENVIRONMENT == "production":
        send_email_as_thread(
            destination=[email],
            email_opt_key="registration",
            format_args={"link": registration_link},
            fail_silently=False
        )
def send_verification_email(email, verification_link):
    if settings.ENVIRONMENT == "production":
        send_email_as_thread(
            destination=[email],
            email_opt_key="email-verification",
            format_args={"link": verification_link},
            fail_silently=False
        )


def create_verification_info(request):
    token, host, port, protocol, uid = account_url_metadata(request)
    base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return f"{base_url}/email-verification/{uid}/{token}", uid


def generate_token(email):
    date_ref = datetime.utcnow() + timedelta(days=1)

    token = jwt.encode({
        'email': email,
        'exp': int(date_ref.strftime('%H%M%S%f'))
    }, settings.SECRET_KEY, algorithm='HS256')

    if isinstance(token, bytes):
        return token.decode('utf-8')

    return token


def extract_url_components(url):
    parsed_url = urlparse(url)
    protocol = parsed_url.scheme
    host = parsed_url.netloc.split(':')[0]  # Extract host from netloc
    # Default ports for HTTP and HTTPS
    port = parsed_url.port if parsed_url.port \
        else (80 if protocol == 'http' else 443)
    return protocol, host, port


def account_url_metadata(request):
    email = request.data.get('email')
    token = generate_token(email)
    uid = urlsafe_base64_encode(force_bytes(email))
    protocol, host, port = extract_url_components(settings.SWAGGER_BASE_URL)
    return token, host, port, protocol, uid


def create_verification_link(host, port, protocol, uid, token):
    # Prepare verification link:
    verification_path = reverse("user:verify-email",
                                kwargs={
                                    'uid': uid,
                                    'token': token
                                })
    return f"{protocol}://{host}:{port}{verification_path}"

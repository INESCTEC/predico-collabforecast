import threading
from smtplib import SMTPException, SMTPConnectError, socket

import structlog
from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.core.mail import get_connection
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import exceptions

from .email_messages import EMAIL_OPTS, EMAIL_SIGNATURE

# init logger:
logger = structlog.get_logger("api_logger")


def send_email(destination,
               email_opt_key=None,
               format_args=None,
               connection=None):
    """
    This is a generic email function that can be used throughout
    the application
    """

    message = EMAIL_OPTS.get(email_opt_key)['message']
    context = {
        **(format_args if format_args is not None else {}),
        'message': message.format(**(format_args if format_args is not None else {})),  # noqa
        'email_signature': EMAIL_SIGNATURE
    }

    html_message = render_to_string('email_template.html', context)
    plain_message = strip_tags(html_message)
    subject = EMAIL_OPTS.get(email_opt_key)['subject']
    from_email = settings.EMAIL_HOST_USER

    # Preventing header injection
    if subject and message and from_email:
        try:
            send_mail(subject=subject,
                      message=plain_message,
                      from_email=from_email,
                      recipient_list=destination,
                      html_message=html_message,
                      connection=connection)

        except BadHeaderError:
            return HttpResponse('Invalid header found.')
    else:
        return HttpResponse('Make sure all fields are entered and valid.')


class EmailThread(threading.Thread):
    """
    Send emails on separate thread
    """
    def __init__(self,
                 destination,
                 email_opt_key,
                 format_args=None,
                 connection=None
                 ):
        self.destination = destination
        self.email_opt_key = email_opt_key
        self.format_args = format_args
        self.connection = connection
        threading.Thread.__init__(self)

    def run(self):
        send_email(
            destination=self.destination,
            email_opt_key=self.email_opt_key,
            format_args=self.format_args,
            connection=self.connection
        )


def send_email_as_thread(destination,
                         email_opt_key=None,
                         format_args=None,
                         fail_silently=False):

    # Attempt email connection. If it is unavailable inform user.
    try:
        connection = get_connection(
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            fail_silently=fail_silently
        )
        check_connection = connection.open()
    except (socket.error, SMTPConnectError, SMTPException) as ex:
        logger.exception("Failed to connect to email.")
        raise exceptions.APIException({
            'message': 'An error occurred while sending email, '
                       'please retry later.'
        }) from ex

    if check_connection:
        # Send email:
        EmailThread(
            destination=destination,
            email_opt_key=email_opt_key,
            format_args=format_args,
            connection=connection,
        ).start()
        # send_email(
        #     destination=destination,
        #     email_opt_key=email_opt_key,
        #     format_args=format_args,
        #     connection=connection,
        # )

import json
from celery import shared_task
from .utils.email_utils import send_email


@shared_task(queue="email")
def send_email_task(destination, email_opt_key, format_args):

    send_email(destination=[destination],
               email_opt_key=email_opt_key,
               format_args=format_args)

    return f"A email was sent to {destination} with the following key " \
           f"{email_opt_key} and args {json.dumps(format_args)}"

import uuid

from rest_framework import exceptions
from ..models import MarketSession, MarketSessionChallenge


def validate_query_params(
        market_session_id=None,
        resource_id=None,
        challenge_id=None,
        user_id=None,
        submission_id=None,
        market_session_status=None,
        confirmed=None,
        latest_only=None,
        pending_only=None,
        open_only=None,
        challenge_use_case=None
):
    if market_session_id is not None:
        try:
            int(market_session_id)
        except ValueError as ex:
            raise exceptions.ValidationError(
                {
                    "market_session": "Query param 'market_session' must be "
                                      "an integer."
                }
            ) from ex
    if user_id is not None:
        try:
            uuid.UUID(str(user_id))
        except ValueError as ex:
            raise exceptions.ValidationError(
                {
                    "user": "Query param 'user' must be a valid uuid."
                }
            ) from ex
    if resource_id is not None:
        try:
            uuid.UUID(resource_id)
        except ValueError as ex:
            raise exceptions.ValidationError(
                {
                    "resource": "Query param 'resource' must be a valid uuid."
                }
            ) from ex
    if challenge_id is not None:
        try:
            uuid.UUID(challenge_id)
        except ValueError as ex:
            raise exceptions.ValidationError(
                {
                    "challenge": "Query param 'challenge' must be a valid uuid."
                }
            ) from ex
    if submission_id is not None:
        try:
            uuid.UUID(submission_id)
        except ValueError as ex:
            raise exceptions.ValidationError(
                {
                    "submission": "Query param 'submission_id' must be a "
                                  "valid uuid."
                }
            ) from ex
    if market_session_status is not None:
        lbl = [x.lower() for x in MarketSession.MarketStatus.values]
        if market_session_status.lower() not in lbl:
            raise exceptions.ValidationError(
                {
                    "session_status": f"Query param 'session_status' must be "
                                      f"one of the following {lbl}"
                }
            )
    if challenge_use_case is not None:
        lbl = [x.lower() for x in MarketSessionChallenge.UseCase.values]
        if challenge_use_case.lower() not in lbl:
            raise exceptions.ValidationError(
                {
                    "use_case": f"Query param 'use_case' must be "
                                f"one of the following {lbl}"
                }
            )
    if ((confirmed is not None)
            and (confirmed.lower() not in ['true', 'false'])):
        raise exceptions.ValidationError(
            {
                "confirmed": "Query param 'confirmed' must be a boolean "
                             "(true/false)"
            }
        )

    if ((latest_only is not None)
            and (latest_only.lower() not in ['true', 'false'])):
        raise exceptions.ValidationError(
            {
                "latest_only": "Query param 'latest_only' must be a boolean "
                               "(true/false)"
            }
        )

    if ((open_only is not None)
            and (open_only.lower() not in ['true', 'false'])):
        raise exceptions.ValidationError(
            {
                "open_only": "Query param 'open_only' must be a boolean "
                             "(true/false)"
            }
        )

    if ((pending_only is not None)
            and (pending_only.lower() not in ['true', 'false'])):
        raise exceptions.ValidationError(
            {
                "pending_only": "Query param 'pending_only' must be a boolean "
                                "(true/false)"
            }
        )

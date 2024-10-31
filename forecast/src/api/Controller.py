import datetime as dt

from time import time

import requests.exceptions
from loguru import logger
from http import HTTPStatus

from conf import settings
from .Endpoint import *
from .RequestController import RequestController
from .exception.APIException import *


class Controller(RequestController):
    config = {
        "RESTAPI_PROTOCOL": settings.RESTAPI_PROTOCOL,
        "N_REQUEST_RETRIES": settings.N_REQUEST_RETRIES,
        "RESTAPI_HOST": settings.RESTAPI_HOST,
        "RESTAPI_PORT": settings.RESTAPI_PORT,
    }

    def __init__(self):
        RequestController.__init__(self, self.config)
        self.access_token = ""

    def __check_if_token_exists(self):
        if self.access_token is None:
            e_msg = "Access token is not yet available. Login first."
            logger.error(e_msg)
            raise ValueError(e_msg)

    def set_access_token(self, token):
        self.access_token = token

    def __request_template(self,
                           endpoint_cls: Endpoint,
                           log_msg: str,
                           exception_cls,
                           data: dict = None,
                           params: dict = None,
                           url_params: list = None,
                           ) -> dict:
        self.__check_if_token_exists()
        t0 = time()
        rsp = self.request(
            endpoint=endpoint_cls,
            data=data,
            params=params,
            url_params=url_params,
            auth_token=self.access_token)
        # -- Inspect response:
        if rsp.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]:
            logger.debug(f"{log_msg} ... Ok! ({time() - t0:.2f})")
            return rsp.json()
        elif rsp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            log_msg_ = f"{log_msg} ... Failed! ({time() - t0:.2f})"
            logger.error(log_msg_ + f"\n{rsp.content}")
            raise exception_cls(message=log_msg_,
                                errors={"message": "Internal Server Error."})
        else:
            log_msg_ = f"{log_msg} ... Failed! ({time() - t0:.2f})"
            logger.error(log_msg_ + f"\n{rsp.json()}")
            raise exception_cls(message=log_msg_, errors=rsp.json())

    def login(self, email: str, password: str):

        t0 = time()
        log_ = f"Logging in user {email}"

        payload = {
            "email": email,
            "password": password
        }
        rsp = self.request(
            endpoint=Endpoint(login.POST, login.uri),
            data=payload
        )

        if rsp.status_code == HTTPStatus.OK:
            logger.debug(f"{log_} ... Ok! ({time() - t0:.2f})")
            self.access_token = rsp.json()['access']
        elif rsp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            log_msg = f"{log_} ... Failed! ({time() - t0:.2f})"
            raise LoginException(message=log_msg,
                                 errors={"message": "Internal Server Error."})
        else:
            log_msg = f"{log_} ... Failed! ({time() - t0:.2f})"
            try:
                error_msg = rsp.json()
            except requests.exceptions.JSONDecodeError:
                error_msg = rsp.content
            logger.error(log_msg + f"\n{error_msg}")
            raise LoginException(message=log_msg, errors=error_msg)

    def list_users(self):
        response = self.__request_template(
            endpoint_cls=Endpoint(user_list.GET, user_list.uri),
            log_msg="Getting users",
            exception_cls=UserException
        )
        return response['data']

    def create_market_session(self):
        payload = {
            "status": "open"
        }
        response = self.__request_template(
            endpoint_cls=Endpoint(market_session.POST, market_session.uri),
            log_msg="Creating market session",
            data=payload,
            exception_cls=MarketSessionException
        )
        return response['data']

    def update_market_session(self, session_id: int, **kwargs):
        # prepare kwargs:
        if isinstance(kwargs.get("launch_ts", None), dt.datetime):
            kwargs["launch_ts"] = kwargs["launch_ts"].strftime("%Y-%m-%dT%H:%M:%S.%f")  # noqa
        if isinstance(kwargs.get("finish_ts", None), dt.datetime):
            kwargs["finish_ts"] = kwargs["finish_ts"].strftime("%Y-%m-%dT%H:%M:%S.%f")  # noqa
        if isinstance(kwargs.get("close_ts", None), dt.datetime):
            kwargs["close_ts"] = kwargs["close_ts"].strftime("%Y-%m-%dT%H:%M:%S.%f")  # noqa
        if isinstance(kwargs.get("open_ts", None), dt.datetime):
            kwargs["open_ts"] = kwargs["open_ts"].strftime("%Y-%m-%dT%H:%M:%S.%f")  # noqa
        # -- Perform Request:
        payload = {}
        payload.update(kwargs)
        response = self.__request_template(
            endpoint_cls=Endpoint(market_session.PATCH, market_session.uri),
            log_msg=f"Updating market session {session_id}",
            data=payload,
            url_params=[session_id],
            exception_cls=MarketSessionException
        )
        return response['data']

    def list_market_sessions(self, status=None):
        params = {}
        if status is not None:
            params["status"] = status
        response = self.__request_template(
            endpoint_cls=Endpoint(market_session.GET, market_session.uri),
            log_msg="Getting market sessions",
            params=params,
            exception_cls=MarketSessionException
        )
        return response['data']

    def list_last_session(self, status: str = None):
        params = {"latest_only": True}
        if status is not None:
            params["status"] = status
            msg = f"Getting last '{status}' market session"
        else:
            msg = "Getting last market session."

        response = self.__request_template(
            endpoint_cls=Endpoint(market_session.GET, market_session.uri),
            log_msg=msg,
            params=params,
            exception_cls=MarketSessionException
        )
        # Get sessions data - check if there are open sessions:
        sessions = response['data']
        if len(sessions) == 0:
            log_msg = "No market sessions available."
            logger.error(log_msg)
            raise NoMarketSessionException(message=log_msg,
                                           errors=response)
        else:
            return sessions[0]

    def list_challenges(self, session_id: int):
        params = {"market_session": session_id}
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge.GET, market_challenge.uri),
            log_msg=f"Listing challenges for session '{session_id}'",
            params=params,
            exception_cls=MarketSessionException
        )
        return response["data"]

    def list_challenges_without_weights(self):
        params = {"pending_only": True}
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_ensemble_weights.GET, market_challenge_ensemble_weights.uri),
            log_msg=f"Listing challenges without weights",
            params=params,
            exception_cls=MarketWeightsException
        )
        return response["data"]

    def list_challenges_submissions(self, challenge_id: int):
        params = {"challenge": challenge_id}
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_submissions.GET, market_challenge_submissions.uri),
            log_msg=f"Listing submissions for challenge '{challenge_id}'",
            params=params,
            exception_cls=MarketSessionException
        )
        return response["data"]

    def list_challenges_submissions_forecasts(self, user_id, resource_id):
        params = {"user": user_id, "resource": resource_id}
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_submissions_forecasts.GET, market_challenge_submissions_forecasts.uri),
            log_msg=f"Listing submissions from user {user_id} "
                    f"to resource {resource_id}",
            params=params,
            exception_cls=MarketSessionException
        )
        return response["data"]

    def list_user_resources(self, to_forecast=None):
        params = {}
        if to_forecast is not None:
            params["to_forecast"] = to_forecast
        response = self.__request_template(
            endpoint_cls=Endpoint(user_resources.GET, user_resources.uri),
            log_msg=f"Getting user resources (to_forecast = {to_forecast})",
            params=params,
            exception_cls=UserException
        )
        return response["data"]

    def list_resource_measurements_data(self, resource_id,
                                        start_date, end_date):
        params = {"resource": resource_id,
                  "start_date": start_date,
                  "end_date": end_date}
        t0 = time()
        response = self.__request_template(
            endpoint_cls=Endpoint(data_measurements.GET, data_measurements.uri),
            log_msg=f"Getting resource '{resource_id}' measurements data.",
            params=params,
            exception_cls=UserException
        )
        print(f"took {time() - t0:.3f} seconds to retrieve {len(response["data"])}")
        return response["data"]

    def post_market_forecasts(self, challenge_id: str,
                              model_id: str,
                              variable_id: str,
                              forecasts: list):
        payload = {
            "model": model_id,
            "variable": variable_id,
            "forecasts": forecasts
        }
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_ensemble_forecasts.POST,
                                  market_challenge_ensemble_forecasts.uri.format(challenge_id=challenge_id)),
            log_msg="Uploading market ensemble forecasts.",
            data=payload,
            exception_cls=MarketSessionException
        )
        return response['data']

    def post_market_ramp_alerts(self, challenge_id: str,
                                model_id: str,
                                ramp_alerts: list):
        payload = {
            "model": model_id,
            "ramp_alerts": ramp_alerts
        }
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_ensemble_ramp_alerts.POST,
                                  market_challenge_ensemble_ramp_alerts.uri.format(challenge_id=challenge_id)),
            log_msg="Uploading market ramp alerts.",
            data=payload,
            exception_cls=MarketSessionException
        )
        return response['data']

    def post_market_weights(self,
                            challenge_id: str,
                            weights: dict):
        payload = weights
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_id_ensemble_weights.POST,
                                  market_challenge_id_ensemble_weights.uri.format(challenge_id=challenge_id)),
            log_msg="Uploading market ensemble weights.",
            data=payload,
            exception_cls=MarketSessionException
        )
        return response['data']

    def post_submission_scores(self,
                               challenge_id: str,
                               scores: dict):
        payload = scores
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_submissions_scores.POST,
                                  market_challenge_submissions_scores.uri.format(challenge_id=challenge_id)),
            log_msg="Uploading market submission scores.",
            data=payload,
            exception_cls=MarketSessionException
        )
        return response['data']

    def list_ensemble_metadata(self, challenge_id):
        params = {"challenge": challenge_id}
        t0 = time()
        response = self.__request_template(
            endpoint_cls=Endpoint(market_challenge_ensemble_meta.GET, market_challenge_ensemble_meta.uri),
            log_msg=f"Getting ensemble metadata for challenge '{challenge_id}'.",
            params=params,
            exception_cls=UserException
        )
        print(f"took {time() - t0:.3f} seconds to retrieve {len(response["data"])}")
        return response["data"]

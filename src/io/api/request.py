import json
import requests
from requests import Response

from loguru import logger
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from .endpoint import Endpoint


class RequestController:
    """
    Manages api calls to remote endpoint using Python *requests* package
    """

    def __init__(self, config):
        self.retries = int(config.get("N_REQUEST_RETRIES", 3))
        self.remote_host = config.get("RESTAPI_HOST", None)
        self.remote_port = config.get("RESTAPI_PORT", None)
        self.remote_protocol = config.get("RESTAPI_PROTOCOL", "http")
        self.remote_uri = (
            f"{self.remote_protocol}://{self.remote_host}:{self.remote_port}"  # noqa
        )
        self.headers = {"content-type": "application/json"}

    # note the endpoint is forced to follow the standard Endpoint class
    def request(
        self,
        endpoint: Endpoint,
        data=None,
        params=None,
        url_params=None,
        auth_token=None,
    ) -> Response:
        """
        :param endpoint:
        :param data:
        :param params:
        :param url_params:
        :param auth_token:
        :return:
        """

        url = self.remote_uri + endpoint.uri
        if url_params is not None:
            if url[-1] != "/":
                url += "/"
            for p in url_params:
                url += f"{p}"
        logger.debug(f"[{endpoint.http_method}]Request to: {url} -- QP {params}")

        data = None if data is None else json.dumps(data)
        headers_ = self.headers
        if auth_token:
            headers_["Authorization"] = f"Bearer {auth_token}"
        try:
            response = self.__requests_retry_session().request(
                method=endpoint.http_method,
                url=url,
                data=data,
                params=params,
                headers=headers_,
            )

        except (
            requests.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.InvalidURL,
        ) as e:
            raise e

        return response

    def __requests_retry_session(
        self, back_off_factor=0.3, status_force_list=(500, 502, 504), session=None
    ):
        """
        https://www.peterbe.com/plog/best-practice-with-retries-with-requests
        :param back_off_factor:
        :param status_force_list:
        :param session:
        :return:
        """
        session = session or requests.Session()

        retry = Retry(
            total=self.retries,
            read=self.retries,
            connect=self.retries,
            backoff_factor=back_off_factor,
            status_forcelist=status_force_list,
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

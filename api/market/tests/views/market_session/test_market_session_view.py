# flake8: noqa

from django.urls import reverse
from rest_framework import status
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from ....models import MarketSession
from ...common import (
    create_and_login_superuser,
    create_user,
    login_user,
)
from ..response_templates import conflict_error_response


class TestMarketSessionView(TransactionTestCase):
    """
        Tests for MarketSession class.

    """
    reset_sequences = True  # reset DB AutoIncremental PK's on each test

    def setUp(self):
        self.client = APIClient()
        self.base_url = reverse("market:market-session")
        self.super_user = create_and_login_superuser(self.client)
        self.normal_user = create_user()

    def test_no_auth_create_session(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.post(self.base_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_auth_list_session(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_create_session_normal_user(self):
        login_user(client=self.client, user=self.normal_user)

        response = self.client.post(self.base_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_update_session(self):
        login_user(client=self.client, user=self.super_user)
        response = self.client.post(self.base_url, format="json")
        session_id = response.json()["data"]["id"]
        login_user(client=self.client, user=self.normal_user)
        data = {"status": "closed"}
        response = self.client.patch(self.base_url + f"/{session_id}", data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_create_session(self):
        login_user(client=self.client, user=self.super_user)

        response = self.client.post(self.base_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_data = response.json()["data"]
        # By default, the status of the session should be "open"
        self.assertEqual(response_data["status"], "open")
        self.assertIsInstance(response_data["open_ts"], str)
        # Check if "open_ts" is a datetime string (ISO 8601 format)
        self.assertRegex(response_data["open_ts"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}Z")
        # Other fields should be None
        self.assertIsNone(response_data["close_ts"])
        self.assertIsNone(response_data["launch_ts"])
        self.assertIsNone(response_data["finish_ts"])

    def test_admin_list_session_without_creation(self):
        login_user(client=self.client, user=self.super_user)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 0)

    def test_admin_list_session(self):
        # Create session w/ default data (status="open")
        MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)

        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)

    def test_admin_list_session_open_status(self):
        MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)

        response = self.client.get(self.base_url, params={"status": "open"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["status"], "open")

    def test_admin_list_session_closed_status(self):
        MarketSession.objects.create(status="closed")
        login_user(client=self.client, user=self.super_user)

        response = self.client.get(self.base_url, params={"status": "closed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["status"], "closed")

    def test_admin_list_session_running_status(self):
        MarketSession.objects.create(status="running")
        login_user(client=self.client, user=self.super_user)

        response = self.client.get(self.base_url, params={"status": "running"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["status"], "running")

    def test_admin_list_session_finished_status(self):
        MarketSession.objects.create(status="finished")
        login_user(client=self.client, user=self.super_user)

        response = self.client.get(self.base_url, params={"status": "finished"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["status"], "finished")

    def test_admin_create_session_with_already_open_session(self):
        MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)

        # Try to create new session - should fail as sessions can only
        # be created if there are no unfinished session
        response = self.client.post(self.base_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        expected_response = conflict_error_response(
            message='Unable to create new session. '
                    'There are still unfinished sessions.'
        )
        self.assertEqual(response.json(), expected_response)

    def test_admin_update_session_status(self):
        MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)
        valid_status = MarketSession.MarketStatus.values

        response = self.client.get(self.base_url, params={"status": "open"})
        session_id = response.json()["data"][0]["id"]

        for status_choice in valid_status:
            data = {"status": status_choice}
            response = self.client.patch(self.base_url + f"/{session_id}",
                                         data=data)
            response_data = response.json()["data"]
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data["id"], session_id)
            self.assertEqual(response_data["status"], status_choice)

    def test_admin_list_latest_session(self):
        MarketSession.objects.create()
        MarketSession.objects.create()
        MarketSession.objects.create()
        login_user(client=self.client, user=self.normal_user)

        response = self.client.get(self.base_url, {"latest_only": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], 3)

    def test_admin_list_session_by_id(self):
        s1 = MarketSession.objects.create()
        s2 = MarketSession.objects.create()
        s3 = MarketSession.objects.create()
        login_user(client=self.client, user=self.normal_user)

        for session in [s1, s2, s3]:
            session_id = session.id
            response = self.client.get(self.base_url, {"market_session": session_id})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()["data"]
            self.assertEqual(len(response_data), 1)
            self.assertEqual(response_data[0]["id"], session_id)

    def test_admin_list_session_by_status(self):

        def session_by_status(session_status, n_sessions):
            response = self.client.get(self.base_url,{"status": session_status})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()["data"]
            self.assertEqual(len(response_data), n_sessions)
            self.assertEqual(response_data[0]["status"], session_status)

        # Create sessions:
        MarketSession.objects.create(status="open")
        MarketSession.objects.create(status="closed")
        MarketSession.objects.create(status="running")
        MarketSession.objects.create(status="finished")
        MarketSession.objects.create(status="finished")
        login_user(client=self.client, user=self.normal_user)
        # Request by status:
        session_by_status(session_status="open", n_sessions=1)
        session_by_status(session_status="closed", n_sessions=1)
        session_by_status(session_status="running", n_sessions=1)
        session_by_status(session_status="finished", n_sessions=2)

    def test_admin_list_latest_session_bad_query_params(self):
        login_user(client=self.client, user=self.normal_user)
        response = self.client.get(self.base_url, {"latest_only": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.base_url, {"latest_only": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.base_url, {"latest_only": "asdsd"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = ["Query param 'latest_only' must be a boolean "
                             "(true/false)"]
        self.assertEqual(response_data, expected_response)

    def test_admin_update_session_invalid_status(self):
        login_user(client=self.client, user=self.super_user)
        response = self.client.post(self.base_url, format="json")
        session_id = response.json()["data"]["id"]
        data = {"status": "invalid_status"}
        response = self.client.patch(self.base_url + f"/{session_id}", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_update_open_session_duplicate_error(self):
        # Create a finished session and a open session:
        s1 = MarketSession.objects.create(status="finished")
        s2 = MarketSession.objects.create(status="open")
        # Login:
        login_user(client=self.client, user=self.super_user)
        # Try to update the status of the finished session to "open"
        # (should fail, the user should not be able to create multiple open
        # market sessions)
        data = {"status": "open"}
        response = self.client.patch(self.base_url + f"/{s1.id}", data=data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_create_multiple_sessions(self):
        login_user(client=self.client, user=self.super_user)
        for session_number in range(0, 5):
            # Create session ('open' status by default)
            response = self.client.post(self.base_url, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Change session status to 'finished'
            session_id = response.json()["data"]["id"]
            data = {"status": "finished"}
            response = self.client.patch(self.base_url + f"/{session_id}",
                                         data=data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            db_entries = MarketSession.objects.all()
            self.assertEqual(len(db_entries), session_number + 1)

    def test_admin_update_session_invalid_data(self):
        login_user(client=self.client, user=self.super_user)
        response = self.client.post(self.base_url, format="json")
        session_id = response.json()["data"]["id"]
        invalid_data = {"invalid_field": "invalid_value"}
        response = self.client.patch(self.base_url + f"/{session_id}", data=invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_delete_session(self):
        login_user(client=self.client, user=self.super_user)
        response = self.client.post(self.base_url, format="json")
        session_id = response.json()["data"]["id"]
        response = self.client.delete(self.base_url + f"/{session_id}")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_admin_list_session_invalid_status(self):
        login_user(client=self.client, user=self.super_user)
        response = self.client.get(self.base_url, {"status": "invalid_status"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_list_session_multiple_valid_query_params(self):
        MarketSession.objects.create(status="open")
        MarketSession.objects.create(status="closed")
        login_user(client=self.client, user=self.super_user)
        response = self.client.get(self.base_url, {"status": "open", "latest_only": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["status"], "open")
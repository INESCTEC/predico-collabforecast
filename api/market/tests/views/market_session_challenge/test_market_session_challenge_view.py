# flake8: noqa
import datetime as dt

from django.urls import reverse
from rest_framework import status
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from ....models import MarketSession
from ...common import (
    create_market_challenge_data,
    create_raw_data,
    create_and_login_superuser,
    create_user,
    login_user, create_superuser,
)
from ..response_templates import conflict_error_response


class TestMarketSessionChallengeView(TransactionTestCase):
    """
        Tests for MarketSession class.

    """
    reset_sequences = True  # reset DB AutoIncremental PK's on each test

    user_resource = {"name": "u1-resource-1", "timezone": "Europe/Brussels"}
    super_user_2_config = {'email': "admin2@user.com",
                           'password': "admin_foo",
                           'is_session_manager': False}

    def setUp(self):
        self.client = APIClient()
        self.base_url = reverse("market:market-session-challenge")
        self.resource_url = reverse("user:resource-list-create")
        self.raw_data_url = reverse("data:raw-measurements")
        self.super_user = create_and_login_superuser(self.client)
        self.super_user_2 = create_superuser(self.client, **self.super_user_2_config)
        self.normal_user = create_user()
        self.ts_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"

    def prepare_market_session(self):
        # Create Session:
        session = MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)
        # Register resource:
        response = self.client.post(self.resource_url, data=self.user_resource, format="json")
        return session.id, response.json()["data"]["id"]

    def create_challenge_pipeline(self, session_id=None, resource_id=None):
        if not session_id and not resource_id:
            session_id, resource_id = self.prepare_market_session()
        # Create challenge data:
        challenge = create_market_challenge_data(
            market_session_id=session_id,
            resource_id=resource_id
        )
        # Create measurements data:
        raw_data = create_raw_data(resource_id=resource_id)
        # Auth:
        login_user(client=self.client, user=self.super_user)
        # Publish raw data (requirement to open a challenge):
        response = self.client.post(self.raw_data_url, data=raw_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Publish challenge:
        response = self.client.post(self.base_url, data=challenge, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Get challenge data:
        response_data = response.json()["data"]
        # Check if resource_id and user_id registered for this challenge
        # match the ones in the challenge data:
        self.assertEqual(response_data["resource"], resource_id)
        self.assertEqual(response_data["resource"], resource_id)
        self.assertEqual(response_data["user"], str(self.super_user.id))
        return response_data

    def test_no_auth_create_challenge(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.post(self.base_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_auth_list_challenge(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_create_challenge(self):
        # Get challenge info:
        challenge_data = self.create_challenge_pipeline()
        # Validate main field types:
        self.assertIsInstance(challenge_data["id"], str)
        self.assertIsInstance(challenge_data["user"], str)
        self.assertIsInstance(challenge_data["market_session"], int)
        self.assertIsInstance(challenge_data["resource"], str)
        self.assertIsInstance(challenge_data["use_case"], str)
        # Check if datetime fields are in ISO 8601 format:
        self.assertRegex(challenge_data["forecast_start_datetime"], self.ts_regex)
        self.assertRegex(challenge_data["forecast_start_datetime"], self.ts_regex)
        # Start datetime should be today (UTC) -> 00:00h Brussels
        start_date = dt.datetime.strptime(challenge_data["forecast_start_datetime"], "%Y-%m-%dT%H:%M:%SZ")
        # End datetime should be tomorrow (UTC) -> 23:45h Brussels
        end_date = dt.datetime.strptime(challenge_data["forecast_end_datetime"], "%Y-%m-%dT%H:%M:%SZ")
        # Confirm dates:
        self.assertGreater(end_date, start_date)
        self.assertEqual(start_date.date(), dt.date.today())
        self.assertEqual(end_date.date(), dt.date.today() + dt.timedelta(days=1))

    def test_admin_update_challenge_use_case(self):
        challenge_data = self.create_challenge_pipeline()
        challenge_data["use_case"] = "wind_power_ramp"
        url = self.base_url + f"/{challenge_data['id']}"
        response = self.client.put(url, data=challenge_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        # Check if field was updated:
        self.assertEqual(response_data["use_case"], "wind_power_ramp")
        # Check if common fields match:
        for k, v in challenge_data.items():
            if k == "use_case": # changed field
                continue
            # Rename datetime fields to match the response:
            k = "start_datetime" if k == "forecast_start_datetime" else k
            k = "end_datetime" if k == "forecast_end_datetime" else k
            self.assertEqual(response_data[k], v)

    def test_admin_update_other_admin_challenge_use_case(self):
        challenge_data = self.create_challenge_pipeline()
        challenge_data["use_case"] = "wind_power_ramp"
        url = self.base_url + f"/{challenge_data['id']}"
        login_user(self.client, self.super_user_2)
        response = self.client.put(url, data=challenge_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_challenge_other_admin_resource(self):
        # Create challenge and register resource for superuser 1:
        session_id, resource_id = self.prepare_market_session()

        # Login with superuser 2
        login_user(self.client, self.super_user_2)

        # Try to create challenge with resource from superuser 1
        challenge = create_market_challenge_data(market_session_id=session_id, resource_id=resource_id)
        response = self.client.post(self.base_url, data=challenge, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_create_challenge_invalid_resource(self):
        # Get challenge info:
        session_id, resource_id = self.prepare_market_session()
        resource_id = 'e5b65f21-76b2-4d55-a1d3-6b82a75b328c'  # Overwrite id
        # Create challenge data:
        challenge = create_market_challenge_data(market_session_id=session_id, resource_id=resource_id)
        response = self.client.post(self.base_url, data=challenge, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_create_multiple_challenges(self):
        # Create Session:
        session = MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)
        n_challenges = 5
        challenge_data_list = []
        for i in range(n_challenges):
            resource = {"name": f"u1-resource-{i}", "timezone": "Europe/Brussels"}
            # Register resources:
            response = self.client.post(self.resource_url, data=resource, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            resource_id = response.json()["data"]["id"]
            # Create challenge data:
            challenge = create_market_challenge_data(
                market_session_id=session.id,
                resource_id=resource_id
            )
            challenge_data_list.append(challenge)
            # Create measurements data:
            raw_data = create_raw_data(resource_id=resource_id)
            # Publish raw data (requirement to open a challenge):
            response = self.client.post(self.raw_data_url, data=raw_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Publish challenge:
            response = self.client.post(self.base_url, data=challenge, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # List created challenges:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get response:
        response_data = response.json()["data"]
        # Check if we have data for all the created challenges::
        self.assertEqual(len(response_data), n_challenges)
        # Check if challenge data matches the one created:
        for i, challenge_data in enumerate(challenge_data_list):
            for k, v in challenge_data.items():
                self.assertEqual(response_data[i][k], v)

    def test_admin_create_multiple_challenges_same_resource(self):
        # Create Session:
        session = MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)
        n_challenges = 2
        challenge_data_list = []
        resource = {"name": f"u1-resource-1", "timezone": "Europe/Brussels"}
        # Register resources:
        response = self.client.post(self.resource_url, data=resource, format="json")
        resource_id = response.json()["data"]["id"]
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for i in range(n_challenges):
            # Create challenge data:
            challenge = create_market_challenge_data(
                market_session_id=session.id,
                resource_id=resource_id
            )
            # Create measurements data:
            raw_data = create_raw_data(resource_id=resource_id)
            # Publish raw data (requirement to open a challenge):
            response = self.client.post(self.raw_data_url, data=raw_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Publish challenge:
            response = self.client.post(self.base_url, data=challenge, format="json")
            # For second attempt, we should get a conflict error since this
            # resource already has a challenge assigned:
            if i == 0:
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            else:
                self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_list_challenge(self):
        # Get challenge info:
        challenge_data = self.create_challenge_pipeline()
        # List challenges:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get response:
        response_data = response.json()["data"]
        # Only 1 challenge registered - 1 challenge returned:
        self.assertEqual(len(response_data), 1)
        # Check if challenge data matches the one created:
        for k, v in challenge_data.items():
            # Rename datetime fields to match the response:
            k = "start_datetime" if k == "forecast_start_datetime" else k
            k = "end_datetime" if k == "forecast_end_datetime" else k
            self.assertEqual(response_data[0][k], v)

    def test_admin_list_challenge_by_id(self):
        # Get challenge info:
        challenge_data = self.create_challenge_pipeline()
        # List challenges:
        response = self.client.get(self.base_url, params={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get response:
        response_data = response.json()["data"]
        # Only 1 challenge registered - 1 challenge returned:
        self.assertEqual(len(response_data), 1)
        # Check if challenge data matches the one created:
        for k, v in challenge_data.items():
            # Rename datetime fields to match the response:
            k = "start_datetime" if k == "forecast_start_datetime" else k
            k = "end_datetime" if k == "forecast_end_datetime" else k
            self.assertEqual(response_data[0][k], v)

    def test_admin_list_challenge_by_market_session(self):
        # Get challenge info:
        challenge_data = self.create_challenge_pipeline()
        # List challenges:
        response = self.client.get(self.base_url, params={"market_session": challenge_data["market_session"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Get response:
        response_data = response.json()["data"]
        # Only 1 challenge registered - 1 challenge returned:
        self.assertEqual(len(response_data), 1)
        # Check if challenge data matches the one created:
        for k, v in challenge_data.items():
            # Rename datetime fields to match the response:
            k = "start_datetime" if k == "forecast_start_datetime" else k
            k = "end_datetime" if k == "forecast_end_datetime" else k
            self.assertEqual(response_data[0][k], v)

    def test_normal_create_challenge(self):
        login_user(client=self.client, user=self.normal_user)
        response = self.client.post(self.base_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_create_challenge_invalid_data(self):
        login_user(client=self.client, user=self.super_user)
        invalid_challenge = {"invalid_field": "invalid_value"}
        response = self.client.post(self.base_url, data=invalid_challenge, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_update_challenge_invalid_data(self):
        challenge_data = self.create_challenge_pipeline()
        challenge_data["use_case"] = ""
        url = self.base_url + f"/{challenge_data['id']}"
        response = self.client.put(url, data=challenge_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_delete_challenge(self):
        challenge_data = self.create_challenge_pipeline()
        url = self.base_url + f"/{challenge_data['id']}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_admin_list_challenge_with_filters(self):
        challenge_data = self.create_challenge_pipeline()
        # List challenges with a filter that matches the created challenge
        response = self.client.get(self.base_url, {"use_case": challenge_data["use_case"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], challenge_data["id"])

        # List challenges with a filter that does not match any challenge
        response = self.client.get(self.base_url, {"use_case": "non_existent_use_case"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
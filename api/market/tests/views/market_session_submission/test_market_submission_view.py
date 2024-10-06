# flake8: noqa
import datetime as dt
import pandas as pd
import threading
from django.urls import reverse
from rest_framework import status
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from ....models import MarketSession
from ...common import (
    create_market_challenge_data,
    create_raw_data,
    create_market_submission_data,
    create_market_historical_forecasts_data,
    create_forecasts_submission_data,
    create_and_login_superuser,
    create_user,
    login_user, create_superuser,
)

class TestMarketSessionSubmissionView(TransactionTestCase):
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
        self.base_market_url = reverse("market:market-session-challenge")
        self.resource_url = reverse("user:resource-list-create")
        self.raw_data_url = reverse("data:raw-measurements")
        self.forecast_historical_data_url = reverse("data:individual-forecasts")
        self.submission_list_url = reverse("market:market-session-submission-list")
        self.submission_forecasts_list_url = reverse("market:market-session-submission-forecasts-list")
        self.super_user = create_and_login_superuser(self.client)
        self.super_user_2 = create_superuser(self.client, **self.super_user_2_config)
        self.normal_user = create_user()
        self.ts_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"

    def prepare_market_session(self):
        session = MarketSession.objects.create()
        login_user(client=self.client, user=self.super_user)
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
        # Auth as admin:
        login_user(client=self.client, user=self.super_user)
        # Publish raw data (requirement to open a challenge):
        response = self.client.post(self.raw_data_url, data=raw_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Publish challenge:
        response = self.client.post(self.base_market_url, data=challenge, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Get challenge data:
        response_data = response.json()["data"]
        # Check if resource_id and user_id registered for this challenge
        # match the ones in the challenge data:
        self.assertEqual(response_data["resource"], resource_id)
        self.assertEqual(response_data["resource"], resource_id)
        self.assertEqual(response_data["user"], str(self.super_user.id))
        return response_data

    def create_submission_pipeline(self, challenge_data, force_admin=False, quantile="q50"):
        if force_admin:
            # Auth as admin:
            login_user(client=self.client, user=self.super_user)
        else:
            # Authenticate as a normal user:
            login_user(client=self.client, user=self.normal_user)
        # Prepare forecast historical data (31 days prior to challenge)
        st_ = dt.datetime.strptime(challenge_data["forecast_start_datetime"], "%Y-%m-%dT%H:%M:%SZ")
        forecasts_historical_data = create_forecasts_submission_data(
            start_date=st_ - pd.DateOffset(days=31),
            end_date=st_
        )
        # Post historical data:
        historical_submission_data = create_market_historical_forecasts_data(
            resource_id=challenge_data["resource"],
            launch_time=dt.datetime.utcnow(),
            variable=quantile,
            forecasts=forecasts_historical_data
        )
        # Publish historical data:
        response = self.client.post(self.forecast_historical_data_url,
                                    data=historical_submission_data,
                                    format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Prepare forecast submission data:
        forecasts_data = create_forecasts_submission_data(
            start_date=challenge_data["forecast_start_datetime"],
            end_date=challenge_data["forecast_end_datetime"]
        )
        # Prepare submission:
        submission_data = create_market_submission_data(
            variable=quantile,
            forecasts=forecasts_data,
        )
        # Publish submission:
        submission_url = reverse(
            "market:market-session-submission-create-update",
            kwargs={"challenge_id": challenge_data["id"]}
        )
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Get submission data:
        submission = response.json()["data"]
        self.assertEqual(submission["challenge_id"], challenge_data["id"])
        return submission

    def test_no_auth_submit_forecast(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        submission_url = reverse("market:market-session-submission-create-update", kwargs={"challenge_id": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.post(submission_url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_forecaster_submit_forecast_without_historical(self):
        challenge_data = self.create_challenge_pipeline()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_submission_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-submission-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_normal_forecaster_submit_forecast_with_historical(self):
        challenge_data = self.create_challenge_pipeline()
        self.create_submission_pipeline(challenge_data=challenge_data)
        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.submission_forecasts_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 96)

    def test_admin_forecaster_submit_forecast_with_historical(self):
        challenge_data = self.create_challenge_pipeline()
        self.create_submission_pipeline(challenge_data=challenge_data, force_admin=True)
        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["market_session_challenge_resource_id"], challenge_data["resource"])
        self.assertEqual(response_data[0]["market_session_challenge"], challenge_data["id"])
        response = self.client.get(self.submission_forecasts_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 96)

    def test_admin_list_submissions_from_another_admin_challenge(self):
        challenge_data = self.create_challenge_pipeline()
        self.create_submission_pipeline(challenge_data=challenge_data, force_admin=True)
        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        login_user(client=self.client, user=self.super_user_2)
        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_admin_list_submission_forecasts_from_another_admin_challenge(self):
        challenge_data = self.create_challenge_pipeline()
        self.create_submission_pipeline(challenge_data=challenge_data, force_admin=True)
        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        login_user(client=self.client, user=self.super_user_2)
        response = self.client.get(self.submission_forecasts_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 0)

    def test_invalid_data_submission(self):
        challenge_data = self.create_challenge_pipeline()
        invalid_submission_data = {"variable": "invalid", "forecasts": []}
        submission_url = reverse("market:market-session-submission-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=invalid_submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        challenge_data = self.create_challenge_pipeline()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_submission_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-submission-create-update", kwargs={"challenge_id": challenge_data["id"]})
        self.client.credentials()  # Remove authentication
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_different_forecast_variables_without_historical(self):
        challenge_data = self.create_challenge_pipeline()
        for variable in ["q05", "q50", "q95"]:
            forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
            submission_data = create_market_submission_data(variable=variable, forecasts=forecasts_data)
            submission_url = reverse("market:market-session-submission-create-update", kwargs={"challenge_id": challenge_data["id"]})
            response = self.client.post(submission_url, data=submission_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_different_forecast_variables(self):
        challenge_data = self.create_challenge_pipeline()
        for variable in ["q05", "q50", "q95"]:
            self.create_submission_pipeline(challenge_data=challenge_data, quantile=variable)

        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 3)
        for submission in response_data:
            self.assertEqual(submission["market_session_challenge"], challenge_data["id"])
            self.assertEqual(submission["market_session_challenge_resource_id"], challenge_data["resource"])
            self.assertIn(submission["variable"], ["q05", "q50", "q95"])

        response = self.client.get(self.submission_forecasts_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 4*24*3)

    def test_submission_update(self):
        challenge_data = self.create_challenge_pipeline()
        submission = self.create_submission_pipeline(challenge_data=challenge_data)
        updated_forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        updated_submission_data = create_market_submission_data(variable="q50", forecasts=updated_forecasts_data)
        submission_url = reverse("market:market-session-submission-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.put(submission_url, data=updated_submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(response_data["challenge_id"], challenge_data["id"])

    def test_concurrent_submissions(self):
        challenge_data = self.create_challenge_pipeline()
        
        # Prepare forecast historical data (31 days prior to challenge)
        st_ = dt.datetime.strptime(challenge_data["forecast_start_datetime"], "%Y-%m-%dT%H:%M:%SZ")
        forecasts_historical_data = create_forecasts_submission_data(
            start_date=st_ - pd.DateOffset(days=31),
            end_date=st_
        )
        # Post historical data:
        historical_submission_data = create_market_historical_forecasts_data(
            resource_id=challenge_data["resource"],
            launch_time=dt.datetime.utcnow(),
            variable="q50",
            forecasts=forecasts_historical_data
        )
        # Publish historical data:
        response = self.client.post(self.forecast_historical_data_url,
                                    data=historical_submission_data,
                                    format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        submission_data = create_market_submission_data(
            variable="q50",
            forecasts=create_forecasts_submission_data(
                start_date=challenge_data["forecast_start_datetime"],
                end_date=challenge_data["forecast_end_datetime"]
            )
        )
        submission_url = reverse(
            "market:market-session-submission-create-update",
            kwargs={"challenge_id": challenge_data["id"]}
        )

        def submit_forecast():
            response = self.client.post(submission_url, data=submission_data, format="json")
            print(response.json())
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT])

        threads = [threading.Thread(target=submit_forecast) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        response = self.client.get(self.submission_list_url, data={"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertGreaterEqual(len(response_data), 1)
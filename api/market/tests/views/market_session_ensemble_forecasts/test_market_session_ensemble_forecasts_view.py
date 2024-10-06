# flake8: noqa
import datetime as dt
import pandas as pd
from django.urls import reverse
from rest_framework import status
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from ....models import MarketSession
from ...common import (
    create_market_challenge_data,
    create_raw_data,
    create_market_ensemble_data,
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
        self.ensemble_forecasts_list_url = reverse("market:market-session-ensemble-list")
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

    def test_no_auth_submit_ensemble(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        ensemble_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.post(ensemble_url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_no_auth_list_ensemble(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.ensemble_forecasts_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_submit_ensemble(self):
        login_user(client=self.client, user=self.normal_user)
        ensemble_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": "123e4567-e89b-12d3-a456-426614174000"})
        response = self.client.post(ensemble_url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_normal_list_ensemble(self):
        login_user(client=self.client, user=self.normal_user)
        response = self.client.get(self.ensemble_forecasts_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_admin_submit_forecast(self):
        challenge_data = self.create_challenge_pipeline()
        # Update market session status to RUNNING:
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        # Create forecasts data:
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_admin_list_forecast(self):
        challenge_data = self.create_challenge_pipeline()
        # Update market session status to RUNNING:
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        # Create forecasts data:
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # List forecasts:
        response = self.client.get(self.ensemble_forecasts_list_url, {"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 4 * 24)
        self.assertEqual(response_data[0]["challenge"], challenge_data["id"])
        self.assertEqual(response_data[0]["resource"], challenge_data["resource"])
        self.assertEqual(response_data[0]["variable"], "q50")
        
    def test_normal_submit_forecast(self):
        challenge_data = self.create_challenge_pipeline()
        # Update market session status to RUNNING:
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        # Create forecasts data:
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        login_user(client=self.client, user=self.normal_user)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_normal_list_forecast(self):
        # List forecasts:
        login_user(client=self.client, user=self.normal_user)
        response = self.client.get(self.ensemble_forecasts_list_url, {"challenge": "123e4567-e89b-12d3-a456-426614174000"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_admin_submit_forecast_other_admin_challenge(self):
        challenge_data = self.create_challenge_pipeline()
        # Update market session status to RUNNING:
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        # Create forecasts data:
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        login_user(client=self.client, user=self.super_user_2)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
    
    def test_admin_list_forecast_other_admin_challenge(self):
        challenge_data = self.create_challenge_pipeline()
        # Update market session status to RUNNING:
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        # Create forecasts data:
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # List forecasts:
        login_user(client=self.client, user=self.super_user_2)
        response = self.client.get(self.ensemble_forecasts_list_url, {"challenge": challenge_data["id"]})
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 0)

    def test_admin_submit_forecast_when_not_running(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.OPEN
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_forecasts_bad_value(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        # Modify forecasts_data to check invalid value
        forecasts_data[0]["value"] = 'string'  # Example of a boundary condition
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_admin_forecasts_incomplete(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        # Modify forecasts_data to remove a sample
        forecasts_data = forecasts_data[:-1]
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_forecasts_too_many_samples(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        # Modify forecasts_data to add extra sample
        forecasts_data += [forecasts_data[-1]]
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_forecasts_bad_variable(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        # Modify forecasts_data to test boundary conditions
        submission_data = create_market_ensemble_data(variable="string", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_admin_concurrent_submissions(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        # Simulate concurrent submissions
        response1 = self.client.post(submission_url, data=submission_data, format="json")
        response2 = self.client.post(submission_url, data=submission_data, format="json")
        self.assertIn(response1.status_code, [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT])
        self.assertIn(response2.status_code, [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT])

    def test_admin_data_integrity(self):
        challenge_data = self.create_challenge_pipeline()
        session = MarketSession.objects.get(id=challenge_data["market_session"])
        session.status = MarketSession.MarketStatus.RUNNING
        session.save()
        forecasts_data = create_forecasts_submission_data(start_date=challenge_data["forecast_start_datetime"], end_date=challenge_data["forecast_end_datetime"])
        submission_data = create_market_ensemble_data(variable="q50", forecasts=forecasts_data)
        submission_url = reverse("market:market-session-ensemble-create-update", kwargs={"challenge_id": challenge_data["id"]})
        response = self.client.post(submission_url, data=submission_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Retrieve and verify data
        response = self.client.get(self.ensemble_forecasts_list_url, {"challenge": challenge_data["id"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), len(forecasts_data))
        self.assertEqual(response_data[0]["challenge"], challenge_data["id"])
        self.assertEqual(response_data[0]["resource"], challenge_data["resource"])
        self.assertEqual(response_data[0]["variable"], "q50")
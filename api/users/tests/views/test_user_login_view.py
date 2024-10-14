# flake8: noqa

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ..common import create_and_login_superuser, drop_dict_field, create_user


User = get_user_model()


class TestUserLoginView(APITestCase):
    """
        Tests for UserRegisterView class.

    """

    data = {'email': 'normal@user.com',
            'password': 'normal_foo',
            'first_name': 'Normal',
            'last_name': 'Peanut'}

    def setUp(self):
        self.register_url = reverse("user:register")
        self.base_url = reverse("token_obtain_pair")
        create_and_login_superuser(self.client)

    def test_failed_login(self):
        # Register user:
        response = self.client.post(self.register_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Login user w/ incorrect password:
        login_ = {
            "email": self.data["email"],
            "password": "incorrect_pw"
        }
        response = self.client.post(self.base_url, data=login_, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {'non_field_errors': ['Invalid login credentials.']}
        response_data = response.json()
        self.assertEqual(response_data, expected_response)

    def test_unverified_login(self):
        # Register user:
        response = self.client.post(self.register_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Login user w/ incorrect password:
        login_ = {
            "email": self.data["email"],
            "password": self.data["password"]
        }
        response = self.client.post(self.base_url, data=login_, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {'non_field_errors': ['Email not verified.']}
        response_data = response.json()
        self.assertEqual(response_data, expected_response)

    def test_verified_login(self):
        # Register user:
        response = self.client.post(self.register_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify user account:
        response = self.client.get(response.json()["data"]["verification_link"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Login user w/ incorrect password:
        login_ = {
            "email": self.data["email"],
            "password": self.data["password"]
        }
        response = self.client.post(self.base_url, data=login_, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_already_verified(self):
        # Register user:
        response = self.client.post(self.register_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification_url = response.json()["data"]["verification_link"]
        # Verify user account:
        response = self.client.get(verification_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify user account (2x):
        response = self.client.get(verification_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


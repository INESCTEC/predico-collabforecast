# flake8: noqa

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ..common import create_superuser, login_user, logout_user


User = get_user_model()


class TestUserLoginView(APITestCase):
    """
        Tests for UserRegisterView class.

    """

    admin_user_1 = {'email': 'admin1@user.com',
                    'password': 'admin1_foo'}
    normal_user_1 = {'email': 'normal1@user.com',
                     'password': 'normal1_foo',
                     'first_name': 'Normal1',
                     'last_name': 'Peanut1'}

    def setUp(self):
        self.admin_register_url = reverse("user:admin-register")
        self.register_url = reverse("user:register")
        self.base_url = reverse("token_obtain_pair")
        self.super_user1 = create_superuser(use_custom_data=True,
                                            **self.admin_user_1)

    def admin_creates_invite_token(self):
        login_user(self.client, user=self.super_user1)
        # Admin creates an invitation token:
        data = {"email": self.normal_user_1["email"]}
        response = self.client.post(self.admin_register_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invite_token = response.json()["data"]["link"].split("/")[-1]
        logout_user(self.client)
        return invite_token

    def test_failed_login(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.register_url, data=self.normal_user_1, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Login user w/ incorrect password:
        login_ = {
            "email": self.normal_user_1["email"],
            "password": "incorrect_pw"
        }
        response = self.client.post(self.base_url, data=login_, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {'non_field_errors': ['Invalid login credentials.']}
        response_data = response.json()
        self.assertEqual(response_data, expected_response)

    def test_unverified_login(self):
        # -- User Registration:
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.register_url, data=self.normal_user_1, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # -- User Login (without verifying email):
        login_ = {
            "email": self.normal_user_1["email"],
            "password": self.normal_user_1["password"]
        }
        response = self.client.post(self.base_url, data=login_, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {'non_field_errors': ['Email not verified.']}
        response_data = response.json()
        self.assertEqual(response_data, expected_response)

    def test_verified_login(self):
        # -- User Registration:
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.register_url, data=self.normal_user_1, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # -- User Email Verification:
        # Verify user account:
        verification_link = response.json()["data"]["verification_link"]
        uidb64 = verification_link.split("/")[-2]
        token = verification_link.split("/")[-1]
        response = self.client.get(reverse("user:verify-email"), data={"uid": uidb64, "token": token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # -- User Login (verified email):
        login_ = {
            "email": self.normal_user_1["email"],
            "password": self.normal_user_1["password"]
        }
        response = self.client.post(self.base_url, data=login_, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_already_verified(self):
        # -- User Registration:
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.register_url, data=self.normal_user_1, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # -- User Email Verification:
        # Verify user account:
        verification_link = response.json()["data"]["verification_link"]
        uidb64 = verification_link.split("/")[-2]
        token = verification_link.split("/")[-1]
        response = self.client.get(reverse("user:verify-email"), data={"uid": uidb64, "token": token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify user account (2x)
        response = self.client.get(reverse("user:verify-email"), data={"uid": uidb64, "token": token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

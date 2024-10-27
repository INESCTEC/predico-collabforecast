# flake8: noqa

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ..common import create_superuser, create_user, login_user, drop_dict_field, logout_user
from .response_templates import missing_field_response


User = get_user_model()


class TestUserRegisterView(APITestCase):
    """
        Tests for user registration class.

    """

    admin_user_1 = {'email': 'admin1@user.com',
                    'password': 'admin1_foo'}
    normal_user_1 = {'email': 'normal1@user.com',
                     'password': 'Normal1_foo_123!',
                     'first_name': 'Normal1',
                     'last_name': 'Peanut1'}

    def setUp(self):
        self.admin_register_url = reverse("user:admin-register")
        self.base_url = reverse("user:register")
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

    def test_admin_create_invite_token(self):
        self.admin_creates_invite_token()

    def test_admin_create_invite_token_no_email(self):
        login_user(self.client, user=self.super_user1)
        field_to_remove = "email"
        response = self.client.post(self.admin_register_url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_admin_create_invite_token_user_already_exists(self):
        # Create user (using Django Model)
        create_user(use_custom_data=True, **self.normal_user_1)
        # Admin creates an invitation token:
        login_user(self.client, user=self.super_user1)
        data = {"email": self.normal_user_1["email"]}
        response = self.client.post(self.admin_register_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        expected_response = {'code': 409,
                             'data': None,
                             'status': 'error',
                             'message': f"The email '{data['email']}' already exists!"}
        self.assertEqual(response.json(), expected_response)

    def test_normal_register_user(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=self.normal_user_1, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_model_data = User.objects.filter(email=self.normal_user_1["email"]).get()
        self.assertEqual(user_model_data.email, self.normal_user_1["email"])
        self.assertTrue(user_model_data.is_active)
        self.assertFalse(user_model_data.is_staff)
        self.assertFalse(user_model_data.is_superuser)

    def test_normal_register_user_no_password(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        field_to_remove = "password"
        data = drop_dict_field(data, field_to_remove)
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_normal_register_user_no_first_name(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        field_to_remove = "first_name"
        data = drop_dict_field(data, field_to_remove)
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_normal_register_user_no_last_name(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        field_to_remove = "last_name"
        data = drop_dict_field(data, field_to_remove)
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_normal_register_user_invalid_email(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        data["email"] = "normal.com"
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {'email': ['Enter a valid email address.']}
        self.assertEqual(response_data, expected_response)

    def test_normal_register_user_invalid_password_min_length(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        data["password"] = "N3o4as92!"
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {
            'password': ['This password is too short. It must contain at least 12 characters.']
        }
        self.assertEqual(response_data, expected_response)

    def test_normal_register_user_invalid_password_numeric_only(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        data["password"] = "128903210894713089471298370"
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {
            'password': ['Your password must contain at least one uppercase letter.']
        }
        self.assertEqual(response_data, expected_response)

    def test_normal_register_user_invalid_invite_token(self):
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}123"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        expected_response = {'code': 403,
                             'data': None,
                             'status': 'error',
                             'message': 'You do not have permission to perform this action.'}
        self.assertEqual(response.json(), expected_response)

    def test_normal_register_user_expire_invite_token(self):
        from time import sleep
        # Admin creates an invitation token:
        invite_token = self.admin_creates_invite_token()
        data = self.normal_user_1.copy()
        sleep(30)
        # User uses this token to register:
        client_headers = {"Authorization": f"Bearer {invite_token}"}
        response = self.client.post(self.base_url, data=data, format="json", headers=client_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        expected_response = {'code': 403,
                             'data': None,
                             'status': 'error',
                             'message': 'You do not have permission to perform this action.'}
        self.assertEqual(response.json(), expected_response)

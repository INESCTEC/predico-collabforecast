# flake8: noqa

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ..common import create_and_login_superuser, drop_dict_field, create_user
from .response_templates import missing_field_response


User = get_user_model()


class TestUserRegisterView(APITestCase):
    """
        Tests for UserRegisterView class.

    """

    data = {'email': 'normal@user.com',
            'password': 'normal_foo',
            'first_name': 'Normal',
            'last_name': 'Peanut'}

    def setUp(self):
        self.base_url = reverse("user:register")
        create_and_login_superuser(self.client)

    def test_register_user(self):
        response = self.client.post(self.base_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_model_data = User.objects.filter(email=self.data["email"]).get()
        self.assertEqual(user_model_data.email, self.data["email"])
        self.assertTrue(user_model_data.is_active)
        self.assertFalse(user_model_data.is_staff)
        self.assertFalse(user_model_data.is_superuser)

    def test_register_user_already_exists(self):
        # Create user (using Django Model)
        create_user(use_custom_data=True, **self.data)
        # Try to register new user:
        response = self.client.post(self.base_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        expected_response = {'code': 409,
                             'data': None,
                             'status': 'error',
                             'message': f"The email '{self.data['email']}' already exists!"}
        self.assertEqual(response.json(), expected_response)

    def test_register_user_no_email(self):
        field_to_remove = "email"
        data = drop_dict_field(self.data, field_to_remove)
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_register_user_no_password(self):
        field_to_remove = "password"
        data = drop_dict_field(self.data, field_to_remove)
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_register_user_no_first_name(self):
        field_to_remove = "first_name"
        data = drop_dict_field(self.data, field_to_remove)
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_register_user_no_last_name(self):
        field_to_remove = "first_name"
        data = drop_dict_field(self.data, field_to_remove)
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = missing_field_response(field_name=field_to_remove)
        self.assertEqual(response.json(), expected_response)

    def test_register_user_invalid_email(self):
        data = {'email': 'normal.com',
                'password': 'normal_foo',
                'first_name': 'Normal',
                'last_name': 'Peanut'}
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {'email': ['Enter a valid email address.']}
        self.assertEqual(response_data, expected_response)

    def test_register_user_invalid_password_min_length(self):
        data = {'email': 'normal@user.com',
                'password': 'normal',
                'first_name': 'Normal',
                'last_name': 'Peanut'}
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {
            'password': ['This password is too short. It must contain at least '
                         '9 characters.', 'This password is too common.']
        }
        self.assertEqual(response_data, expected_response)

    def test_register_user_invalid_password_too_common(self):
        data = {'email': 'normal@user.com',
                'password': '123456789a',
                'first_name': 'Normal',
                'last_name': 'Peanut'}
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {
            'password': ['This password is too common.']
        }
        self.assertEqual(response_data, expected_response)

    def test_register_user_invalid_password_numeric_only(self):
        data = {'email': 'normal@user.com',
                'password': '1353521989',
                'first_name': 'Normal',
                'last_name': 'Peanut'}
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()["data"]
        expected_response = {
            'password': ['This password is entirely numeric.']
        }
        self.assertEqual(response_data, expected_response)

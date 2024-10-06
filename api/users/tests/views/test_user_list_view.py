# flake8: noqa

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..common import create_and_login_superuser, create_user, login_user


class TestUserListView(APITestCase):
    """
    Tests for UserListView class. This method should only be available
    to superusers.

    """

    def setUp(self):
        self.base_url = reverse("user:user-list")
        self.super_user = create_and_login_superuser(self.client)
        self.normal_user = create_user()

    def test_list_users_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_list_own_user(self):
        login_user(self.client, self.normal_user)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        # Ensure that response_data is a dictionary
        # (user can only access his own info)
        self.assertIsInstance(response_data, dict)
        self.assertEqual(response_data["email"], self.normal_user.email)
        self.assertEqual(response_data["first_name"], self.normal_user.first_name)
        self.assertEqual(response_data["last_name"], self.normal_user.last_name)

    def test_superuser_list_users(self):
        login_user(self.client, self.super_user)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        # Ensure that response_data is a list
        # (admins access all other users info)
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 2)

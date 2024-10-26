# flake8: noqa

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ...models import UserResources
from ..common import create_superuser, create_user, login_user


class TestUserResourceView(APITestCase):
    """
    Tests for UserResourcesView class.
    """

    admin_user_1 = {'email': 'admin1@user.com',
                    'password': 'admin1_foo'}
    admin_user_2 = {'email': 'admin2@user.com',
                    'password': 'admin2_foo'}
    normal_user_1 = {'email': 'normal1@user.com',
                     'password': 'Normal1_foo_123!',
                     'first_name': 'Normal1',
                     'last_name': 'Peanut1'}

    admin_user_1_resources = [
        {"name": "u1-resource-1",
         "timezone": "Europe/Brussels"},
        {"name": "u1-resource-2",
         "timezone": "Europe/Brussels"},
        {"name": "u1-resource-3",
         "timezone": "Europe/Brussels"},
    ]

    admin_user_2_resources = [
        {"name": "u2-resource-1",
         "timezone": "Europe/Brussels"},
        {"name": "u2-resource-2",
         "timezone": "Europe/Brussels"},
        {"name": "u2-resource-3",
         "timezone": "Europe/Brussels"},
    ]

    def setUp(self):
        self.base_url = reverse("user:resource-list-create")
        self.super_user1 = create_superuser(use_custom_data=True,
                                            **self.admin_user_1)
        self.super_user2 = create_superuser(use_custom_data=True,
                                            **self.admin_user_2)
        self.normal_user1 = create_user(use_custom_data=True,
                                        **self.normal_user_1)

    def register_resources(self, user_resources):
        for resource in user_resources:
            response = self.client.post(self.base_url, data=resource, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_single_resource_no_auth(self):
        data = {"name": "resource-x", "timezone": "Europe/Brussels"}
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.post(self.base_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_resource_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_register_single_resource(self):
        """
        Check if Market Maker 1 can register a resource
        """
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        response = self.client.post(self.base_url, data=resource, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["data"]
        self.assertEqual(response_data["name"], resource["name"])
        self.assertEqual(response_data["timezone"], resource["timezone"])
        # Confirm if resource entry is correctly registered in DB
        resource_id = response_data["id"]
        resource_data = UserResources.objects.filter(id=resource_id).get()
        self.assertEqual(resource_data.name, response_data["name"])
        self.assertEqual(resource_data.timezone, response_data["timezone"])

    def test_admin_list_all_resources(self):
        login_user(self.client, user=self.super_user1)
        self.register_resources(self.admin_user_1_resources)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), len(self.admin_user_1_resources))
        for resource in response_data:
            original = [x for x in self.admin_user_1_resources if x["name"] == resource["name"]]
            # Check if this resource exists in the original resource list
            # and compare its attributes to original:
            self.assertEqual(len(original), 1)
            self.assertEqual(resource["timezone"], original[0]["timezone"])

    def test_admin_list_resource_by_id(self):
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        response = self.client.post(self.base_url, data=resource, format="json")
        resource_id = response.data["id"]
        params = {"resource": resource_id}
        response = self.client.get(self.base_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(response_data[0]["id"], resource_id)

    def test_admin_list_other_admin_resource_by_id(self):
        """
        Check if Market Maker 2 can access Market Maker 1's resources by id
        """
        # login with user 1
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        response = self.client.post(self.base_url, data=resource, format="json")
        resource_id = response.data["id"]
        # login with user 2
        login_user(self.client, user=self.super_user2)
        # Try to access resource from user 1
        params = {"resource": resource_id}
        response = self.client.get(self.base_url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data), 0)

    def test_admin_delete_resource(self):
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        # Create resource:
        response = self.client.post(self.base_url, data=resource, format="json")
        self.assertTrue(response.status_code, status.HTTP_201_CREATED)
        resource_id = response.data["id"]
        # Check if resource exists:
        self.assertTrue(UserResources.objects.filter(id=resource_id))
        # Delete resource:
        response = self.client.delete(self.base_url + f"/{resource_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if resource exists:
        self.assertFalse(UserResources.objects.filter(id=resource_id))

    def test_admin_delete_other_admin_resource(self):
        # login with user 1
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        response = self.client.post(self.base_url, data=resource, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resource_id = response.data["id"]

        # login with user 2
        login_user(self.client, user=self.super_user2)
        # Try to delete resource from user 1:
        response = self.client.delete(self.base_url + f"/{resource_id}")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        # Check if resource still exists:
        self.assertTrue(UserResources.objects.filter(id=resource_id))

        login_user(self.client, user=self.super_user1)
        response = self.client.delete(self.base_url + f"/{resource_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_update_resource(self):
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        # Create resource:
        response = self.client.post(self.base_url, data=resource, format="json")
        self.assertTrue(response.status_code, status.HTTP_201_CREATED)
        resource_id = response.data["id"]
        # Check if resource exists:
        self.assertTrue(UserResources.objects.filter(id=resource_id))
        # Update resource:
        resource["name"] = "new-resource-1"
        response = self.client.patch(self.base_url + f"/{resource_id}", data=resource, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        # Check if resource ID is the same:
        self.assertEqual(response_data["id"], resource_id)
        # Check if resource name was updated:
        resource_data = UserResources.objects.get(id=resource_id)
        self.assertTrue(resource_data.name, resource["name"])

    def test_normal_list_all_resources(self):
        login_user(self.client, user=self.normal_user1)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_delete_admin_resource(self):
        # login with user 1
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        response = self.client.post(self.base_url, data=resource, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resource_id = response.data["id"]

        # login with normal user
        login_user(self.client, user=self.normal_user1)
        # Try to delete resource from user 1:
        response = self.client.delete(self.base_url + f"/{resource_id}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check if resource still exists:
        self.assertTrue(UserResources.objects.filter(id=resource_id))

    def test_normal_update_admin_resource(self):
        login_user(self.client, user=self.super_user1)
        resource = self.admin_user_1_resources[0]
        # Create resource:
        response = self.client.post(self.base_url, data=resource, format="json")
        self.assertTrue(response.status_code, status.HTTP_201_CREATED)
        resource_id = response.data["id"]

        # login with normal user
        login_user(self.client, user=self.normal_user1)
        # Try to update resource:
        resource["name"] = "new-resource-1"
        response = self.client.patch(self.base_url + f"/{resource_id}", data=resource, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

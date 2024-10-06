from django.test import TestCase
from ...models.user_notification import UserNotificationType
from ...serializers.user_notification import UserNotificationTypeSerializer


class UserNotificationTypeSerializerTestCase(TestCase):

    def setUp(self):
        self.notification_type_data = {
            'name': 'Test Notification Type'
        }

    def test_valid_serialization(self):
        """
        This method will test a valid payload
        """
        serializer = UserNotificationTypeSerializer(
            data=self.notification_type_data)
        self.assertTrue(serializer.is_valid())

    def test_duplicate_notification_type(self):
        """
        This method will check if the serializer is avoiding
        saving exact duplicates
        """
        UserNotificationType.objects.create(
            **self.notification_type_data)
        serializer = UserNotificationTypeSerializer(
            data=self.notification_type_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_similar_notification_type(self):
        """
        This method will not be valid with a similar notification
        type name inserted.
        """
        UserNotificationType.objects.create(name='Test Notification Type 2')
        serializer = UserNotificationTypeSerializer(
            data=self.notification_type_data)
        self.assertFalse(serializer.is_valid())

from django.test import TestCase
from django.contrib.auth import get_user_model
from ...models.user_notification import UserNotificationType
from ...serializers.user_notification import UserPostNotificationSerializer

User = get_user_model()


class UserNotificationSerializerTestCase(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            email='test@example.com',
            password='password'
        )
        self.notification_type = UserNotificationType.objects.create(
            name='Test Notification Type'
        )
        self.notification_data = {
            'state': True,
            'user': self.user.id,
            'notification_type': self.notification_type.id,
            'notification_title': 'Test Notification Title',
            'notification_description': 'Test Notification Description'
        }
        self.serializer = UserPostNotificationSerializer(
            data=self.notification_data)

    def test_user_notification_serialization(self):
        is_valid = self.serializer.is_valid()
        self.assertTrue(is_valid)

    def test_user_notification_deserialization(self):
        if not self.serializer.is_valid():
            print(self.serializer.errors)
        self.serializer.is_valid(raise_exception=True)
        instance = self.serializer.save()
        self.assertEqual(instance.state, True)
        self.assertEqual(instance.user, self.user)
        self.assertEqual(instance.notification_type, self.notification_type)

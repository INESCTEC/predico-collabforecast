from django.test import TestCase
from ...serializers.user import UserRegistrationSerializer
from ...models.user import User
from ...exceptions.Exception import EmailAlreadyExists


class UserRegistrationSerializerTestCase(TestCase):
    def setUp(self):
        self.valid_data = {
            "email": "testuser1@inesctec.pt",
            "password": "Testuser1password!",
            "first_name": "Test",
            "last_name": "User 1"
        }

    def test_email_already_exists(self):
        User.objects.create_user(**self.valid_data)
        serializer = UserRegistrationSerializer(data=self.valid_data)
        with self.assertRaises(EmailAlreadyExists):
            serializer.is_valid(raise_exception=True)

    def test_valid_data(self):
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_data(self):
        serializer = UserRegistrationSerializer(
            data={**self.valid_data, 'password': 'weak'})
        self.assertFalse(serializer.is_valid())

    def test_invalid_email(self):
        self.valid_data['email'] = 'invalid-email'
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors['email'][0],
            'Enter a valid email address.')

    def tearDown(self):
        User.objects.all().delete()

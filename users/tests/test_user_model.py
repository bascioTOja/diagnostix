from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from django.test import TestCase

from users.models import RoleChoices


class CustomUserModelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_create_user_sets_email_as_username(self):
        user = self.user_model.objects.create_user(
            email="client@example.com",
            first_name="Jan",
            last_name="Nowak",
            password="secret123",
        )

        self.assertEqual(user.email, "client@example.com")
        self.assertEqual(user.first_name, "Jan")
        self.assertEqual(user.last_name, "Nowak")
        self.assertEqual(user.get_full_name(), "Jan Nowak")
        self.assertEqual(user.role, RoleChoices.KLIENT)
        self.assertTrue(user.check_password("secret123"))

    def test_email_is_unique(self):
        self.user_model.objects.create_user(email="dup@example.com", password="secret123")

        with self.assertRaises(IntegrityError):
            self.user_model.objects.create_user(email="dup@example.com", password="secret456")

    def test_authenticate_by_email(self):
        self.user_model.objects.create_user(email="login@example.com", password="secret123")

        authenticated = authenticate(email="login@example.com", password="secret123")

        self.assertIsNotNone(authenticated)
        self.assertEqual(authenticated.email, "login@example.com")

    def test_create_superuser_sets_admin_role(self):
        admin = self.user_model.objects.create_superuser(
            email="admin@example.com",
            password="secret123",
        )

        self.assertEqual(admin.role, RoleChoices.ADMINISTRATOR)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)



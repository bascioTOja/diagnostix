from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import RoleChoices


class AuthProfileApiTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user_model = get_user_model()

    def test_register_positive(self):
        response = self.client_api.post(
            "/api/auth/register/",
            {
                "email": "new@user.com",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "password": "secret123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "new@user.com")
        self.assertEqual(response.data["first_name"], "Jan")
        self.assertEqual(response.data["last_name"], "Kowalski")
        self.assertEqual(response.data["role"], RoleChoices.KLIENT)

    def test_register_duplicate_email_negative(self):
        self.user_model.objects.create_user(email="dup@user.com", password="secret123")

        response = self.client_api.post(
            "/api/auth/register/",
            {
                "email": "dup@user.com",
                "first_name": "Anna",
                "last_name": "Nowak",
                "password": "secret123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "validation_error")

    def test_login_and_profile_positive(self):
        user = self.user_model.objects.create_user(
            email="profile@user.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )

        login_response = self.client_api.post(
            "/api/auth/login/",
            {"email": user.email, "password": "secret123"},
            format="json",
        )
        profile_response = self.client_api.get("/api/profile/")

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], user.email)

    def test_login_invalid_credentials_negative(self):
        self.user_model.objects.create_user(email="wrong@user.com", password="secret123")

        response = self.client_api.post(
            "/api/auth/login/",
            {"email": "wrong@user.com", "password": "badpass"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_profile_patch_positive(self):
        user = self.user_model.objects.create_user(email="edit@user.com", password="secret123")
        self.client_api.force_authenticate(user=user)

        response = self.client_api.patch(
            "/api/profile/",
            {"email": "edited@user.com", "first_name": "Edyta", "last_name": "Nowa"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "edited@user.com")
        self.assertEqual(response.data["first_name"], "Edyta")
        self.assertEqual(response.data["last_name"], "Nowa")


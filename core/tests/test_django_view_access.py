from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from users.models import RoleChoices


@override_settings(ROOT_URLCONF="core.tests.urls")
class DjangoViewAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@test.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diagnosta@test.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.client_user = user_model.objects.create_user(
            email="client@test.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )

    def test_admin_view_allows_administrator(self):
        self.client.force_login(self.admin)

        response = self.client.get("/rbac/admin-only/")

        self.assertEqual(response.status_code, 200)

    def test_admin_view_forbids_non_admin_role(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get("/rbac/admin-only/")

        self.assertEqual(response.status_code, 403)

    def test_client_resource_own_object_returns_200(self):
        self.client.force_login(self.client_user)

        response = self.client.get(f"/rbac/client-resource/{self.client_user.id}/")

        self.assertEqual(response.status_code, 200)

    def test_client_resource_foreign_object_returns_404(self):
        self.client.force_login(self.client_user)

        response = self.client.get(f"/rbac/client-resource/{self.admin.id}/")

        self.assertEqual(response.status_code, 404)

    def test_client_resource_wrong_role_returns_403(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(f"/rbac/client-resource/{self.diagnosta.id}/")

        self.assertEqual(response.status_code, 403)

    def test_diagnosta_assignment_own_object_returns_200(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(f"/rbac/diagnosta-assignment/{self.diagnosta.id}/")

        self.assertEqual(response.status_code, 200)

    def test_diagnosta_assignment_foreign_object_returns_404(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(f"/rbac/diagnosta-assignment/{self.admin.id}/")

        self.assertEqual(response.status_code, 404)

    def test_diagnosta_assignment_wrong_role_returns_403(self):
        self.client.force_login(self.client_user)

        response = self.client.get(f"/rbac/diagnosta-assignment/{self.diagnosta.id}/")

        self.assertEqual(response.status_code, 403)


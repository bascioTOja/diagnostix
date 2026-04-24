from django.contrib.auth import get_user_model
from django.test import TestCase

from users.models import RoleChoices


class AdminSiteAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@panel.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client@panel.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )

    def test_admin_role_can_open_admin_index(self):
        self.client.force_login(self.admin)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)

    def test_non_admin_role_cannot_open_admin_index(self):
        self.client.force_login(self.client_user)

        response = self.client.get("/admin/")

        self.assertNotEqual(response.status_code, 200)


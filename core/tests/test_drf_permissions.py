from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from rest_framework.exceptions import NotFound
from rest_framework.test import APIRequestFactory

from core.common.permissions import IsAdministrator, IsDiagnostaAssignedOr404, IsKlientOwnerOr404
from users.models import RoleChoices


class DrfPermissionsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@api.com", password="secret123", role=RoleChoices.ADMINISTRATOR
        )
        self.diagnosta = user_model.objects.create_user(
            email="diagnosta@api.com", password="secret123", role=RoleChoices.DIAGNOSTA
        )
        self.client_user = user_model.objects.create_user(
            email="client@api.com", password="secret123", role=RoleChoices.KLIENT
        )
        self.factory = APIRequestFactory()

    def _request_for_user(self, user):
        request = self.factory.get("/api/test/")
        request.user = user
        return request

    def test_admin_permission_positive(self):
        permission = IsAdministrator()
        request = self._request_for_user(self.admin)

        self.assertTrue(permission.has_permission(request, view=SimpleNamespace()))

    def test_admin_permission_negative_raises_403(self):
        permission = IsAdministrator()
        request = self._request_for_user(self.client_user)

        with self.assertRaises(PermissionDenied):
            permission.has_permission(request, view=SimpleNamespace())

    def test_client_object_permission_positive(self):
        permission = IsKlientOwnerOr404()
        request = self._request_for_user(self.client_user)
        obj = SimpleNamespace(owner_id=self.client_user.id)

        self.assertTrue(permission.has_object_permission(request, SimpleNamespace(), obj))

    def test_client_object_permission_foreign_returns_404(self):
        permission = IsKlientOwnerOr404()
        request = self._request_for_user(self.client_user)
        obj = SimpleNamespace(owner_id=self.admin.id)

        with self.assertRaises(NotFound):
            permission.has_object_permission(request, SimpleNamespace(), obj)

    def test_diagnosta_object_permission_positive(self):
        permission = IsDiagnostaAssignedOr404()
        request = self._request_for_user(self.diagnosta)
        obj = SimpleNamespace(diagnosta_id=self.diagnosta.id)

        self.assertTrue(permission.has_object_permission(request, SimpleNamespace(), obj))

    def test_diagnosta_object_permission_foreign_returns_404(self):
        permission = IsDiagnostaAssignedOr404()
        request = self._request_for_user(self.diagnosta)
        obj = SimpleNamespace(diagnosta_id=self.admin.id)

        with self.assertRaises(NotFound):
            permission.has_object_permission(request, SimpleNamespace(), obj)



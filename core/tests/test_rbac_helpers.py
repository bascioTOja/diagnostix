from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.common.rbac import (
    RBAC_RULES,
    ROLE_ADMINISTRATOR,
    ROLE_DIAGNOSTA,
    ROLE_KLIENT,
    action_allowed,
    is_assigned_diagnosta,
    is_owner,
)


class RbacHelpersTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@ex.com", password="secret123", role=ROLE_ADMINISTRATOR
        )
        self.client_user = user_model.objects.create_user(
            email="client@ex.com", password="secret123", role=ROLE_KLIENT
        )
        self.diagnosta = user_model.objects.create_user(
            email="diagnosta@ex.com", password="secret123", role=ROLE_DIAGNOSTA
        )

    def test_action_allowed_uses_central_matrix(self):
        self.assertIn("admin.panel", RBAC_RULES)
        self.assertTrue(action_allowed(self.admin, "admin.panel"))
        self.assertFalse(action_allowed(self.client_user, "admin.panel"))

    def test_owner_helper(self):
        own_object = SimpleNamespace(owner_id=self.client_user.id)
        other_object = SimpleNamespace(owner_id=self.admin.id)

        self.assertTrue(is_owner(self.client_user, own_object))
        self.assertFalse(is_owner(self.client_user, other_object))

    def test_assigned_diagnosta_helper(self):
        assigned_object = SimpleNamespace(diagnosta_id=self.diagnosta.id)
        other_object = SimpleNamespace(diagnosta_id=self.admin.id)

        self.assertTrue(is_assigned_diagnosta(self.diagnosta, assigned_object))
        self.assertFalse(is_assigned_diagnosta(self.diagnosta, other_object))


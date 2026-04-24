from __future__ import annotations

from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound

from core.common.rbac import (
    ROLE_ADMINISTRATOR,
    ROLE_DIAGNOSTA,
    ROLE_KLIENT,
    is_assigned_diagnosta,
    is_owner,
    user_has_any_role,
)


class RoleRequiredPermission(BasePermission):
    required_roles: tuple[str, ...] = tuple()

    def has_permission(self, request, view):
        roles = getattr(view, "required_roles", self.required_roles)
        if user_has_any_role(request.user, roles):
            return True
        if request.user.is_authenticated:
            raise PermissionDenied("Brak wymaganej roli.")
        return False


class IsAdministrator(RoleRequiredPermission):
    required_roles = (ROLE_ADMINISTRATOR,)


class IsDiagnosta(RoleRequiredPermission):
    required_roles = (ROLE_DIAGNOSTA,)


class IsKlient(RoleRequiredPermission):
    required_roles = (ROLE_KLIENT,)


class IsKlientOwnerOr404(IsKlient):
    owner_attr = "owner_id"

    def has_object_permission(self, request, view, obj):
        if not super().has_permission(request, view):
            return False
        owner_attr = getattr(view, "owner_attr", self.owner_attr)
        if not is_owner(request.user, obj, owner_attr=owner_attr):
            raise NotFound("Zasob nie istnieje.")
        return True


class IsDiagnostaAssignedOr404(IsDiagnosta):
    diagnosta_attr = "diagnosta_id"

    def has_object_permission(self, request, view, obj):
        if not super().has_permission(request, view):
            return False
        diagnosta_attr = getattr(view, "diagnosta_attr", self.diagnosta_attr)
        if not is_assigned_diagnosta(request.user, obj, diagnosta_attr=diagnosta_attr):
            raise NotFound("Zasob nie istnieje.")
        return True


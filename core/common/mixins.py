from __future__ import annotations

from django.contrib.auth.mixins import AccessMixin
from django.http import Http404, HttpResponseForbidden

from core.common.rbac import (
    ROLE_DIAGNOSTA,
    ROLE_KLIENT,
    is_assigned_diagnosta,
    is_owner,
    user_has_any_role,
)


class RoleRequiredMixin(AccessMixin):
    allowed_roles: tuple[str, ...] = tuple()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_has_any_role(request.user, self.allowed_roles):
            return HttpResponseForbidden("Brak wymaganej roli.")
        return super().dispatch(request, *args, **kwargs)


class ClientOwnerOr404Mixin:
    owner_attr = "owner_id"

    def enforce_client_owner_or_404(self, request, obj):
        if not user_has_any_role(request.user, (ROLE_KLIENT,)):
            return HttpResponseForbidden("Brak wymaganej roli.")
        if not is_owner(request.user, obj, owner_attr=self.owner_attr):
            raise Http404("Zasob nie istnieje.")
        return None


class DiagnostaAssignedOr404Mixin:
    diagnosta_attr = "diagnosta_id"

    def enforce_diagnosta_assigned_or_404(self, request, obj):
        if not user_has_any_role(request.user, (ROLE_DIAGNOSTA,)):
            return HttpResponseForbidden("Brak wymaganej roli.")
        if not is_assigned_diagnosta(request.user, obj, diagnosta_attr=self.diagnosta_attr):
            raise Http404("Zasob nie istnieje.")
        return None


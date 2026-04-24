from types import SimpleNamespace

from django.http import HttpResponse
from django.views import View

from core.common.mixins import ClientOwnerOr404Mixin, DiagnostaAssignedOr404Mixin, RoleRequiredMixin
from core.common.rbac import ROLE_ADMINISTRATOR


class AdminOnlyView(RoleRequiredMixin, View):
    allowed_roles = (ROLE_ADMINISTRATOR,)

    def get(self, request):
        return HttpResponse("ok")


class ClientResourceView(ClientOwnerOr404Mixin, View):
    def get(self, request, owner_id: int):
        obj = SimpleNamespace(owner_id=owner_id)
        denied_response = self.enforce_client_owner_or_404(request, obj)
        if denied_response is not None:
            return denied_response
        return HttpResponse("ok")


class DiagnostaAssignmentView(DiagnostaAssignedOr404Mixin, View):
    def get(self, request, diagnosta_id: int):
        obj = SimpleNamespace(diagnosta_id=diagnosta_id)
        denied_response = self.enforce_diagnosta_assigned_or_404(request, obj)
        if denied_response is not None:
            return denied_response
        return HttpResponse("ok")


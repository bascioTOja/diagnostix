from __future__ import annotations

from django.db.models import QuerySet
from rest_framework.exceptions import PermissionDenied

from inspections.models import Inspection
from users.models import RoleChoices


def inspection_history_for_user(user) -> QuerySet[Inspection]:
    base_queryset = Inspection.objects.select_related(
        "appointment",
        "appointment__vehicle",
        "appointment__client",
        "diagnostician",
    ).order_by("-created_at")

    if user.role == RoleChoices.ADMINISTRATOR:
        return base_queryset
    if user.role == RoleChoices.DIAGNOSTA:
        return base_queryset.filter(appointment__assigned_diagnostician=user)
    if user.role == RoleChoices.KLIENT:
        return base_queryset.filter(appointment__client=user)
    raise PermissionDenied("Brak wymaganej roli.")


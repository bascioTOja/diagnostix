from __future__ import annotations

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, PermissionDenied

from users.models import RoleChoices
from vehicles.models import Vehicle


def vehicles_for_user(user) -> QuerySet[Vehicle]:
    if user.role == RoleChoices.ADMINISTRATOR:
        return Vehicle.objects.all().order_by("id")
    if user.role == RoleChoices.KLIENT:
        return Vehicle.objects.filter(owner=user).order_by("id")
    if user.role == RoleChoices.DIAGNOSTA:
        return Vehicle.objects.filter(appointments__assigned_diagnostician=user).distinct().order_by("id")
    raise PermissionDenied("Brak wymaganej roli.")


def get_vehicle_for_user_or_404(user, vehicle_id: int) -> Vehicle:
    queryset = vehicles_for_user(user)
    try:
        return queryset.get(pk=vehicle_id)
    except Vehicle.DoesNotExist as exc:
        raise NotFound("Zasob nie istnieje.") from exc


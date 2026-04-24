from __future__ import annotations

from django.db.models import QuerySet
from rest_framework.exceptions import PermissionDenied

from appointments.models import Appointment
from users.models import RoleChoices


def appointments_for_user(user) -> QuerySet[Appointment]:
    if user.role == RoleChoices.ADMINISTRATOR:
        return Appointment.objects.select_related("vehicle", "station", "client", "assigned_diagnostician").order_by("-scheduled_at")
    if user.role == RoleChoices.KLIENT:
        return Appointment.objects.select_related("vehicle", "station", "client", "assigned_diagnostician").filter(client=user).order_by("-scheduled_at")
    if user.role == RoleChoices.DIAGNOSTA:
        return Appointment.objects.select_related("vehicle", "station", "client", "assigned_diagnostician").filter(assigned_diagnostician=user).order_by("-scheduled_at")
    raise PermissionDenied("Brak wymaganej roli.")


def diagnostician_schedule(user) -> QuerySet[Appointment]:
    if user.role != RoleChoices.DIAGNOSTA:
        raise PermissionDenied("Brak wymaganej roli.")
    return Appointment.objects.select_related("vehicle", "station", "client").filter(assigned_diagnostician=user).order_by("scheduled_at")


from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from appointments.models import Appointment, AppointmentStatusChoices
from users.models import RoleChoices
def create_appointment_for_client(user, validated_data: dict) -> Appointment:
    if user.role != RoleChoices.KLIENT:
        raise PermissionDenied("Brak wymaganej roli.")

    vehicle = validated_data["vehicle"]
    if vehicle.owner_id != user.id:
        raise NotFound("Zasob nie istnieje.")

    validated_data["client"] = user
    validated_data["created_by"] = user
    try:
        return Appointment.objects.create(**validated_data)
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict) from exc


@transaction.atomic
def cancel_appointment_for_user(user, appointment_id: int) -> Appointment:
    try:
        appointment = Appointment.objects.select_for_update().get(pk=appointment_id)
    except Appointment.DoesNotExist as exc:
        raise NotFound("Zasob nie istnieje.") from exc

    if user.role == RoleChoices.KLIENT and appointment.client_id != user.id:
        raise NotFound("Zasob nie istnieje.")
    if user.role not in (RoleChoices.KLIENT, RoleChoices.ADMINISTRATOR):
        raise PermissionDenied("Brak wymaganej roli.")

    if appointment.status in (AppointmentStatusChoices.COMPLETED, AppointmentStatusChoices.CANCELLED):
        raise PermissionDenied("Nie mozna anulowac tej wizyty.")

    appointment.status = AppointmentStatusChoices.CANCELLED
    appointment.save(update_fields=["status", "updated_at"])
    return appointment




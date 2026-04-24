from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied, ValidationError

from users.models import RoleChoices
from vehicles.models import Vehicle


def create_vehicle_for_user(user, validated_data: dict) -> Vehicle:
    if user.role != RoleChoices.KLIENT:
        raise PermissionDenied("Brak wymaganej roli.")
    try:
        return Vehicle.objects.create(owner=user, **validated_data)
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict) from exc


def update_vehicle_for_user(user, vehicle: Vehicle, validated_data: dict) -> Vehicle:
    if user.role != RoleChoices.KLIENT:
        raise PermissionDenied("Brak wymaganej roli.")
    if vehicle.owner_id != user.id:
        raise PermissionDenied("Brak dostepu do zasobu.")

    for key, value in validated_data.items():
        setattr(vehicle, key, value)
    try:
        vehicle.save()
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    return vehicle


def delete_vehicle_for_user(user, vehicle: Vehicle) -> None:
    if user.role == RoleChoices.ADMINISTRATOR:
        vehicle.delete()
        return
    if user.role == RoleChoices.KLIENT and vehicle.owner_id == user.id:
        vehicle.delete()
        return
    raise PermissionDenied("Brak dostepu do zasobu.")



from __future__ import annotations

import datetime
import itertools

from django.contrib.auth import get_user_model
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionResultChoices
from notifications.models import Notification, NotificationChannelChoices, NotificationStatusChoices, NotificationTypeChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle, VehicleTypeChoices

_counter = itertools.count(1)


def _next_id() -> int:
    return next(_counter)


def create_user(*, role: str = RoleChoices.KLIENT, is_staff: bool | None = None, password: str = "secret123"):
    idx = _next_id()
    if is_staff is None:
        is_staff = role == RoleChoices.ADMINISTRATOR

    return get_user_model().objects.create_user(
        email=f"user{idx}@factory.com",
        password=password,
        role=role,
        is_staff=is_staff,
    )


def create_station(*, is_active: bool = True, slot_duration_minutes: int = 30) -> DiagnosticStation:
    idx = _next_id()
    return DiagnosticStation.objects.create(
        name=f"Factory Station {idx}",
        is_active=is_active,
        slot_duration_minutes=slot_duration_minutes,
    )


def create_vehicle(*, owner, vehicle_type: str = VehicleTypeChoices.PASSENGER) -> Vehicle:
    idx = _next_id()
    return Vehicle.objects.create(
        owner=owner,
        registration_number=f"WF{idx:05d}",
        vin=f"WVWZZZ1JZXW{idx:06d}",
        make="Factory",
        model=f"Model{idx}",
        production_year=2020,
        vehicle_type=vehicle_type,
    )


def create_appointment(
    *,
    vehicle: Vehicle,
    client,
    station: DiagnosticStation,
    assigned_diagnostician=None,
    status: str = AppointmentStatusChoices.SCHEDULED,
    scheduled_at=None,
    created_by=None,
) -> Appointment:
    if scheduled_at is None:
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
    if created_by is None:
        created_by = client

    return Appointment.objects.create(
        vehicle=vehicle,
        client=client,
        station=station,
        scheduled_at=scheduled_at,
        status=status,
        assigned_diagnostician=assigned_diagnostician,
        created_by=created_by,
    )


def create_inspection(
    *,
    appointment: Appointment,
    diagnostician,
    result: str = InspectionResultChoices.PASSED,
    next_inspection_date=None,
) -> Inspection:
    return Inspection.objects.create(
        appointment=appointment,
        result=result,
        diagnostician=diagnostician,
        next_inspection_date=next_inspection_date,
    )


def create_notification(
    *,
    user,
    notification_type: str = NotificationTypeChoices.SYSTEM,
    status: str = NotificationStatusChoices.PENDING,
    dedupe_key: str | None = None,
) -> Notification:
    scheduled_for = timezone.now() + datetime.timedelta(hours=1)
    sent_at = timezone.now() if status == NotificationStatusChoices.SENT else None
    return Notification.objects.create(
        user=user,
        type=notification_type,
        channel=NotificationChannelChoices.IN_APP,
        status=status,
        scheduled_for=scheduled_for,
        sent_at=sent_at,
        dedupe_key=dedupe_key,
        payload={"factory": True},
    )


from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.common.models import TimeStampedModel
from users.models import RoleChoices


class AppointmentStatusChoices(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No show"


ACTIVE_APPOINTMENT_STATUSES = (
    AppointmentStatusChoices.SCHEDULED,
    AppointmentStatusChoices.CONFIRMED,
)


class Appointment(TimeStampedModel):
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments_as_client",
    )
    station = models.ForeignKey(
        "vehicles.DiagnosticStation",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=16,
        choices=AppointmentStatusChoices,
        default=AppointmentStatusChoices.SCHEDULED,
    )
    assigned_diagnostician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments_as_diagnostician",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments_created",
    )

    class Meta:
        indexes = [
            models.Index(fields=["scheduled_at"], name="appointment_sched_idx"),
            models.Index(fields=["status"], name="appointment_status_idx"),
            models.Index(fields=["scheduled_at", "status"], name="appointment_sched_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle", "scheduled_at"],
                condition=models.Q(status__in=ACTIVE_APPOINTMENT_STATUSES),
                name="appointment_unique_vehicle_slot_active",
            ),
            models.UniqueConstraint(
                fields=["station", "scheduled_at"],
                condition=models.Q(status__in=ACTIVE_APPOINTMENT_STATUSES),
                name="appointment_unique_station_slot_active",
            ),
            models.UniqueConstraint(
                fields=["assigned_diagnostician", "scheduled_at"],
                condition=models.Q(
                    status__in=ACTIVE_APPOINTMENT_STATUSES,
                    assigned_diagnostician__isnull=False,
                ),
                name="appointment_unique_diagnostician_slot_active",
            ),
        ]

    def clean(self):
        super().clean()
        if self.client_id and self.vehicle_id and self.vehicle.owner_id != self.client_id:
            raise ValidationError({"client": "Klient wizyty musi byc wlascicielem pojazdu."})

        if self.client_id and self.client.role != RoleChoices.KLIENT:
            raise ValidationError({"client": "Klient wizyty musi miec role klient."})

        if self.assigned_diagnostician_id and self.assigned_diagnostician.role != RoleChoices.DIAGNOSTA:
            raise ValidationError({"assigned_diagnostician": "Przypisany uzytkownik musi miec role diagnosta."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


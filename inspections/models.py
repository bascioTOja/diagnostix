from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.common.models import TimeStampedModel
from users.models import RoleChoices


class InspectionResultChoices(models.TextChoices):
    PASSED = "passed", "Pozytywny"
    FAILED = "failed", "Negatywny"
    CONDITIONAL = "conditional", "Warunkowy"


class Inspection(TimeStampedModel):
    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        related_name="inspection",
    )
    result = models.CharField(max_length=16, choices=InspectionResultChoices)
    notes = models.TextField(blank=True)
    detected_defects = models.TextField(blank=True, default="")
    repair_recommendations = models.TextField(blank=True, default="")
    next_inspection_date = models.DateField(null=True, blank=True)
    diagnostician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspections",
    )

    class Meta:
        indexes = [
            models.Index(fields=["result"], name="inspection_result_idx"),
        ]

    def clean(self):
        super().clean()
        if self.diagnostician.role != RoleChoices.DIAGNOSTA:
            raise ValidationError({"diagnostician": "Badanie moze zapisac tylko diagnosta."})

        if (
            self.appointment.assigned_diagnostician_id
            and self.appointment.assigned_diagnostician_id != self.diagnostician_id
        ):
            raise ValidationError({"diagnostician": "Diagnosta musi byc przypisany do wizyty."})

        if self.result == InspectionResultChoices.FAILED and not self.next_inspection_date:
            raise ValidationError({"next_inspection_date": "Dla wyniku negatywnego podaj date kolejnego badania."})

        if self.result == InspectionResultChoices.PASSED and self.next_inspection_date:
            raise ValidationError({"next_inspection_date": "Dla wyniku pozytywnego data kolejnego badania nie jest wymagana."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class InspectionAuditEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        INSPECTION_FINALIZED = "inspection_finalized", "Inspection finalized"

    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="inspection_audit_events",
    )
    inspection = models.ForeignKey(
        "inspections.Inspection",
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspection_audit_events",
    )
    event_type = models.CharField(max_length=64, choices=EventType)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["appointment", "created_at"], name="insp_audit_app_created_idx"),
            models.Index(fields=["event_type", "created_at"], name="insp_audit_event_created_idx"),
        ]



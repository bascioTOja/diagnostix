from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionAuditEvent
from users.models import RoleChoices


@transaction.atomic
def finalize_inspection(*, appointment_id: int, diagnostician, payload: dict) -> Inspection:
    if diagnostician.role != RoleChoices.DIAGNOSTA:
        raise PermissionDenied("Brak wymaganej roli.")

    try:
        appointment = Appointment.objects.select_for_update().get(pk=appointment_id)
    except Appointment.DoesNotExist as exc:
        raise NotFound("Zasob nie istnieje.") from exc

    if appointment.assigned_diagnostician_id != diagnostician.id:
        raise NotFound("Zasob nie istnieje.")

    if appointment.status not in (AppointmentStatusChoices.SCHEDULED, AppointmentStatusChoices.CONFIRMED):
        raise ValidationError({"status": "Wizyta nie moze byc finalizowana w tym statusie."})

    try:
        inspection, _ = Inspection.objects.update_or_create(
            appointment=appointment,
            defaults={
                "result": payload["result"],
                "notes": payload.get("notes", ""),
                "detected_defects": payload.get("detected_defects", ""),
                "repair_recommendations": payload.get("repair_recommendations", ""),
                "next_inspection_date": payload.get("next_inspection_date"),
                "diagnostician": diagnostician,
            },
        )
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict) from exc

    appointment.status = AppointmentStatusChoices.COMPLETED
    appointment.save(update_fields=["status", "updated_at"])

    InspectionAuditEvent.objects.create(
        appointment=appointment,
        inspection=inspection,
        actor=diagnostician,
        event_type=InspectionAuditEvent.EventType.INSPECTION_FINALIZED,
        payload={
            "result": inspection.result,
            "detected_defects": inspection.detected_defects,
            "repair_recommendations": inspection.repair_recommendations,
            "next_inspection_date": str(inspection.next_inspection_date) if inspection.next_inspection_date else None,
        },
    )

    return inspection



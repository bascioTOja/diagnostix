from __future__ import annotations

from datetime import date

from django.db.models import Count, QuerySet
from django.db.models.functions import TruncDate, TruncMonth

from appointments.models import AppointmentStatusChoices
from inspections.models import Inspection
from vehicles.models import Vehicle


def completed_inspections_queryset(*, date_from: date, date_to: date) -> QuerySet[Inspection]:
    return Inspection.objects.filter(
        appointment__status=AppointmentStatusChoices.COMPLETED,
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )


def completed_inspections_total(*, date_from: date, date_to: date) -> int:
    return completed_inspections_queryset(date_from=date_from, date_to=date_to).count()


def completed_inspections_daily(*, date_from: date, date_to: date):
    return (
        completed_inspections_queryset(date_from=date_from, date_to=date_to)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )


def completed_inspections_monthly(*, date_from: date, date_to: date):
    return (
        completed_inspections_queryset(date_from=date_from, date_to=date_to)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )


def top_inspected_vehicle_types(*, date_from: date, date_to: date):
    return (
        completed_inspections_queryset(date_from=date_from, date_to=date_to)
        .values("appointment__vehicle__vehicle_type")
        .annotate(inspections_count=Count("id"))
        .order_by("-inspections_count", "appointment__vehicle__vehicle_type")
    )


def vehicles_total() -> int:
    return Vehicle.objects.count()


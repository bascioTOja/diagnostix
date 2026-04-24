from __future__ import annotations

import datetime

from celery import shared_task
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from appointments.models import ACTIVE_APPOINTMENT_STATUSES, Appointment
from inspections.models import Inspection
from notifications.models import (
    Notification,
    NotificationChannelChoices,
    NotificationStatusChoices,
    NotificationTypeChoices,
)


def _create_sent_notification(*, user_id: int, notification_type: str, dedupe_key: str, payload: dict, scheduled_for=None) -> bool:
    scheduled_for = scheduled_for or timezone.now()
    try:
        with transaction.atomic():
            Notification.objects.create(
                user_id=user_id,
                type=notification_type,
                channel=NotificationChannelChoices.IN_APP,
                status=NotificationStatusChoices.SENT,
                scheduled_for=scheduled_for,
                sent_at=timezone.now(),
                dedupe_key=dedupe_key,
                payload=payload,
            )
    except (IntegrityError, ValidationError):
        return False
    return True


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_inspection_result_notification(inspection_id: int) -> bool:
    try:
        inspection = Inspection.objects.select_related("appointment__client").get(pk=inspection_id)
    except Inspection.DoesNotExist:
        return False

    dedupe_key = f"inspection_result:{inspection.id}"
    payload = {
        "inspection_id": inspection.id,
        "appointment_id": inspection.appointment_id,
        "result": inspection.result,
    }
    return _create_sent_notification(
        user_id=inspection.appointment.client_id,
        notification_type=NotificationTypeChoices.INSPECTION_RESULT,
        dedupe_key=dedupe_key,
        payload=payload,
    )


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_appointment_reminder(appointment_id: int) -> bool:
    try:
        appointment = Appointment.objects.select_related("client").get(pk=appointment_id)
    except Appointment.DoesNotExist:
        return False

    if appointment.status not in ACTIVE_APPOINTMENT_STATUSES:
        return False

    dedupe_key = f"appointment_reminder:{appointment.id}:24h"
    payload = {
        "appointment_id": appointment.id,
        "scheduled_at": appointment.scheduled_at.isoformat(),
    }
    return _create_sent_notification(
        user_id=appointment.client_id,
        notification_type=NotificationTypeChoices.APPOINTMENT_REMINDER,
        dedupe_key=dedupe_key,
        payload=payload,
        scheduled_for=appointment.scheduled_at - datetime.timedelta(hours=24),
    )


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_expiration_warning(inspection_id: int, days_before: int) -> bool:
    if days_before not in (30, 7):
        return False

    try:
        inspection = Inspection.objects.select_related("appointment__client").get(pk=inspection_id)
    except Inspection.DoesNotExist:
        return False

    if not inspection.next_inspection_date:
        return False

    notify_date = inspection.next_inspection_date - datetime.timedelta(days=days_before)
    notify_at = timezone.make_aware(datetime.datetime.combine(notify_date, datetime.time(hour=9, minute=0)))

    dedupe_key = f"expiration_warning:{inspection.id}:{days_before}d"
    payload = {
        "inspection_id": inspection.id,
        "appointment_id": inspection.appointment_id,
        "next_inspection_date": inspection.next_inspection_date.isoformat(),
        "days_before": days_before,
    }
    return _create_sent_notification(
        user_id=inspection.appointment.client_id,
        notification_type=NotificationTypeChoices.SYSTEM,
        dedupe_key=dedupe_key,
        payload=payload,
        scheduled_for=notify_at,
    )


@shared_task
def enqueue_appointment_reminders(hours_before: int = 24, lookahead_minutes: int = 15) -> int:
    now = timezone.now()
    window_start = now + datetime.timedelta(hours=hours_before)
    window_end = window_start + datetime.timedelta(minutes=lookahead_minutes)

    appointment_ids = list(
        Appointment.objects.filter(
            status__in=ACTIVE_APPOINTMENT_STATUSES,
            scheduled_at__gte=window_start,
            scheduled_at__lt=window_end,
        ).values_list("id", flat=True)
    )

    for appointment_id in appointment_ids:
        send_appointment_reminder.delay(appointment_id=appointment_id)

    return len(appointment_ids)


@shared_task
def enqueue_expiration_warnings(days_before: int) -> int:
    if days_before not in (30, 7):
        return 0

    target_date = timezone.localdate() + datetime.timedelta(days=days_before)
    inspection_ids = list(
        Inspection.objects.filter(next_inspection_date=target_date).values_list("id", flat=True)
    )

    for inspection_id in inspection_ids:
        send_expiration_warning.delay(inspection_id=inspection_id, days_before=days_before)

    return len(inspection_ids)




from __future__ import annotations

import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from appointments.models import ACTIVE_APPOINTMENT_STATUSES, Appointment
from inspections.models import Inspection
from notifications.tasks import (
    send_appointment_reminder,
    send_expiration_warning,
    send_inspection_result_notification,
)


@receiver(post_save, sender=Appointment)
def appointment_post_save(sender, instance: Appointment, created: bool, **kwargs):
    if not created or instance.status not in ACTIVE_APPOINTMENT_STATUSES:
        return

    eta = instance.scheduled_at - datetime.timedelta(hours=24)
    if eta <= timezone.now():
        send_appointment_reminder.delay(appointment_id=instance.id)
    else:
        send_appointment_reminder.apply_async(kwargs={"appointment_id": instance.id}, eta=eta)


@receiver(post_save, sender=Inspection)
def inspection_post_save(sender, instance: Inspection, created: bool, **kwargs):
    if not created:
        return

    send_inspection_result_notification.delay(inspection_id=instance.id)

    if not instance.next_inspection_date:
        return

    for days_before in (30, 7):
        eta_date = instance.next_inspection_date - datetime.timedelta(days=days_before)
        eta = timezone.make_aware(datetime.datetime.combine(eta_date, datetime.time(hour=9, minute=0)))
        if eta <= timezone.now():
            send_expiration_warning.delay(inspection_id=instance.id, days_before=days_before)
        else:
            send_expiration_warning.apply_async(
                kwargs={"inspection_id": instance.id, "days_before": days_before},
                eta=eta,
            )


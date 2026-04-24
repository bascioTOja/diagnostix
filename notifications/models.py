from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.common.models import TimeStampedModel


class NotificationTypeChoices(models.TextChoices):
    APPOINTMENT_REMINDER = "appointment_reminder", "Appointment reminder"
    APPOINTMENT_STATUS = "appointment_status", "Appointment status"
    INSPECTION_RESULT = "inspection_result", "Inspection result"
    SYSTEM = "system", "System"


class NotificationChannelChoices(models.TextChoices):
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    IN_APP = "in_app", "In-app"


class NotificationStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Notification(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=32, choices=NotificationTypeChoices)
    channel = models.CharField(max_length=16, choices=NotificationChannelChoices)
    status = models.CharField(
        max_length=16,
        choices=NotificationStatusChoices,
        default=NotificationStatusChoices.PENDING,
    )
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    dedupe_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["scheduled_for"], name="notification_sched_idx"),
            models.Index(fields=["status"], name="notification_status_idx"),
            models.Index(fields=["status", "scheduled_for"], name="notification_status_sched_idx"),
        ]

    def clean(self):
        super().clean()
        if self.status == NotificationStatusChoices.SENT and not self.sent_at:
            raise ValidationError({"sent_at": "sent_at jest wymagane gdy status to sent."})

        if self.status == NotificationStatusChoices.PENDING and self.sent_at:
            raise ValidationError({"sent_at": "sent_at nie moze byc ustawione dla pending."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


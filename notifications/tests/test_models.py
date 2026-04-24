import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from notifications.models import (
    Notification,
    NotificationChannelChoices,
    NotificationStatusChoices,
    NotificationTypeChoices,
)
from users.models import RoleChoices


class NotificationModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            email="client@notify.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )

    def test_create_pending_notification_positive(self):
        notification = Notification.objects.create(
            user=self.client_user,
            type=NotificationTypeChoices.APPOINTMENT_REMINDER,
            channel=NotificationChannelChoices.EMAIL,
            status=NotificationStatusChoices.PENDING,
            scheduled_for=timezone.now() + datetime.timedelta(hours=2),
            payload={"appointment_id": 1},
        )

        self.assertEqual(notification.status, NotificationStatusChoices.PENDING)

    def test_sent_requires_sent_at_negative(self):
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                user=self.client_user,
                type=NotificationTypeChoices.APPOINTMENT_STATUS,
                channel=NotificationChannelChoices.IN_APP,
                status=NotificationStatusChoices.SENT,
                scheduled_for=timezone.now(),
                payload={},
            )

    def test_pending_cannot_have_sent_at_negative(self):
        with self.assertRaises(ValidationError):
            Notification.objects.create(
                user=self.client_user,
                type=NotificationTypeChoices.SYSTEM,
                channel=NotificationChannelChoices.SMS,
                status=NotificationStatusChoices.PENDING,
                scheduled_for=timezone.now(),
                sent_at=timezone.now(),
                payload={},
            )


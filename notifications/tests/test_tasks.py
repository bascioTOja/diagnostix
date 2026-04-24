import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionResultChoices
from notifications.models import Notification, NotificationTypeChoices
from notifications.tasks import (
    enqueue_appointment_reminders,
    enqueue_expiration_warnings,
    send_appointment_reminder,
    send_expiration_warning,
    send_inspection_result_notification,
)
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class NotificationTaskTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            email="client@tasks.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@tasks.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )

        self.station = DiagnosticStation.objects.create(name="Stacja Tasks", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WT12345",
            vin="WVWZZZ1JZXW123456",
            make="VW",
            model="Golf",
            production_year=2020,
        )
        self.appointment = Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            status=AppointmentStatusChoices.CONFIRMED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )
        self.inspection = Inspection.objects.create(
            appointment=self.appointment,
            result=InspectionResultChoices.PASSED,
            diagnostician=self.diagnosta,
        )

    def test_send_inspection_result_notification_creates_notification(self):
        created = send_inspection_result_notification.run(inspection_id=self.inspection.id)

        self.assertTrue(created)
        notification = Notification.objects.get(dedupe_key=f"inspection_result:{self.inspection.id}")
        self.assertEqual(notification.type, NotificationTypeChoices.INSPECTION_RESULT)
        self.assertEqual(notification.user_id, self.client_user.id)

    def test_send_inspection_result_notification_is_idempotent_negative(self):
        send_inspection_result_notification.run(inspection_id=self.inspection.id)
        created = send_inspection_result_notification.run(inspection_id=self.inspection.id)

        self.assertFalse(created)
        self.assertEqual(Notification.objects.filter(dedupe_key=f"inspection_result:{self.inspection.id}").count(), 1)

    def test_send_appointment_reminder_skips_completed_appointment_negative(self):
        self.appointment.status = AppointmentStatusChoices.COMPLETED
        self.appointment.save(update_fields=["status", "updated_at"])

        created = send_appointment_reminder.run(appointment_id=self.appointment.id)

        self.assertFalse(created)
        self.assertEqual(Notification.objects.count(), 0)

    def test_send_expiration_warning_creates_notification(self):
        self.inspection.result = InspectionResultChoices.FAILED
        self.inspection.next_inspection_date = timezone.localdate() + datetime.timedelta(days=40)
        self.inspection.save(update_fields=["result", "next_inspection_date", "updated_at"])

        created = send_expiration_warning.run(inspection_id=self.inspection.id, days_before=30)

        self.assertTrue(created)
        notification = Notification.objects.get(dedupe_key=f"expiration_warning:{self.inspection.id}:30d")
        self.assertEqual(notification.user_id, self.client_user.id)

    def test_send_expiration_warning_skips_when_missing_next_date_negative(self):
        created = send_expiration_warning.run(inspection_id=self.inspection.id, days_before=30)

        self.assertFalse(created)
        self.assertEqual(Notification.objects.count(), 0)

    @patch("notifications.tasks.send_appointment_reminder.delay")
    def test_enqueue_appointment_reminders_dispatches_tasks(self, reminder_delay):
        self.appointment.scheduled_at = timezone.now() + datetime.timedelta(hours=24, minutes=5)
        self.appointment.save(update_fields=["scheduled_at", "updated_at"])

        count = enqueue_appointment_reminders(hours_before=24, lookahead_minutes=15)

        self.assertEqual(count, 1)
        reminder_delay.assert_called_once_with(appointment_id=self.appointment.id)

    @patch("notifications.tasks.send_expiration_warning.delay")
    def test_enqueue_expiration_warnings_dispatches_tasks(self, warning_delay):
        self.inspection.result = InspectionResultChoices.FAILED
        self.inspection.next_inspection_date = timezone.localdate() + datetime.timedelta(days=30)
        self.inspection.save(update_fields=["result", "next_inspection_date", "updated_at"])

        count = enqueue_expiration_warnings(days_before=30)

        self.assertEqual(count, 1)
        warning_delay.assert_called_once_with(inspection_id=self.inspection.id, days_before=30)



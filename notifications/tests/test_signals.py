import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionResultChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class NotificationSignalsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            email="client@signals.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@signals.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.station = DiagnosticStation.objects.create(name="Stacja Signals", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WS12345",
            vin="WVWZZZ1JZXW654321",
            make="Ford",
            model="Focus",
            production_year=2018,
        )

    @patch("notifications.signals.send_appointment_reminder.apply_async")
    def test_appointment_post_save_schedules_reminder_event(self, apply_async):
        Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            status=AppointmentStatusChoices.SCHEDULED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )

        apply_async.assert_called_once()
        kwargs = apply_async.call_args.kwargs["kwargs"]
        self.assertIn("appointment_id", kwargs)

    @patch("notifications.signals.send_appointment_reminder.delay")
    def test_appointment_post_save_falls_back_to_immediate_dispatch(self, delay):
        appointment = Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(hours=2),
            status=AppointmentStatusChoices.CONFIRMED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )

        delay.assert_called_once_with(appointment_id=appointment.id)

    @patch("notifications.signals.send_expiration_warning.apply_async")
    @patch("notifications.signals.send_inspection_result_notification.delay")
    def test_inspection_post_save_emits_result_and_expiration_events(self, result_delay, expiration_apply_async):
        appointment = Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            status=AppointmentStatusChoices.CONFIRMED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )

        inspection = Inspection.objects.create(
            appointment=appointment,
            result=InspectionResultChoices.FAILED,
            next_inspection_date=timezone.localdate() + datetime.timedelta(days=60),
            diagnostician=self.diagnosta,
        )

        result_delay.assert_called_once_with(inspection_id=inspection.id)
        self.assertEqual(expiration_apply_async.call_count, 2)

    @patch("notifications.signals.send_expiration_warning.apply_async")
    @patch("notifications.signals.send_inspection_result_notification.delay")
    def test_inspection_post_save_without_next_date_skips_expiration_negative(self, result_delay, expiration_apply_async):
        appointment = Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            status=AppointmentStatusChoices.CONFIRMED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )

        inspection = Inspection.objects.create(
            appointment=appointment,
            result=InspectionResultChoices.PASSED,
            diagnostician=self.diagnosta,
        )

        result_delay.assert_called_once_with(inspection_id=inspection.id)
        expiration_apply_async.assert_not_called()


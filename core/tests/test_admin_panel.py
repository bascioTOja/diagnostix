import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionResultChoices
from notifications.models import Notification, NotificationChannelChoices, NotificationStatusChoices, NotificationTypeChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class AdminPanelBL22Tests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            email="admin-bl22@panel.com",
            password="secret123",
        )
        self.diagnosta_staff = user_model.objects.create_user(
            email="diag-staff@panel.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
            is_staff=True,
        )
        self.client_staff = user_model.objects.create_user(
            email="client-staff@panel.com",
            password="secret123",
            role=RoleChoices.KLIENT,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client-bl22@panel.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )

        self.station = DiagnosticStation.objects.create(name="Stacja Admin", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WA99999",
            vin="WVWZZZ1JZXW999999",
            make="Skoda",
            model="Octavia",
            production_year=2019,
        )
        self.appointment = Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            status=AppointmentStatusChoices.SCHEDULED,
            assigned_diagnostician=self.diagnosta_staff,
            created_by=self.client_user,
        )
        self.inspection = Inspection.objects.create(
            appointment=self.appointment,
            result=InspectionResultChoices.FAILED,
            next_inspection_date=timezone.localdate() + datetime.timedelta(days=365),
            diagnostician=self.diagnosta_staff,
        )
        self.notification = Notification.objects.create(
            user=self.client_user,
            type=NotificationTypeChoices.SYSTEM,
            channel=NotificationChannelChoices.IN_APP,
            status=NotificationStatusChoices.PENDING,
            scheduled_for=timezone.now() + datetime.timedelta(hours=1),
            payload={"source": "test"},
        )

    def test_admin_can_open_registered_model_changelists(self):
        self.client.force_login(self.admin_user)

        changelist_urls = [
            reverse("diagnostix_admin:users_customuser_changelist"),
            reverse("diagnostix_admin:vehicles_vehicle_changelist"),
            reverse("diagnostix_admin:vehicles_diagnosticstation_changelist"),
            reverse("diagnostix_admin:appointments_appointment_changelist"),
            reverse("diagnostix_admin:inspections_inspection_changelist"),
            reverse("diagnostix_admin:notifications_notification_changelist"),
        ]

        for url in changelist_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_non_administrator_staff_roles_cannot_open_admin_index_negative(self):
        self.client.force_login(self.diagnosta_staff)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_client_staff_role_cannot_open_admin_index_negative(self):
        self.client.force_login(self.client_staff)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_bulk_action_deactivate_users(self):
        self.client.force_login(self.admin_user)
        target_user = get_user_model().objects.create_user(
            email="active-user@panel.com",
            password="secret123",
            role=RoleChoices.KLIENT,
            is_active=True,
        )

        response = self.client.post(
            reverse("diagnostix_admin:users_customuser_changelist"),
            {
                "action": "deactivate_selected_users",
                "_selected_action": [str(target_user.id)],
                "index": "0",
            },
            follow=True,
        )

        target_user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(target_user.is_active)

    def test_bulk_action_mark_appointments_as_confirmed(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("diagnostix_admin:appointments_appointment_changelist"),
            {
                "action": "mark_as_confirmed",
                "_selected_action": [str(self.appointment.id)],
                "index": "0",
            },
            follow=True,
        )

        self.appointment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.appointment.status, AppointmentStatusChoices.CONFIRMED)

    def test_bulk_action_mark_appointments_as_cancelled(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("diagnostix_admin:appointments_appointment_changelist"),
            {
                "action": "mark_as_cancelled",
                "_selected_action": [str(self.appointment.id)],
                "index": "0",
            },
            follow=True,
        )

        self.appointment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.appointment.status, AppointmentStatusChoices.CANCELLED)


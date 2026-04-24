from __future__ import annotations

import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import AppointmentStatusChoices
from core.tests.factories import (
    create_appointment,
    create_inspection,
    create_station,
    create_user,
    create_vehicle,
)
from inspections.models import InspectionResultChoices
from notifications.models import Notification, NotificationTypeChoices
from notifications.tasks import send_appointment_reminder, send_inspection_result_notification
from users.models import RoleChoices
from vehicles.models import VehicleTypeChoices


class CriticalE2EFlowsTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.admin = self._create_admin_user()
        self.client_user = create_user(role=RoleChoices.KLIENT)
        self.diagnosta = create_user(role=RoleChoices.DIAGNOSTA)
        self.station = create_station()

    def _create_admin_user(self):
        user_model = get_user_model()
        return user_model.objects.create_superuser(
            email="admin-flow@e2e.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
        )

    def test_client_registration_vehicle_and_appointment_flow(self):
        register_response = self.api_client.post(
            "/api/auth/register/",
            {
                "email": "flow-client@e2e.com",
                "first_name": "Flow",
                "last_name": "Client",
                "password": "secret123",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        created_client = self.client_user.__class__.objects.get(email="flow-client@e2e.com")
        self.api_client.force_authenticate(user=created_client)

        vehicle_response = self.api_client.post(
            "/api/vehicles/",
            {
                "registration_number": "WE12345",
                "vin": "WVWZZZ1JZXW123999",
                "make": "Toyota",
                "model": "Corolla",
                "production_year": 2020,
                "vehicle_type": VehicleTypeChoices.PASSENGER,
            },
            format="json",
        )
        self.assertEqual(vehicle_response.status_code, status.HTTP_201_CREATED)

        appointment_response = self.api_client.post(
            "/api/appointments/",
            {
                "vehicle": vehicle_response.data["id"],
                "station": self.station.id,
                "scheduled_at": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
                "status": AppointmentStatusChoices.SCHEDULED,
                "assigned_diagnostician": self.diagnosta.id,
            },
            format="json",
        )
        self.assertEqual(appointment_response.status_code, status.HTTP_201_CREATED)

    def test_diagnosta_schedule_and_finalize_flow(self):
        vehicle = create_vehicle(owner=self.client_user)
        appointment = create_appointment(
            vehicle=vehicle,
            client=self.client_user,
            station=self.station,
            assigned_diagnostician=self.diagnosta,
            status=AppointmentStatusChoices.CONFIRMED,
        )

        self.api_client.force_authenticate(user=self.diagnosta)
        schedule_response = self.api_client.get("/api/diagnostician/schedule/")
        self.assertEqual(schedule_response.status_code, status.HTTP_200_OK)
        self.assertEqual(schedule_response.data[0]["id"], appointment.id)

        finalize_response = self.api_client.post(
            f"/api/inspections/{appointment.id}/result/",
            {"result": InspectionResultChoices.PASSED, "notes": "OK"},
            format="json",
        )
        self.assertEqual(finalize_response.status_code, status.HTTP_201_CREATED)

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, AppointmentStatusChoices.COMPLETED)

    def test_client_history_views_flow(self):
        vehicle = create_vehicle(owner=self.client_user)
        appointment = create_appointment(
            vehicle=vehicle,
            client=self.client_user,
            station=self.station,
            assigned_diagnostician=self.diagnosta,
            status=AppointmentStatusChoices.COMPLETED,
        )
        create_inspection(
            appointment=appointment,
            diagnostician=self.diagnosta,
            result=InspectionResultChoices.PASSED,
        )

        self.api_client.force_authenticate(user=self.client_user)
        appointments_response = self.api_client.get("/api/appointments/")
        inspections_response = self.api_client.get("/api/inspections/history/")

        self.assertEqual(appointments_response.status_code, status.HTTP_200_OK)
        self.assertEqual(inspections_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(appointments_response.data), 1)
        self.assertEqual(len(inspections_response.data), 1)

    def test_administrator_can_open_management_panels(self):
        self.client.force_login(self.admin)

        changelist_urls = [
            reverse("diagnostix_admin:users_customuser_changelist"),
            reverse("diagnostix_admin:vehicles_vehicle_changelist"),
            reverse("diagnostix_admin:vehicles_diagnosticstation_changelist"),
        ]

        for url in changelist_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notifications_inspection_result_and_reminder_flow_with_deduplication(self):
        vehicle = create_vehicle(owner=self.client_user)
        completed_appointment = create_appointment(
            vehicle=vehicle,
            client=self.client_user,
            station=self.station,
            assigned_diagnostician=self.diagnosta,
            status=AppointmentStatusChoices.COMPLETED,
        )
        inspection = create_inspection(
            appointment=completed_appointment,
            diagnostician=self.diagnosta,
            result=InspectionResultChoices.PASSED,
        )

        reminder_appointment = create_appointment(
            vehicle=vehicle,
            client=self.client_user,
            station=self.station,
            assigned_diagnostician=self.diagnosta,
            status=AppointmentStatusChoices.CONFIRMED,
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
        )

        self.assertTrue(send_inspection_result_notification.run(inspection_id=inspection.id))
        self.assertTrue(send_appointment_reminder.run(appointment_id=reminder_appointment.id))

        self.assertFalse(send_inspection_result_notification.run(inspection_id=inspection.id))
        self.assertFalse(send_appointment_reminder.run(appointment_id=reminder_appointment.id))

        self.assertEqual(
            Notification.objects.filter(type=NotificationTypeChoices.INSPECTION_RESULT).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(type=NotificationTypeChoices.APPOINTMENT_REMINDER).count(),
            1,
        )





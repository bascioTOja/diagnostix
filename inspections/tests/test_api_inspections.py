import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionAuditEvent
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class InspectionsApiTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@inspapi.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client@inspapi.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@inspapi.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.other_diagnosta = user_model.objects.create_user(
            email="otherdiag@inspapi.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )

        self.station = DiagnosticStation.objects.create(name="Station Insp", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WC10000",
            vin="WVWZZZ1JZXW999999",
            make="Kia",
            model="Ceed",
            production_year=2018,
        )
        self.appointment = Appointment.objects.create(
            vehicle=self.vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            status=AppointmentStatusChoices.CONFIRMED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )

    def test_finalize_inspection_positive_with_audit(self):
        self.client_api.force_authenticate(user=self.diagnosta)

        response = self.client_api.post(
            f"/api/inspections/{self.appointment.id}/result/",
            {"result": "passed", "notes": "Wynik pozytywny"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatusChoices.COMPLETED)
        self.assertEqual(InspectionAuditEvent.objects.count(), 1)

    def test_finalize_inspection_stores_defects_and_recommendations(self):
        self.client_api.force_authenticate(user=self.diagnosta)

        response = self.client_api.post(
            f"/api/inspections/{self.appointment.id}/result/",
            {
                "result": "failed",
                "detected_defects": "Nieszczelnosc ukladu wydechowego.",
                "repair_recommendations": "Uszczelnic laczenia i wykonac ponowne badanie.",
                "next_inspection_date": (timezone.localdate() + datetime.timedelta(days=14)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inspection = Inspection.objects.get(appointment=self.appointment)
        self.assertIn("Nieszczelnosc", inspection.detected_defects)
        self.assertIn("Uszczelnic", inspection.repair_recommendations)

    def test_finalize_inspection_unassigned_diagnostician_negative(self):
        self.client_api.force_authenticate(user=self.other_diagnosta)

        response = self.client_api.post(
            f"/api/inspections/{self.appointment.id}/result/",
            {"result": "passed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_finalize_inspection_validation_rolls_back_status_negative(self):
        self.client_api.force_authenticate(user=self.diagnosta)

        response = self.client_api.post(
            f"/api/inspections/{self.appointment.id}/result/",
            {"result": "failed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatusChoices.CONFIRMED)
        self.assertEqual(InspectionAuditEvent.objects.count(), 0)

    def test_inspection_history_for_client_positive(self):
        self.client_api.force_authenticate(user=self.diagnosta)
        self.client_api.post(
            f"/api/inspections/{self.appointment.id}/result/",
            {"result": "passed"},
            format="json",
        )

        self.client_api.force_authenticate(user=self.client_user)
        response = self.client_api.get("/api/inspections/history/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_inspection_result_requires_diagnostician_role_negative(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.post(
            f"/api/inspections/{self.appointment.id}/result/",
            {"result": "passed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


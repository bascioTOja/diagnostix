import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatusChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class AppointmentsApiTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@appapi.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client@appapi.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.other_client = user_model.objects.create_user(
            email="other@appapi.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@appapi.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )

        self.station = DiagnosticStation.objects.create(name="Station App", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WB10000",
            vin="WVWZZZ1JZXW777777",
            make="Seat",
            model="Leon",
            production_year=2018,
        )
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other_client,
            registration_number="WB20000",
            vin="WVWZZZ1JZXW888888",
            make="BMW",
            model="X1",
            production_year=2019,
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

    def test_client_can_create_appointment_positive(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.post(
            "/api/appointments/",
            {
                "vehicle": self.vehicle.id,
                "station": self.station.id,
                "scheduled_at": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
                "status": AppointmentStatusChoices.SCHEDULED,
                "assigned_diagnostician": self.diagnosta.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["client"], self.client_user.id)

    def test_client_cannot_create_appointment_for_foreign_vehicle_negative(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.post(
            "/api/appointments/",
            {
                "vehicle": self.other_vehicle.id,
                "station": self.station.id,
                "scheduled_at": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
                "status": AppointmentStatusChoices.SCHEDULED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_can_cancel_own_appointment_positive(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.patch(f"/api/appointments/{self.appointment.id}/cancel/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], AppointmentStatusChoices.CANCELLED)

    def test_client_cannot_cancel_foreign_appointment_negative(self):
        self.client_api.force_authenticate(user=self.other_client)

        response = self.client_api.patch(f"/api/appointments/{self.appointment.id}/cancel/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_diagnostician_schedule_positive(self):
        self.client_api.force_authenticate(user=self.diagnosta)

        response = self.client_api.get("/api/diagnostician/schedule/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.appointment.id)

    def test_schedule_for_non_diagnostician_negative(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.get("/api/diagnostician/schedule/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


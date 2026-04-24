import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatusChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class VehiclesApiTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@vehapi.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client@vehapi.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.other_client = user_model.objects.create_user(
            email="other@vehapi.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@vehapi.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.station = DiagnosticStation.objects.create(name="Station API", slot_duration_minutes=30)

        self.client_vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WA10000",
            vin="WVWZZZ1JZXW444444",
            make="Toyota",
            model="Corolla",
            production_year=2018,
        )
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other_client,
            registration_number="WA20000",
            vin="WVWZZZ1JZXW555555",
            make="Audi",
            model="A4",
            production_year=2019,
        )

        Appointment.objects.create(
            vehicle=self.client_vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            status=AppointmentStatusChoices.CONFIRMED,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )

    def test_client_can_create_vehicle_positive(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.post(
            "/api/vehicles/",
            {
                "registration_number": "WA30000",
                "vin": "WVWZZZ1JZXW666666",
                "make": "Ford",
                "model": "Focus",
                "production_year": 2020,
                "vehicle_type": "passenger",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.client_user.id)

    def test_client_cannot_access_foreign_vehicle_negative(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.patch(
            f"/api/vehicles/{self.other_vehicle.id}/",
            {"make": "Skoda"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_list_all_vehicles_positive(self):
        self.client_api.force_authenticate(user=self.admin)

        response = self.client_api.get("/api/vehicles/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_diagnosta_sees_only_assigned_vehicle_positive(self):
        self.client_api.force_authenticate(user=self.diagnosta)

        response = self.client_api.get("/api/vehicles/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.client_vehicle.id)


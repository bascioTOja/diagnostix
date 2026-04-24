import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionResultChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class DashboardStatsApiTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@stats.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client@stats.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@stats.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )

        self.station = DiagnosticStation.objects.create(name="Stacja Stats", slot_duration_minutes=30)
        self.vehicle_passenger = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WS70001",
            vin="WVWZZZ1JZXW700001",
            make="Toyota",
            model="Yaris",
            production_year=2019,
            vehicle_type="passenger",
        )
        self.vehicle_truck = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WS70002",
            vin="WVWZZZ1JZXW700002",
            make="MAN",
            model="TGS",
            production_year=2018,
            vehicle_type="truck",
        )
        self.vehicle_motorcycle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WS70003",
            vin="WVWZZZ1JZXW700003",
            make="Honda",
            model="CB500",
            production_year=2021,
            vehicle_type="motorcycle",
        )

        self._create_inspection(
            vehicle=self.vehicle_passenger,
            scheduled_at=timezone.make_aware(datetime.datetime(2026, 4, 5, 8, 0)),
            inspection_created_at=timezone.make_aware(datetime.datetime(2026, 4, 5, 9, 0)),
            status=AppointmentStatusChoices.COMPLETED,
        )
        self._create_inspection(
            vehicle=self.vehicle_truck,
            scheduled_at=timezone.make_aware(datetime.datetime(2026, 4, 5, 10, 0)),
            inspection_created_at=timezone.make_aware(datetime.datetime(2026, 4, 5, 11, 0)),
            status=AppointmentStatusChoices.COMPLETED,
        )
        self._create_inspection(
            vehicle=self.vehicle_truck,
            scheduled_at=timezone.make_aware(datetime.datetime(2026, 4, 6, 10, 0)),
            inspection_created_at=timezone.make_aware(datetime.datetime(2026, 4, 6, 11, 0)),
            status=AppointmentStatusChoices.COMPLETED,
        )
        self._create_inspection(
            vehicle=self.vehicle_motorcycle,
            scheduled_at=timezone.make_aware(datetime.datetime(2026, 4, 7, 10, 0)),
            inspection_created_at=timezone.make_aware(datetime.datetime(2026, 4, 7, 11, 0)),
            status=AppointmentStatusChoices.CONFIRMED,
        )

    def _create_inspection(self, *, vehicle, scheduled_at, inspection_created_at, status):
        appointment = Appointment.objects.create(
            vehicle=vehicle,
            client=self.client_user,
            station=self.station,
            scheduled_at=scheduled_at,
            status=status,
            assigned_diagnostician=self.diagnosta,
            created_by=self.client_user,
        )
        inspection = Inspection.objects.create(
            appointment=appointment,
            result=InspectionResultChoices.PASSED,
            diagnostician=self.diagnosta,
        )
        Inspection.objects.filter(id=inspection.id).update(created_at=inspection_created_at, updated_at=inspection_created_at)
        appointment.refresh_from_db()
        inspection.refresh_from_db()
        return appointment, inspection

    def test_dashboard_stats_endpoint_returns_expected_aggregates_for_admin(self):
        self.client_api.force_authenticate(user=self.admin)

        response = self.client_api.get(
            "/api/dashboard/stats/",
            {"date_from": "2026-04-01", "date_to": "2026-04-30"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["metrics"]["completed_inspections_total"], 3)
        self.assertEqual(response.data["metrics"]["vehicles_total"], 3)

        self.assertEqual(
            response.data["completed_inspections_daily"],
            [
                {"date": "2026-04-05", "count": 2},
                {"date": "2026-04-06", "count": 1},
            ],
        )
        self.assertEqual(
            response.data["completed_inspections_monthly"],
            [{"month": "2026-04", "count": 3}],
        )

        self.assertEqual(response.data["top_vehicle_types"][0]["vehicle_type"], "truck")
        self.assertEqual(response.data["top_vehicle_types"][0]["inspections_count"], 2)
        self.assertEqual(response.data["top_vehicle_types"][1]["vehicle_type"], "passenger")
        self.assertEqual(response.data["top_vehicle_types"][1]["inspections_count"], 1)

    def test_dashboard_stats_endpoint_for_non_admin_returns_403_negative(self):
        self.client_api.force_authenticate(user=self.client_user)

        response = self.client_api.get("/api/dashboard/stats/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_stats_endpoint_with_invalid_date_range_returns_400_negative(self):
        self.client_api.force_authenticate(user=self.admin)

        response = self.client_api.get(
            "/api/dashboard/stats/",
            {"date_from": "2026-04-30", "date_to": "2026-04-01"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_stats_endpoint_uses_default_date_range(self):
        self.client_api.force_authenticate(user=self.admin)

        response = self.client_api.get("/api/dashboard/stats/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("date_from", response.data)
        self.assertIn("date_to", response.data)
        self.assertIn("metrics", response.data)


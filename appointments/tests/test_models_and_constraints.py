import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class AppointmentModelAndConstraintTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            email="client@app.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.other_client = user_model.objects.create_user(
            email="other@app.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@app.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.station = DiagnosticStation.objects.create(name="Stacja A", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WX11111",
            vin="WVWZZZ1JZXW111111",
            make="Toyota",
            model="Auris",
            production_year=2019,
        )
        self.scheduled_at = timezone.now() + datetime.timedelta(days=3)

    def _create_appointment(self, **kwargs):
        defaults = {
            "vehicle": self.vehicle,
            "client": self.client_user,
            "station": self.station,
            "scheduled_at": self.scheduled_at,
            "status": AppointmentStatusChoices.SCHEDULED,
            "assigned_diagnostician": self.diagnosta,
            "created_by": self.client_user,
        }
        defaults.update(kwargs)
        return Appointment.objects.create(**defaults)

    def test_create_valid_appointment(self):
        appointment = self._create_appointment()

        self.assertEqual(appointment.client_id, self.client_user.id)
        self.assertEqual(appointment.assigned_diagnostician_id, self.diagnosta.id)

    def test_client_must_be_vehicle_owner_negative(self):
        with self.assertRaises(ValidationError):
            self._create_appointment(client=self.other_client)

    def test_duplicate_vehicle_slot_active_negative(self):
        self._create_appointment()

        with self.assertRaises(ValidationError):
            self._create_appointment()

    def test_duplicate_station_slot_active_negative(self):
        self._create_appointment()
        another_vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WX22222",
            vin="WVWZZZ1JZXW222222",
            make="Ford",
            model="Focus",
            production_year=2021,
        )

        with self.assertRaises(ValidationError):
            self._create_appointment(vehicle=another_vehicle, assigned_diagnostician=None)

    def test_cancelled_allows_reuse_of_same_vehicle_slot_positive(self):
        self._create_appointment(status=AppointmentStatusChoices.CANCELLED)

        appointment = self._create_appointment(status=AppointmentStatusChoices.SCHEDULED)

        self.assertEqual(appointment.status, AppointmentStatusChoices.SCHEDULED)



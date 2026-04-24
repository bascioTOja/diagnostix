import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionResultChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class InspectionModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            email="client@insp.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@insp.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.other_diagnosta = user_model.objects.create_user(
            email="otherdiag@insp.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.station = DiagnosticStation.objects.create(name="Stacja I", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WI11111",
            vin="WVWZZZ1JZXW333333",
            make="BMW",
            model="320",
            production_year=2017,
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

    def test_valid_inspection(self):
        inspection = Inspection.objects.create(
            appointment=self.appointment,
            result=InspectionResultChoices.PASSED,
            diagnostician=self.diagnosta,
            detected_defects="Zuzyte klocki hamulcowe.",
            repair_recommendations="Wymienic klocki i sprawdzic tarcze.",
        )

        self.assertEqual(inspection.result, InspectionResultChoices.PASSED)
        self.assertIn("klocki", inspection.detected_defects)
        self.assertIn("Wymienic", inspection.repair_recommendations)

    def test_failed_requires_next_inspection_date_negative(self):
        with self.assertRaises(ValidationError):
            Inspection.objects.create(
                appointment=self.appointment,
                result=InspectionResultChoices.FAILED,
                diagnostician=self.diagnosta,
            )

    def test_passed_forbids_next_inspection_date_negative(self):
        with self.assertRaises(ValidationError):
            Inspection.objects.create(
                appointment=self.appointment,
                result=InspectionResultChoices.PASSED,
                next_inspection_date=timezone.now().date() + datetime.timedelta(days=365),
                diagnostician=self.diagnosta,
            )

    def test_diagnostician_must_match_assigned_negative(self):
        with self.assertRaises(ValidationError):
            Inspection.objects.create(
                appointment=self.appointment,
                result=InspectionResultChoices.CONDITIONAL,
                diagnostician=self.other_diagnosta,
            )


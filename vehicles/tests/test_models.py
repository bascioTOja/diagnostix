from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle, VehicleTypeChoices


class VehicleModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            email="owner@vehicle.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )

    def test_vehicle_valid_data(self):
        vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="wa1234a",
            vin="1hgcm82633a123456",
            make="Toyota",
            model="Yaris",
            production_year=2020,
            vehicle_type=VehicleTypeChoices.PASSENGER,
        )

        self.assertEqual(vehicle.registration_number, "WA1234A")
        self.assertEqual(vehicle.vin, "1HGCM82633A123456")
        self.assertTrue(vehicle.qr_code)

    def test_vehicle_qr_code_is_unique(self):
        vehicle_1 = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WA00003",
            vin="WVWZZZ1JZXW000124",
            make="Toyota",
            model="Corolla",
            production_year=2020,
        )
        vehicle_2 = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WA00004",
            vin="WVWZZZ1JZXW000125",
            make="Toyota",
            model="Corolla",
            production_year=2021,
        )

        self.assertNotEqual(vehicle_1.qr_code, vehicle_2.qr_code)

    def test_vehicle_invalid_vin_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Vehicle.objects.create(
                owner=self.client_user,
                registration_number="WA00001",
                vin="INVALIDVIN",
                make="Toyota",
                model="Yaris",
                production_year=2020,
            )

    def test_vehicle_invalid_production_year_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Vehicle.objects.create(
                owner=self.client_user,
                registration_number="WA00002",
                vin="WVWZZZ1JZXW000123",
                make="Audi",
                model="A3",
                production_year=1700,
            )


class DiagnosticStationModelTests(TestCase):
    def test_station_slot_duration_constraint_negative(self):
        with self.assertRaises(IntegrityError):
            station = DiagnosticStation(
                name="Stacja Test",
                slot_duration_minutes=1,
            )
            station.save(force_insert=True)

    def test_station_valid(self):
        station = DiagnosticStation.objects.create(name="Stacja Centrum", slot_duration_minutes=30)

        self.assertEqual(station.name, "Stacja Centrum")
        self.assertTrue(station.is_active)



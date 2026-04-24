from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from appointments.models import Appointment
from notifications.models import Notification
from vehicles.models import DiagnosticStation, Vehicle


class SeedFixtureTests(TestCase):
    def test_load_mvp_seed_fixture(self):
        call_command("loaddata", "mvp_seed", verbosity=0)

        user_model = get_user_model()
        self.assertEqual(user_model.objects.count(), 3)
        self.assertEqual(DiagnosticStation.objects.count(), 2)
        self.assertEqual(Vehicle.objects.count(), 2)
        self.assertEqual(Appointment.objects.count(), 2)
        self.assertEqual(Notification.objects.count(), 2)


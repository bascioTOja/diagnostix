import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatusChoices
from inspections.models import Inspection, InspectionAuditEvent, InspectionResultChoices
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle


class FrontendTemplatesTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            email="admin@front.com",
            password="secret123",
            role=RoleChoices.ADMINISTRATOR,
            is_staff=True,
        )
        self.client_user = user_model.objects.create_user(
            email="client@front.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.other_client = user_model.objects.create_user(
            email="other@front.com",
            password="secret123",
            role=RoleChoices.KLIENT,
        )
        self.diagnosta = user_model.objects.create_user(
            email="diag@front.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )
        self.other_diagnosta = user_model.objects.create_user(
            email="diag-other@front.com",
            password="secret123",
            role=RoleChoices.DIAGNOSTA,
        )

        self.station = DiagnosticStation.objects.create(name="Stacja Front", slot_duration_minutes=30)
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WD10000",
            vin="WVWZZZ1JZXW123456",
            make="Toyota",
            model="Corolla",
            production_year=2020,
        )
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other_client,
            registration_number="WD20000",
            vin="WVWZZZ1JZXW654321",
            make="Audi",
            model="A3",
            production_year=2019,
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

    def test_home_view_renders(self):
        response = self.client.get(reverse("web-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Diagnostix")

    def test_register_view_creates_client_user(self):
        response = self.client.post(
            reverse("web-register"),
            {
                "first_name": "Nowy",
                "last_name": "Klient",
                "email": "newclient@front.com",
                "password1": "secret123",
                "password2": "secret123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(email="newclient@front.com", role=RoleChoices.KLIENT).exists())

    def test_login_redirects_to_home_page(self):
        response = self.client.post(
            reverse("web-login"),
            {
                "email": self.client_user.email,
                "password": "secret123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("web-home"))

    def test_client_dashboard_requires_login(self):
        response = self.client.get(reverse("web-client-dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("web-login"), response["Location"])

    def test_client_dashboard_for_other_role_returns_403(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(reverse("web-client-dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_client_dashboard_contains_manage_vehicles_and_appointment_detail_link(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("web-client-vehicles"))
        self.assertContains(response, reverse("web-client-appointment-detail", kwargs={"appointment_id": self.appointment.id}))

    def test_vehicle_list_shows_only_own_vehicles(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-vehicles"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vehicle.registration_number)
        self.assertNotContains(response, self.other_vehicle.registration_number)
        self.assertContains(response, reverse("web-client-vehicle-edit", kwargs={"vehicle_id": self.vehicle.id}))
        self.assertContains(response, reverse("web-client-vehicle-delete", kwargs={"vehicle_id": self.vehicle.id}))

    def test_vehicle_detail_for_foreign_vehicle_returns_404(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-vehicle-detail", kwargs={"vehicle_id": self.other_vehicle.id}))

        self.assertEqual(response.status_code, 404)

    def test_appointment_booking_page_contains_dynamic_slot_hook(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-appointment-book"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-slot-url-template")

    def test_station_slots_endpoint_returns_json(self):
        self.client.force_login(self.client_user)

        day = (timezone.now() + datetime.timedelta(days=3)).date().isoformat()
        response = self.client.get(reverse("web-client-station-slots", kwargs={"station_id": self.station.id}), {"date": day})

        self.assertEqual(response.status_code, 200)
        self.assertIn("slots", response.json())

    def test_client_can_book_appointment_from_form(self):
        self.client.force_login(self.client_user)
        day = (timezone.now() + datetime.timedelta(days=5)).date()
        naive_dt = datetime.datetime.combine(day, datetime.time(hour=10, minute=0))
        dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())

        response = self.client.post(
            reverse("web-client-appointment-book"),
            {
                "vehicle": self.vehicle.id,
                "station": self.station.id,
                "booking_date": day.isoformat(),
                "slot_choice": timezone.localtime(dt).strftime("%Y-%m-%dT%H:%M"),
                "assigned_diagnostician": self.diagnosta.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appointment.objects.filter(client=self.client_user, scheduled_at=dt).exists())

    def test_diagnostician_schedule_access_control(self):
        self.client.force_login(self.client_user)
        response_for_client = self.client.get(reverse("web-diagnostician-schedule"))

        self.client.force_login(self.diagnosta)
        response_for_diagnostician = self.client.get(reverse("web-diagnostician-schedule"))

        self.assertEqual(response_for_client.status_code, 403)
        self.assertEqual(response_for_diagnostician.status_code, 200)

    def test_diagnostician_can_submit_inspection_result_and_create_audit(self):
        self.client.force_login(self.diagnosta)

        response = self.client.post(
            reverse("web-diagnostician-appointment-result", kwargs={"appointment_id": self.appointment.id}),
            {
                "result": "passed",
                "notes": "OK",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatusChoices.COMPLETED)
        self.assertEqual(InspectionAuditEvent.objects.filter(appointment=self.appointment).count(), 1)

    def test_diagnostician_inspection_form_shows_polish_result_options(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(
            reverse("web-diagnostician-appointment-result", kwargs={"appointment_id": self.appointment.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pozytywny")
        self.assertContains(response, "Negatywny")
        self.assertContains(response, "Warunkowy")

    def test_diagnostician_inspection_form_contains_defects_and_recommendations_fields(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(
            reverse("web-diagnostician-appointment-result", kwargs={"appointment_id": self.appointment.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wykryte usterki")
        self.assertContains(response, "Zalecenia naprawy")

    def test_diagnostician_inspection_form_shows_field_error_for_positive_result_with_date(self):
        self.client.force_login(self.diagnosta)

        response = self.client.post(
            reverse("web-diagnostician-appointment-result", kwargs={"appointment_id": self.appointment.id}),
            {
                "result": "passed",
                "notes": "OK",
                "next_inspection_date": (timezone.localdate() + datetime.timedelta(days=365)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Dla wyniku pozytywnego data kolejnego badania nie jest wymagana.", status_code=400)
        self.assertNotContains(response, "ErrorDetail(", status_code=400)

    def test_diagnostician_inspection_form_contains_next_inspection_toggle_hooks(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(
            reverse("web-diagnostician-appointment-result", kwargs={"appointment_id": self.appointment.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-field-name="next_inspection_date"')
        self.assertContains(response, "resultSelect.value === 'passed'")

    def test_admin_dashboard_access_control(self):
        self.client.force_login(self.client_user)
        response_for_client = self.client.get(reverse("web-admin-dashboard"))

        self.client.force_login(self.admin)
        response_for_admin = self.client.get(reverse("web-admin-dashboard"))

        self.assertEqual(response_for_client.status_code, 403)
        self.assertEqual(response_for_admin.status_code, 200)
        self.assertContains(response_for_admin, "Wykonane badania")
        self.assertContains(response_for_admin, "Trend dzienny wykonanych badań")

    def test_admin_user_list_access_control(self):
        self.client.force_login(self.client_user)
        response_for_client = self.client.get(reverse("web-admin-users"))

        self.client.force_login(self.admin)
        response_for_admin = self.client.get(reverse("web-admin-users"))

        self.assertEqual(response_for_client.status_code, 403)
        self.assertEqual(response_for_admin.status_code, 200)
        self.assertContains(response_for_admin, self.client_user.email)

    def test_admin_can_edit_user_and_change_role(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("web-admin-user-edit", kwargs={"user_id": self.client_user.id}),
            {
                "first_name": "Nowe",
                "last_name": "Nazwisko",
                "email": "client-updated@front.com",
                "role": RoleChoices.DIAGNOSTA,
                "is_active": "on",
            },
        )

        self.client_user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client_user.first_name, "Nowe")
        self.assertEqual(self.client_user.email, "client-updated@front.com")
        self.assertEqual(self.client_user.role, RoleChoices.DIAGNOSTA)

    def test_admin_vehicle_list_access_control(self):
        self.client.force_login(self.client_user)
        response_for_client = self.client.get(reverse("web-admin-vehicles"))

        self.client.force_login(self.admin)
        response_for_admin = self.client.get(reverse("web-admin-vehicles"))

        self.assertEqual(response_for_client.status_code, 403)
        self.assertEqual(response_for_admin.status_code, 200)
        self.assertContains(response_for_admin, self.vehicle.registration_number)

    def test_admin_can_delete_vehicle_from_admin_list(self):
        vehicle_to_delete = Vehicle.objects.create(
            owner=self.client_user,
            registration_number="WD40000",
            vin="WVWZZZ1JZXW333444",
            make="Ford",
            model="Focus",
            production_year=2018,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("web-admin-vehicle-delete", kwargs={"vehicle_id": vehicle_to_delete.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Vehicle.objects.filter(id=vehicle_to_delete.id).exists())

    def test_admin_cannot_delete_vehicle_linked_to_appointment_negative(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("web-admin-vehicle-delete", kwargs={"vehicle_id": self.vehicle.id}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Vehicle.objects.filter(id=self.vehicle.id).exists())
        self.assertContains(response, "Nie można usunąć pojazdu")

    def test_client_appointments_contains_cancel_modal_hook(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-appointments"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-confirm")

    def test_client_can_open_own_appointment_details(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-appointment-detail", kwargs={"appointment_id": self.appointment.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.appointment.vehicle.registration_number)
        self.assertContains(response, self.appointment.station.name)

    def test_client_appointment_details_for_foreign_appointment_return_404(self):
        foreign_appointment = Appointment.objects.create(
            vehicle=self.other_vehicle,
            client=self.other_client,
            station=self.station,
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            status=AppointmentStatusChoices.SCHEDULED,
            created_by=self.other_client,
        )
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-appointment-detail", kwargs={"appointment_id": foreign_appointment.id}))

        self.assertEqual(response.status_code, 404)

    def test_vehicle_details_contains_validity_information(self):
        Inspection.objects.create(
            appointment=self.appointment,
            result=InspectionResultChoices.FAILED,
            notes="Braki",
            next_inspection_date=timezone.localdate() - datetime.timedelta(days=2),
            diagnostician=self.diagnosta,
        )
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-vehicle-detail", kwargs={"vehicle_id": self.vehicle.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ważność badania")
        self.assertContains(response, "Badanie nieważne")

    def test_vehicle_create_supports_motorcycle_type(self):
        self.client.force_login(self.client_user)

        response = self.client.post(
            reverse("web-client-vehicle-add"),
            {
                "registration_number": "WD30000",
                "vin": "WVWZZZ1JZXW112233",
                "make": "Yamaha",
                "model": "MT-07",
                "production_year": 2022,
                "vehicle_type": "motorcycle",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vehicle.objects.filter(owner=self.client_user, vehicle_type="motorcycle").exists())

    def test_client_vehicle_details_contains_qr_code_and_qr_link(self):
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("web-client-vehicle-detail", kwargs={"vehicle_id": self.vehicle.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kod QR pojazdu")
        self.assertContains(
            response,
            reverse("web-diagnostician-vehicle-by-qr", kwargs={"qr_code": self.vehicle.qr_code}),
        )

    def test_diagnostician_can_open_vehicle_card_by_qr(self):
        self.client.force_login(self.diagnosta)

        response = self.client.get(
            reverse("web-diagnostician-vehicle-by-qr", kwargs={"qr_code": self.vehicle.qr_code}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Karta pojazdu")
        self.assertContains(response, self.vehicle.registration_number)

    def test_non_assigned_diagnostician_gets_404_for_vehicle_qr_negative(self):
        self.client.force_login(self.other_diagnosta)

        response = self.client.get(
            reverse("web-diagnostician-vehicle-by-qr", kwargs={"qr_code": self.vehicle.qr_code})
        )

        self.assertEqual(response.status_code, 404)


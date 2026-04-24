from __future__ import annotations

import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from rest_framework.exceptions import APIException

from analytics.services import build_dashboard_stats, default_date_range
from appointments.models import ACTIVE_APPOINTMENT_STATUSES, Appointment
from appointments.selectors import diagnostician_schedule
from appointments.services import cancel_appointment_for_user, create_appointment_for_client
from core.common.mixins import RoleRequiredMixin
from core.web.forms import (
    AdminUserEditForm,
    AppointmentBookingForm,
    InspectionResultForm,
    LoginForm,
    ProfileForm,
    RegisterForm,
    VehicleForm,
)
from inspections.models import Inspection, InspectionAuditEvent
from inspections.services import finalize_inspection
from users.models import RoleChoices
from vehicles.models import DiagnosticStation, Vehicle

User = get_user_model()


def _raise_for_api_exception(exc: APIException):
    if exc.status_code == 404:
        raise Http404(str(exc.detail))
    if exc.status_code == 403:
        raise PermissionError(str(exc.detail))
    raise ValueError(exc.detail)


def _extract_error_text(detail) -> str:
    if isinstance(detail, list):
        if not detail:
            return "Wystapil blad walidacji."
        return _extract_error_text(detail[0])
    if isinstance(detail, dict):
        if not detail:
            return "Wystapil blad walidacji."
        return _extract_error_text(next(iter(detail.values())))
    return str(detail)


def _add_api_validation_errors_to_form(form, detail):
    if not isinstance(detail, dict):
        form.add_error(None, _extract_error_text(detail))
        return

    for field_name, field_detail in detail.items():
        target_field = field_name if field_name in form.fields else None
        form.add_error(target_field, _extract_error_text(field_detail))


def _vehicle_validity_context(inspections):
    latest_inspection = inspections.first()
    validity_label = "Brak danych o badaniu"
    validity_badge = "secondary"
    validity_date = None

    if latest_inspection and latest_inspection.next_inspection_date:
        validity_date = latest_inspection.next_inspection_date
        if latest_inspection.next_inspection_date >= timezone.localdate():
            validity_label = "Badanie ważne"
            validity_badge = "success"
        else:
            validity_label = "Badanie nieważne"
            validity_badge = "danger"
    elif latest_inspection:
        validity_label = "Brak daty kolejnego badania"
        validity_badge = "warning"

    return {
        "validity_label": validity_label,
        "validity_badge": validity_badge,
        "validity_date": validity_date,
    }


def _diagnostician_vehicle_or_404(*, diagnostician, vehicle_id: int):
    has_assignment = Appointment.objects.filter(vehicle_id=vehicle_id, assigned_diagnostician=diagnostician).exists()
    if not has_assignment:
        raise Http404("Zasob nie istnieje.")
    return get_object_or_404(Vehicle, pk=vehicle_id)


class HomeView(View):
    def get(self, request):
        return render(request, "web/home.html")


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("web-profile")
        return render(request, "web/auth/register.html", {"form": RegisterForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("web-profile")

        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Konto zostalo utworzone.")
            return redirect("web-client-dashboard")
        return render(request, "web/auth/register.html", {"form": form}, status=400)


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("web-home")
        return render(request, "web/auth/login.html", {"form": LoginForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("web-home")

        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            messages.success(request, "Zalogowano.")
            return redirect("web-home")
        return render(request, "web/auth/login.html", {"form": form}, status=400)


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        messages.info(request, "Wylogowano.")
        return redirect("web-home")


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, "web/auth/profile.html", {"form": form})

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil zaktualizowany.")
            return redirect("web-profile")
        return render(request, "web/auth/profile.html", {"form": form}, status=400)


class ClientDashboardView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request):
        vehicles_count = Vehicle.objects.filter(owner=request.user).count()
        appointments_count = Appointment.objects.filter(client=request.user).count()
        upcoming_appointments = (
            Appointment.objects.filter(client=request.user)
            .select_related("vehicle", "station")
            .order_by("scheduled_at")[:5]
        )
        return render(
            request,
            "web/client/dashboard.html",
            {
                "vehicles_count": vehicles_count,
                "appointments_count": appointments_count,
                "upcoming_appointments": upcoming_appointments,
            },
        )


class ClientVehicleListView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user).order_by("registration_number")
        return render(request, "web/client/vehicle_list.html", {"vehicles": vehicles})


class ClientVehicleCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request):
        return render(request, "web/client/vehicle_form.html", {"form": VehicleForm(), "title": "Dodaj pojazd"})

    def post(self, request):
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.owner = request.user
            vehicle.save()
            messages.success(request, "Pojazd dodany.")
            return redirect("web-client-vehicles")
        return render(request, "web/client/vehicle_form.html", {"form": form, "title": "Dodaj pojazd"}, status=400)


class ClientVehicleUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get_object(self, request, vehicle_id: int):
        return get_object_or_404(Vehicle, pk=vehicle_id, owner=request.user)

    def get(self, request, vehicle_id: int):
        vehicle = self.get_object(request, vehicle_id)
        form = VehicleForm(instance=vehicle)
        return render(request, "web/client/vehicle_form.html", {"form": form, "title": "Edytuj pojazd"})

    def post(self, request, vehicle_id: int):
        vehicle = self.get_object(request, vehicle_id)
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Pojazd zaktualizowany.")
            return redirect("web-client-vehicle-detail", vehicle_id=vehicle.id)
        return render(request, "web/client/vehicle_form.html", {"form": form, "title": "Edytuj pojazd"}, status=400)


class ClientVehicleDeleteView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def post(self, request, vehicle_id: int):
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id, owner=request.user)
        vehicle.delete()
        messages.success(request, "Pojazd usuniety.")
        return redirect("web-client-vehicles")


class ClientVehicleDetailView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request, vehicle_id: int):
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id, owner=request.user)
        inspections = (
            Inspection.objects.filter(appointment__vehicle=vehicle, appointment__client=request.user)
            .select_related("diagnostician")
            .order_by("-created_at")
        )
        validity_context = _vehicle_validity_context(inspections)
        qr_access_path = request.build_absolute_uri(
            reverse("web-diagnostician-vehicle-by-qr", kwargs={"qr_code": vehicle.qr_code})
        )

        return render(
            request,
            "web/client/vehicle_detail.html",
            {
                "vehicle": vehicle,
                "inspections": inspections,
                "qr_access_path": qr_access_path,
                **validity_context,
            },
        )


class ClientAppointmentsView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request):
        appointments = Appointment.objects.filter(client=request.user).select_related("vehicle", "station", "assigned_diagnostician").order_by("-scheduled_at")
        return render(request, "web/client/appointment_list.html", {"appointments": appointments})


class ClientAppointmentDetailView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request, appointment_id: int):
        appointment = get_object_or_404(
            Appointment.objects.select_related("vehicle", "station", "assigned_diagnostician", "inspection"),
            pk=appointment_id,
            client=request.user,
        )
        return render(request, "web/client/appointment_detail.html", {"appointment": appointment})


class ClientAppointmentCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request):
        return render(request, "web/client/appointment_form.html", {"form": AppointmentBookingForm(user=request.user)})

    def post(self, request):
        form = AppointmentBookingForm(request.POST, user=request.user)
        if form.is_valid():
            payload = dict(form.cleaned_data)
            payload.pop("booking_date", None)
            payload.pop("slot_choice", None)
            try:
                create_appointment_for_client(request.user, payload)
            except APIException as exc:
                try:
                    _raise_for_api_exception(exc)
                except Http404 as not_found:
                    raise not_found
                except PermissionError as denied:
                    return render(request, "403.html", status=403)
                except ValueError as detail:
                    form.add_error(None, str(detail))
            else:
                messages.success(request, "Wizyta zostala zarezerwowana.")
                return redirect("web-client-appointments")
        return render(request, "web/client/appointment_form.html", {"form": form}, status=400)


class ClientAppointmentCancelView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def post(self, request, appointment_id: int):
        try:
            cancel_appointment_for_user(request.user, appointment_id)
            messages.success(request, "Wizyta anulowana.")
        except APIException as exc:
            try:
                _raise_for_api_exception(exc)
            except Http404 as not_found:
                raise not_found
            except PermissionError:
                return render(request, "403.html", status=403)
            except ValueError as detail:
                messages.error(request, str(detail))
        return redirect("web-client-appointments")


class StationSlotsAPIView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.KLIENT,)

    def get(self, request, station_id: int):
        day = request.GET.get("date")
        if not day:
            return JsonResponse({"slots": []})

        station = get_object_or_404(DiagnosticStation, pk=station_id, is_active=True)
        selected_day = datetime.datetime.strptime(day, "%Y-%m-%d").date()

        start = datetime.datetime.combine(selected_day, datetime.time(hour=8, minute=0))
        end = datetime.datetime.combine(selected_day, datetime.time(hour=17, minute=0))
        start = timezone.make_aware(start, timezone.get_current_timezone())
        end = timezone.make_aware(end, timezone.get_current_timezone())

        booked = set(
            Appointment.objects.filter(
                station=station,
                scheduled_at__gte=start,
                scheduled_at__lt=end,
                status__in=ACTIVE_APPOINTMENT_STATUSES,
            ).values_list("scheduled_at", flat=True)
        )

        slots = []
        current = start
        while current < end:
            if current not in booked and current > timezone.now():
                slots.append(
                    {
                        "value": timezone.localtime(current).strftime("%Y-%m-%dT%H:%M"),
                        "label": timezone.localtime(current).strftime("%H:%M"),
                    }
                )
            current += datetime.timedelta(minutes=station.slot_duration_minutes)

        return JsonResponse({"slots": slots})


class DiagnosticianScheduleView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.DIAGNOSTA,)

    def get(self, request):
        try:
            appointments = diagnostician_schedule(request.user)
        except APIException:
            return render(request, "403.html", status=403)
        return render(request, "web/diagnostician/schedule.html", {"appointments": appointments})


class DiagnosticianAppointmentDetailView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.DIAGNOSTA,)

    def get(self, request, appointment_id: int):
        appointment = get_object_or_404(
            Appointment.objects.select_related("vehicle", "station", "client", "inspection"),
            pk=appointment_id,
            assigned_diagnostician=request.user,
        )
        vehicle_qr_path = reverse("web-diagnostician-vehicle-by-qr", kwargs={"qr_code": appointment.vehicle.qr_code})
        return render(
            request,
            "web/diagnostician/appointment_detail.html",
            {
                "appointment": appointment,
                "vehicle_qr_path": vehicle_qr_path,
            },
        )


class DiagnosticianVehicleByQRView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ("diagnosta",)

    def get(self, request, qr_code: str):
        vehicle = get_object_or_404(Vehicle, qr_code=qr_code)
        _diagnostician_vehicle_or_404(diagnostician=request.user, vehicle_id=vehicle.id)
        return redirect("web-diagnostician-vehicle-detail", vehicle_id=vehicle.id)


class DiagnosticianVehicleDetailView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ("diagnosta",)

    def get(self, request, vehicle_id: int):
        vehicle = _diagnostician_vehicle_or_404(diagnostician=request.user, vehicle_id=vehicle_id)
        inspections = Inspection.objects.filter(appointment__vehicle=vehicle).select_related("diagnostician").order_by("-created_at")
        validity_context = _vehicle_validity_context(inspections)
        return render(
            request,
            "web/diagnostician/vehicle_detail.html",
            {
                "vehicle": vehicle,
                "inspections": inspections,
                **validity_context,
            },
        )


class DiagnosticianInspectionResultView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.DIAGNOSTA,)

    def get(self, request, appointment_id: int):
        appointment = get_object_or_404(Appointment, pk=appointment_id, assigned_diagnostician=request.user)
        form = InspectionResultForm()
        return render(request, "web/diagnostician/inspection_form.html", {"form": form, "appointment": appointment})

    def post(self, request, appointment_id: int):
        appointment = get_object_or_404(Appointment, pk=appointment_id, assigned_diagnostician=request.user)
        form = InspectionResultForm(request.POST)
        if form.is_valid():
            try:
                finalize_inspection(
                    appointment_id=appointment.id,
                    diagnostician=request.user,
                    payload=form.cleaned_data,
                )
            except APIException as exc:
                try:
                    _raise_for_api_exception(exc)
                except Http404 as not_found:
                    raise not_found
                except PermissionError:
                    return render(request, "403.html", status=403)
                except ValueError as detail:
                    normalized_detail = detail.args[0] if detail.args else str(detail)
                    _add_api_validation_errors_to_form(form, normalized_detail)
            else:
                messages.success(request, "Wynik badania zapisany.")
                return redirect("web-diagnostician-appointment-detail", appointment_id=appointment.id)
        return render(
            request,
            "web/diagnostician/inspection_form.html",
            {"form": form, "appointment": appointment},
            status=400,
        )


class AdminDashboardView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.ADMINISTRATOR,)

    def get(self, request):
        default_date_from, default_date_to = default_date_range()
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        try:
            parsed_date_from = datetime.date.fromisoformat(date_from) if date_from else default_date_from
            parsed_date_to = datetime.date.fromisoformat(date_to) if date_to else default_date_to
            stats = build_dashboard_stats(date_from=parsed_date_from, date_to=parsed_date_to)
        except ValueError:
            messages.error(request, "Nieprawidlowy zakres dat dla statystyk.")
            stats = build_dashboard_stats(date_from=default_date_from, date_to=default_date_to)

        users = list(
            User.objects.order_by("email").values("id", "email", "first_name", "last_name", "role")[:10]
        )
        stations = DiagnosticStation.objects.order_by("name")[:10]
        audit_events = InspectionAuditEvent.objects.select_related("actor", "appointment").order_by("-created_at")[:10]
        return render(
            request,
            "web/admin/dashboard.html",
            {
                "users": users,
                "stations": stations,
                "audit_events": audit_events,
                "stats": stats,
            },
        )


class AdminVehicleListView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.ADMINISTRATOR,)

    def get(self, request):
        vehicles = Vehicle.objects.select_related("owner").order_by("registration_number", "id")
        return render(request, "web/admin/vehicle_list.html", {"vehicles": vehicles})


class AdminVehicleDeleteView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.ADMINISTRATOR,)

    def post(self, request, vehicle_id: int):
        vehicle = get_object_or_404(Vehicle.objects.select_related("owner"), pk=vehicle_id)
        vehicle_label = vehicle.registration_number
        try:
            vehicle.delete()
            messages.success(request, f"Pojazd {vehicle_label} został usunięty.")
        except ProtectedError:
            messages.error(
                request,
                "Nie można usunąć pojazdu, ponieważ jest powiązany z wizytami lub badaniami.",
            )
        return redirect("web-admin-vehicles")


class AdminUserListView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.ADMINISTRATOR,)

    def get(self, request):
        users = User.objects.order_by("email")
        return render(request, "web/admin/user_list.html", {"users": users})


class AdminUserUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = (RoleChoices.ADMINISTRATOR,)

    def get_object(self, user_id: int):
        return get_object_or_404(User, pk=user_id)

    def get(self, request, user_id: int):
        user_obj = self.get_object(user_id)
        form = AdminUserEditForm(instance=user_obj)
        return render(
            request,
            "web/admin/user_form.html",
            {
                "form": form,
                "user_obj": user_obj,
            },
        )

    def post(self, request, user_id: int):
        user_obj = self.get_object(user_id)
        form = AdminUserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Dane użytkownika zostały zaktualizowane.")
            return redirect("web-admin-users")
        return render(
            request,
            "web/admin/user_form.html",
            {
                "form": form,
                "user_obj": user_obj,
            },
            status=400,
        )



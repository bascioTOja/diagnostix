from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone

from appointments.models import Appointment
from inspections.models import InspectionResultChoices
from users.models import RoleChoices
from vehicles.models import Vehicle

User = get_user_model()


class BootstrapFormMixin:
    fields: dict[str, forms.Field]

    def _apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget
            css_class = "form-control"
            if isinstance(widget, forms.Select):
                css_class = "form-select"
            elif isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"

            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()


class RegisterForm(BootstrapFormMixin, forms.ModelForm):
    password1 = forms.CharField(label="Haslo", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Powtorz haslo", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Imie",
            "last_name": "Nazwisko",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self._apply_bootstrap_classes()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Hasla musza byc identyczne.")
        return cleaned

    def save(self, commit=True):
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            password=self.cleaned_data["password1"],
            role=RoleChoices.KLIENT,
        )
        return user


class LoginForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Haslo", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Niepoprawny email lub haslo.")
            cleaned["user"] = user
        return cleaned


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Imie",
            "last_name": "Nazwisko",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class AdminUserEditForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "role", "is_active")
        labels = {
            "first_name": "Imię",
            "last_name": "Nazwisko",
            "email": "E-mail",
            "role": "Rola",
            "is_active": "Konto aktywne",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class VehicleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = (
            "registration_number",
            "vin",
            "make",
            "model",
            "production_year",
            "vehicle_type",
        )
        labels = {
            "registration_number": "Numer rejestracyjny",
            "vin": "VIN",
            "make": "Marka",
            "model": "Model",
            "production_year": "Rok produkcji",
            "vehicle_type": "Typ pojazdu",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class AppointmentBookingForm(BootstrapFormMixin, forms.ModelForm):
    booking_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Dzień wizyty",
    )
    slot_choice = forms.CharField(required=False, label="Dostępny termin")

    class Meta:
        model = Appointment
        fields = (
            "vehicle",
            "station",
            "scheduled_at",
            "assigned_diagnostician",
        )
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].queryset = Vehicle.objects.filter(owner=self.user)
        self.fields["vehicle"].label_from_instance = (
            lambda vehicle: f"{vehicle.registration_number} - {vehicle.make} {vehicle.model} ({vehicle.production_year})"
        )
        self.fields["assigned_diagnostician"].queryset = User.objects.filter(role=RoleChoices.DIAGNOSTA)
        self.fields["scheduled_at"].required = False
        self.fields["scheduled_at"].widget = forms.HiddenInput()
        self._apply_bootstrap_classes()

    def clean(self):
        cleaned = super().clean()
        slot_choice = cleaned.get("slot_choice")

        if not slot_choice:
            raise forms.ValidationError("Wybierz dostępny termin wizyty.")

        parsed = forms.DateTimeField(input_formats=["%Y-%m-%dT%H:%M"]).clean(slot_choice)
        cleaned["scheduled_at"] = parsed

        if timezone.is_naive(cleaned["scheduled_at"]):
            cleaned["scheduled_at"] = timezone.make_aware(cleaned["scheduled_at"], timezone.get_current_timezone())

        return cleaned


class InspectionResultForm(BootstrapFormMixin, forms.Form):
    result = forms.ChoiceField(choices=InspectionResultChoices, label="Wynik")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Uwagi")
    detected_defects = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Wykryte usterki",
    )
    repair_recommendations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Zalecenia naprawy",
    )
    next_inspection_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Data kolejnego badania",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


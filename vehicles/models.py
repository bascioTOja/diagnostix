from __future__ import annotations

import datetime
import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.common.models import TimeStampedModel

VIN_REGEX = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
MIN_PRODUCTION_YEAR = 1886
MAX_PRODUCTION_YEAR = datetime.date.today().year + 1


class VehicleTypeChoices(models.TextChoices):
    PASSENGER = "passenger", "Osobowy"
    TRUCK = "truck", "Ciezarowy"
    MOTORCYCLE = "motorcycle", "Motocykl"


class Vehicle(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    registration_number = models.CharField(max_length=16, unique=True)
    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=64)
    model = models.CharField(max_length=64)
    production_year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_PRODUCTION_YEAR),
            MaxValueValidator(MAX_PRODUCTION_YEAR),
        ]
    )
    vehicle_type = models.CharField(
        max_length=16,
        choices=VehicleTypeChoices,
        default=VehicleTypeChoices.PASSENGER,
    )
    qr_code = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "registration_number"], name="vehicle_owner_reg_idx"),
        ]

    def clean(self):
        super().clean()
        self.registration_number = self.registration_number.upper().strip()
        self.vin = self.vin.upper().strip()
        if self.qr_code:
            self.qr_code = str(self.qr_code).strip()
        if not VIN_REGEX.fullmatch(self.vin):
            raise ValidationError({"vin": "VIN musi miec 17 znakow i nie moze zawierac I, O, Q."})

    def _generate_qr_code(self):
        if self.qr_code:
            return

        while True:
            candidate = uuid.uuid4().hex
            conflict_qs = self.__class__.objects.filter(qr_code=candidate)
            if self.pk:
                conflict_qs = conflict_qs.exclude(pk=self.pk)
            if not conflict_qs.exists():
                self.qr_code = candidate
                return

    def save(self, *args, **kwargs):
        self._generate_qr_code()
        self.full_clean()
        return super().save(*args, **kwargs)


class DiagnosticStation(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    slot_duration_minutes = models.PositiveSmallIntegerField(default=30)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "name"], name="station_active_name_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(slot_duration_minutes__gte=5),
                name="station_slot_duration_gte_5",
            )
        ]

    def __str__(self) -> str:
        return self.name


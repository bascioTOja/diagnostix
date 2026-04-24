from django.contrib import admin

from core.admin_site import diagnostix_admin_site
from vehicles.models import DiagnosticStation, Vehicle


@admin.register(Vehicle, site=diagnostix_admin_site)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "registration_number", "vin", "owner", "make", "model", "production_year", "vehicle_type")
    list_filter = ("vehicle_type", "production_year", "created_at")
    search_fields = ("registration_number", "vin", "make", "model", "owner__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DiagnosticStation, site=diagnostix_admin_site)
class DiagnosticStationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "slot_duration_minutes")
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


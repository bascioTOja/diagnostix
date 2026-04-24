from django.contrib import admin

from appointments.models import Appointment, AppointmentStatusChoices
from core.admin_site import diagnostix_admin_site


@admin.register(Appointment, site=diagnostix_admin_site)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "scheduled_at",
        "status",
        "client",
        "vehicle",
        "station",
        "assigned_diagnostician",
    )
    list_filter = ("status", "scheduled_at", "station")
    search_fields = ("client__email", "vehicle__registration_number", "vehicle__vin", "station__name")
    readonly_fields = ("created_at", "updated_at")
    actions = ("mark_as_confirmed", "mark_as_cancelled")

    @admin.action(description="Oznacz wybrane wizyty jako confirmed")
    def mark_as_confirmed(self, request, queryset):
        queryset.filter(status=AppointmentStatusChoices.SCHEDULED).update(status=AppointmentStatusChoices.CONFIRMED)

    @admin.action(description="Oznacz wybrane wizyty jako cancelled")
    def mark_as_cancelled(self, request, queryset):
        queryset.exclude(status=AppointmentStatusChoices.COMPLETED).update(status=AppointmentStatusChoices.CANCELLED)


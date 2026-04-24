from django.contrib import admin

from core.admin_site import diagnostix_admin_site
from inspections.models import Inspection


@admin.register(Inspection, site=diagnostix_admin_site)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "result", "diagnostician", "next_inspection_date")
    list_filter = ("result", "next_inspection_date", "created_at")
    search_fields = ("appointment__client__email", "appointment__vehicle__registration_number", "diagnostician__email")
    readonly_fields = ("created_at", "updated_at")


from django.contrib import admin

from core.admin_site import diagnostix_admin_site
from notifications.models import Notification


@admin.register(Notification, site=diagnostix_admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "channel", "status", "scheduled_for", "sent_at")
    list_filter = ("type", "channel", "status", "scheduled_for")
    search_fields = ("user__email", "dedupe_key")
    readonly_fields = ("created_at", "updated_at")


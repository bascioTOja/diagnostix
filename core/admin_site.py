from django.contrib.admin import AdminSite

from users.models import RoleChoices


class DiagnostixAdminSite(AdminSite):
    site_header = "Diagnostix - panel administracyjny"
    site_title = "Diagnostix Admin"
    index_title = "Zarzadzanie"

    def has_permission(self, request):
        user = request.user
        return bool(
            user.is_active
            and user.is_authenticated
            and user.is_staff
            and getattr(user, "role", None) == RoleChoices.ADMINISTRATOR
        )


diagnostix_admin_site = DiagnostixAdminSite(name="diagnostix_admin")


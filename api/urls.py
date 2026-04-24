from django.urls import include, path

from users.api.views import ProfileAPIView

urlpatterns = [
    path("auth/", include("users.api.urls")),
    path("profile/", ProfileAPIView.as_view(), name="api-profile"),
    path("", include("analytics.api.urls")),
    path("", include("vehicles.api.urls")),
    path("", include("appointments.api.urls")),
    path("", include("inspections.api.urls")),
]


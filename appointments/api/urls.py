from django.urls import path

from appointments.api.views import (
    AppointmentCancelAPIView,
    AppointmentListCreateAPIView,
    DiagnosticianScheduleAPIView,
)

urlpatterns = [
    path("appointments/", AppointmentListCreateAPIView.as_view(), name="api-appointments"),
    path("appointments/<int:pk>/cancel/", AppointmentCancelAPIView.as_view(), name="api-appointments-cancel"),
    path("diagnostician/schedule/", DiagnosticianScheduleAPIView.as_view(), name="api-diagnostician-schedule"),
]


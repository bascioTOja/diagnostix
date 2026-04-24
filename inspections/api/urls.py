from django.urls import path

from inspections.api.views import InspectionHistoryAPIView, InspectionResultCreateAPIView

urlpatterns = [
    path("inspections/history/", InspectionHistoryAPIView.as_view(), name="api-inspections-history"),
    path("inspections/<int:appointment_id>/result/", InspectionResultCreateAPIView.as_view(), name="api-inspections-result"),
]


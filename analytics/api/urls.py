from django.urls import path

from analytics.api.views import DashboardStatsAPIView

urlpatterns = [
    path("dashboard/stats/", DashboardStatsAPIView.as_view(), name="api-dashboard-stats"),
]


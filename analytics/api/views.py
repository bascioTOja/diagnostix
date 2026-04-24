from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.api.serializers import DashboardStatsQuerySerializer, DashboardStatsSerializer
from analytics.services import build_dashboard_stats, default_date_range
from core.common.permissions import IsAdministrator


class DashboardStatsAPIView(APIView):
    permission_classes = (IsAuthenticated, IsAdministrator)

    def get(self, request):
        query_serializer = DashboardStatsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        default_from, default_to = default_date_range()
        date_from = query_serializer.validated_data.get("date_from", default_from)
        date_to = query_serializer.validated_data.get("date_to", default_to)

        payload = build_dashboard_stats(date_from=date_from, date_to=date_to)
        response_serializer = DashboardStatsSerializer(payload)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.common.permissions import IsDiagnosta
from inspections.api.serializers import FinalizeInspectionSerializer, InspectionSerializer
from inspections.selectors import inspection_history_for_user
from inspections.services import finalize_inspection


class InspectionHistoryAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = inspection_history_for_user(request.user)
        serializer = InspectionSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InspectionResultCreateAPIView(APIView):
    permission_classes = (IsAuthenticated, IsDiagnosta)

    def post(self, request, appointment_id: int):
        serializer = FinalizeInspectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inspection = finalize_inspection(
            appointment_id=appointment_id,
            diagnostician=request.user,
            payload=serializer.validated_data,
        )
        return Response(InspectionSerializer(inspection).data, status=status.HTTP_201_CREATED)


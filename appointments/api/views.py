from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.api.serializers import AppointmentCancelSerializer, AppointmentSerializer
from appointments.selectors import appointments_for_user, diagnostician_schedule
from appointments.services import cancel_appointment_for_user, create_appointment_for_client


class AppointmentListCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = appointments_for_user(request.user)
        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = create_appointment_for_client(request.user, serializer.validated_data)
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


class AppointmentCancelAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, pk: int):
        appointment = cancel_appointment_for_user(request.user, appointment_id=pk)
        serializer = AppointmentCancelSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DiagnosticianScheduleAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = diagnostician_schedule(request.user)
        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


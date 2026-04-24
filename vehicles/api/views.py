from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from vehicles.api.serializers import VehicleSerializer
from vehicles.selectors import get_vehicle_for_user_or_404, vehicles_for_user
from vehicles.services import create_vehicle_for_user, delete_vehicle_for_user, update_vehicle_for_user


class VehicleViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        queryset = vehicles_for_user(request.user)
        serializer = VehicleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = VehicleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = create_vehicle_for_user(request.user, serializer.validated_data)
        return Response(VehicleSerializer(vehicle).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        vehicle = get_vehicle_for_user_or_404(request.user, int(pk))
        serializer = VehicleSerializer(instance=vehicle, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        vehicle = update_vehicle_for_user(request.user, vehicle, serializer.validated_data)
        return Response(VehicleSerializer(vehicle).data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        vehicle = get_vehicle_for_user_or_404(request.user, int(pk))
        delete_vehicle_for_user(request.user, vehicle)
        return Response(status=status.HTTP_204_NO_CONTENT)


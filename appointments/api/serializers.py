from rest_framework import serializers

from appointments.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = (
            "id",
            "vehicle",
            "client",
            "station",
            "scheduled_at",
            "status",
            "assigned_diagnostician",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "client", "created_by", "created_at", "updated_at")


class AppointmentCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ("id", "status", "updated_at")
        read_only_fields = ("id", "status", "updated_at")


from __future__ import annotations

from rest_framework import serializers


class DashboardStatsQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"date_from": "date_from nie moze byc pozniejsze od date_to."})
        return attrs


class CountByDateSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField(min_value=0)


class CountByMonthSerializer(serializers.Serializer):
    month = serializers.CharField()
    count = serializers.IntegerField(min_value=0)


class VehicleTypeStatsSerializer(serializers.Serializer):
    vehicle_type = serializers.CharField()
    inspections_count = serializers.IntegerField(min_value=0)


class DashboardStatsSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    metrics = serializers.DictField()
    completed_inspections_daily = CountByDateSerializer(many=True)
    completed_inspections_monthly = CountByMonthSerializer(many=True)
    top_vehicle_types = VehicleTypeStatsSerializer(many=True)


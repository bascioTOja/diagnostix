from rest_framework import serializers

from inspections.models import Inspection


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = (
            "id",
            "appointment",
            "result",
            "notes",
            "detected_defects",
            "repair_recommendations",
            "next_inspection_date",
            "diagnostician",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "appointment", "diagnostician", "created_at", "updated_at")


class FinalizeInspectionSerializer(serializers.Serializer):
    result = serializers.ChoiceField(choices=list(Inspection._meta.get_field("result").choices))
    notes = serializers.CharField(required=False, allow_blank=True)
    detected_defects = serializers.CharField(required=False, allow_blank=True)
    repair_recommendations = serializers.CharField(required=False, allow_blank=True)
    next_inspection_date = serializers.DateField(required=False, allow_null=True)


from rest_framework import serializers

from .models import MitigationInterventionMaster, MitigationPlanItem


class MitigationInterventionMasterSerializer(serializers.ModelSerializer):
    vulnerable_asset = serializers.SerializerMethodField()

    class Meta:
        model = MitigationInterventionMaster
        fields = [
            "id",
            "theme",
            "subtheme",
            "housing_type",
            "road_type",
            "bridge_type",
            "electric_type",
            "intervention_type",
            "intervention_name",
            "display_note",
            "unit",
            "area",
            "default_quantity",
            "unit_cost_rs",
            "status",
            "vulnerable_asset",
        ]

    def get_vulnerable_asset(self, obj):
        if obj.housing_type_id:
            return obj.housing_type.house_type
        if obj.road_type_id:
            return obj.road_type.name
        if obj.bridge_type_id:
            return obj.bridge_type.name
        if obj.electric_type_id:
            return obj.electric_type.name
        return ""


class MitigationPlanItemSerializer(serializers.ModelSerializer):
    master_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MitigationPlanItem
        fields = [
            "id",
            "village",
            "typology",
            "vulnerability_type",
            "master",
            "quantity",
            "unit_cost_rs",
            "estimated_cost_rs",
            "target_beneficiaries",
            "priority_rank",
            "remarks",
            "location_text",
            "timeline_start",
            "timeline_end",
            "status",
            "master_data",
        ]

    def get_master_data(self, obj):
        master = obj.master
        if not master:
            return None
        return {
            "id": master.id,
            "theme": master.theme,
            "subtheme": master.subtheme,
            "vulnerable_asset": MitigationInterventionMasterSerializer(
                master
            ).get_vulnerable_asset(master),
            "intervention_type": master.intervention_type,
            "intervention_name": master.intervention_name,
            "display_note": master.display_note,
            "unit": master.unit,
            "default_quantity": master.default_quantity,
            "unit_cost_rs": master.unit_cost_rs,
            "status": master.status,
        }

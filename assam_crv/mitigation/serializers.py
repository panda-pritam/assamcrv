from rest_framework import serializers

from .models import MitigationInterventionMaster, MitigationPlanItem


class MitigationInterventionMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MitigationInterventionMaster
        fields = "__all__"


class MitigationPlanItemSerializer(serializers.ModelSerializer):
    master_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MitigationPlanItem
        fields = [
            "id",
            "village",
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
            "vulnerable_asset": master.vulnerable_asset,
            "intervention_type": master.intervention_type,
            "intervention_name": master.intervention_name,
            "display_note": master.display_note,
            "unit": master.unit,
            "default_quantity": master.default_quantity,
            "unit_cost_rs": master.unit_cost_rs,
            "status": master.status,
        }

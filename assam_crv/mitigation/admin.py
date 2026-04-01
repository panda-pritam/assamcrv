from django.contrib import admin

from .models import MitigationInterventionMaster, MitigationPlanItem


@admin.register(MitigationInterventionMaster)
class MitigationInterventionMasterAdmin(admin.ModelAdmin):
    list_display = (
        "theme",
        "subtheme",
        "get_vulnerable_asset",
        "intervention_type",
        "status",
    )
    list_filter = ("theme", "subtheme", "status")
    search_fields = ("intervention_name",)

    def get_vulnerable_asset(self, obj):
        if obj.housing_type_id:
            return obj.housing_type.house_type
        if obj.road_type_id:
            return obj.road_type.name
        if obj.bridge_type_id:
            return obj.bridge_type.name
        if obj.electric_type_id:
            return obj.electric_type.name
        return "-"

    get_vulnerable_asset.short_description = "Vulnerable Asset"


@admin.register(MitigationPlanItem)
class MitigationPlanItemAdmin(admin.ModelAdmin):
    list_display = ("id", "village", "master", "quantity", "status")
    list_filter = ("status",)

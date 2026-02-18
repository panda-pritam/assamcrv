from django.contrib import admin

from .models import MitigationInterventionMaster, MitigationPlanItem


@admin.register(MitigationInterventionMaster)
class MitigationInterventionMasterAdmin(admin.ModelAdmin):
    list_display = ("theme", "subtheme", "vulnerable_asset", "intervention_type", "status")
    list_filter = ("theme", "subtheme", "status")
    search_fields = ("vulnerable_asset", "intervention_name")


@admin.register(MitigationPlanItem)
class MitigationPlanItemAdmin(admin.ModelAdmin):
    list_display = ("id", "village", "master", "quantity", "status")
    list_filter = ("status",)

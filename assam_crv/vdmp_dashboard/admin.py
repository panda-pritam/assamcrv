from django.contrib import admin
from .models import ( HouseholdSurvey, Transformer, Commercial, Critical_Facility, ElectricPole,
                      VillageListOfAllTheDistricts, VillageRoadInfo,VDMP_Maps_Data, BridgeSurvey, Risk_Assesment)


@admin.register(Risk_Assesment)
class Risk_AssesmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'village',)
    search_fields = ('village',)
    list_filter = ('village','hazard')

@admin.register(BridgeSurvey)
class BridgeSurveyAdmin(admin.ModelAdmin):
    list_display = ('id', 'village', 'bridge_surface_type', 'length_meters', 'width_meters')
    search_fields = ('village',)
    list_filter = ('village', 'bridge_surface_type')

@admin.register(HouseholdSurvey)
class HouseholdSurveyAdmin(admin.ModelAdmin):
    list_display = ('id', 'village','village_code')
    search_fields = ('village',)
    list_filter = ('village',)

@admin.register(Transformer)
class TransformerAdmin(admin.ModelAdmin):
    list_display = ('id', 'village',)
    search_fields = ('village',)
    list_filter = ('village',)

@admin.register(Commercial)
class CommercialAdmin(admin.ModelAdmin):
    list_display = ('id', 'village',)
    search_fields = ('village',)
    list_filter = ('village',)

@admin.register(Critical_Facility)
class Critical_FacilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'village',)
    search_fields = ('village',)
    list_filter = ('village',)

@admin.register(ElectricPole)
class ElectricPoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'village',)
    search_fields = ('village',)
    list_filter = ('village',)

@admin.register(VillageListOfAllTheDistricts)
class VillageListOfAllTheDistrictsAdmin(admin.ModelAdmin):
    list_display = ('id', 'village', 'district_name', 'village_name')
    search_fields = ('village_name', 'district_name')
    list_filter = ('district_name',)

@admin.register(VillageRoadInfo)
class VillageRoadInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'village', 'road_surface_type', 'road_length_m')
    search_fields = ('village_name', 'road_surface_type')
    list_filter = ('village', 'road_surface_type')

@admin.register(VDMP_Maps_Data)
class VDMP_Maps_DataAdmin(admin.ModelAdmin):
    list_display = ('id', 'village',)
    search_fields = ('village',)
    list_filter = ('village',)
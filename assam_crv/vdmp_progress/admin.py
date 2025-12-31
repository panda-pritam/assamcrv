from django.contrib import admin
from .models import tblVDMP_Activity, tblVDMP_Activity_Status,house_type_combination_mapping,house_type,flood_MDR_table,EQ_MDR_table,wind_MDR_table,Risk_Assessment_Result

@admin.register(tblVDMP_Activity_Status)
class VDMPActivityStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity', 'village', 'status', 'last_update')
    list_filter = ('status', 'last_update', 'activity__name', 'village__gram_panchayat__circle__district__name')
    search_fields = ('activity__name', 'village__name', 'status',)
    ordering = ('-last_update',)

@admin.register(tblVDMP_Activity)
class VDMPActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name' )
    search_fields = ('name',)


@admin.register(house_type)
class HouseTypeAdmin(admin.ModelAdmin):
    list_display = ('house_type_id', 'house_type', 'per_unit_cost')
    

@admin.register(house_type_combination_mapping)
class HouseTypeCombinationMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'wall_type', 'roof_type', 'floor_type', 'combo_key', 'house_type')

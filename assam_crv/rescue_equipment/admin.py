from django.contrib import admin
from .models import tbl_Rescue_Equipment, tbl_Rescue_Equipment_Status

@admin.register(tbl_Rescue_Equipment)
class RescueEquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'task_force')
    search_fields = ('name','task_force')
    ordering = ('name',)

@admin.register(tbl_Rescue_Equipment_Status)
class RescueEquipmentStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment', 'village', 'count', 'last_update', 'updated_by')
    search_fields = ('equipment__name', 'village__name')
    list_filter = ('equipment',)
    ordering = ('-last_update',)

    def updated_by(self, obj):
        return obj.updated_by.username if obj.updated_by else 'Unknown'
    updated_by.short_description = 'Updated By'
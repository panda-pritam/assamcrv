from django.contrib import admin
from .models import tblVDMP_Activity, tblVDMP_Activity_Status

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
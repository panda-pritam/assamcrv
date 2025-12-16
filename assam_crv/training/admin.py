from django.contrib import admin
from .models import tbl_Training_Activities_Status, tbl_Training_Activities


@admin.register(tbl_Training_Activities_Status)
class TrainingActivitiesStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity', 'village', 'status', 'last_update', 'updated_by')
    search_fields = ('activity__name', 'village__name', 'status')
    list_filter = ('status',)
    ordering = ('-last_update',)

    def updated_by(self, obj):
        return obj.updated_by.username if obj.updated_by else 'Unknown'
    updated_by.short_description = 'Updated By'

@admin.register(tbl_Training_Activities)
class TrainingActivitiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

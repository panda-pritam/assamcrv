from django.contrib import admin
from .models import LineDepartmentMaster,LineDepartment


@admin.register(LineDepartmentMaster)
class LineDepartmentMasterAdmin(admin.ModelAdmin):
    list_display = ('section', 'description', 'created_at', 'updated_at')
    search_fields = ('section', 'description')
    ordering = ('section',)
    list_per_page = 20


@admin.register(LineDepartment)
class LineDepartmentAdmin(admin.ModelAdmin):
    list_display = (
        'section_master',
        'village',
        'contact_name',
        'phone_number',
        'official_number',
        'created_at',
    )
    search_fields = (
        'section_master__section',
        'village__name',
        'contact_name',
        'phone_number',
        'official_number',
    )
    list_filter = ('section_master', 'village')
    ordering = ('section_master',)
    autocomplete_fields = ('village', 'section_master')
    list_per_page = 25

# Register your models here.

from django.contrib import admin
from .models import FieldImage

@admin.register(FieldImage)
class FieldImageAdmin(admin.ModelAdmin):
    list_display = ['village', 'category', 'name', 'upload_datetime', 'uploaded_by']
    list_filter = ['category', 'village', 'upload_datetime']
    search_fields = ['village__name', 'name', 'category']
    readonly_fields = ['upload_datetime']

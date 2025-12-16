from django.contrib import admin
from .models import GeoserverLayers

@admin.register(GeoserverLayers)
class GeoserverLayersAdmin(admin.ModelAdmin):
    list_display = ('title', 'layer_name', 'workspace')
    search_fields = ('title', 'layer_name', 'workspace')

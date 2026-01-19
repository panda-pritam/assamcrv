from django.contrib import admin
from .models import GeoserverLayers, village_flood_raster_Files

@admin.register(GeoserverLayers)
class GeoserverLayersAdmin(admin.ModelAdmin):
    list_display = ('title', 'layer_name', 'workspace')
    search_fields = ('title', 'layer_name', 'workspace')


@admin.register(village_flood_raster_Files)
class VillageFloodRasterFilesAdmin(admin.ModelAdmin):
    list_display = ('village', 'layer_name', 'workspace', 'created_at')
    search_fields = ('village__village_name', 'layer_name', 'workspace')
    readonly_fields = ('created_at',)

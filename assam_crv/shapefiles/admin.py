from django.contrib import admin

# Register your models here.
from .models import PraBoundary, ExposureRiver, ExposureRoadVillage


@admin.register(ExposureRoadVillage)
class ExposureRoadVillageAdmin(admin.ModelAdmin):
    list_display = ('vill_id',)

@admin.register(PraBoundary)
class PraBoundaryAdmin(admin.ModelAdmin):
    list_display = ('village',)

@admin.register(ExposureRiver)
class ExposureRiverAdmin(admin.ModelAdmin):
    list_display = ('village',)
from django.db import models

from village_profile.models import tblVillage, tblDistrict

# Create your models here.
class GeoserverLayers(models.Model):
    title = models.CharField(max_length=255)
    title_as = models.CharField(max_length=255, blank=True, null=True)
    title_bn = models.CharField(max_length=255, blank=True, null=True)    
    layer_name = models.CharField(max_length=255)
    workspace = models.CharField(max_length=255)


def flood_map_upload_to(instance, filename):
    village_id = instance.village_id or "unknown"
    return f"maps/flood/{village_id}/{filename}"


def wind_map_upload_to(instance, filename):
    district_id = instance.district_id or "unknown"
    return f"maps/wind/{district_id}/{filename}"


def eq_map_upload_to(instance, filename):
    district_id = instance.district_id or "unknown"
    return f"maps/eq/{district_id}/{filename}"


class village_flood_raster_Files(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    raster_file = models.FileField(upload_to='pipeline_data/flood_raster/')
    flood_map_image = models.FileField(upload_to=flood_map_upload_to, blank=True, null=True)
    layer_name = models.CharField(max_length=255, blank=True, null=True)
    workspace = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.village.name} - {self.layer_name}"


class district_wind_raster_file(models.Model):
    district = models.ForeignKey(tblDistrict, on_delete=models.CASCADE)
    raster_file = models.FileField(upload_to='pipeline_data/wind_raster/',blank=True, null=True, default="pipeline_data/wind_raster/Wind.tif")
    wind_map_image = models.FileField(upload_to=wind_map_upload_to, blank=True, null=True)
    layer_name = models.CharField(max_length=255, blank=True, null=True)
    workspace = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.district.name} - {self.layer_name}"


class district_eq_raster_file(models.Model):
    district = models.ForeignKey(tblDistrict, on_delete=models.CASCADE)
    raster_file = models.FileField(upload_to='pipeline_data/eq_raster/',blank=True, null=True, default="pipeline_data/eq_raster/eq.tif")
    eq_map_image = models.FileField(upload_to=eq_map_upload_to, blank=True, null=True)
    layer_name = models.CharField(max_length=255, blank=True, null=True)
    workspace = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.district.name} - {self.layer_name}"

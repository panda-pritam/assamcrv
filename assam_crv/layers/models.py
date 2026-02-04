from django.db import models

from village_profile.models import tblVillage

# Create your models here.
class GeoserverLayers(models.Model):
    title = models.CharField(max_length=255)
    title_as = models.CharField(max_length=255, blank=True, null=True)
    title_bn = models.CharField(max_length=255, blank=True, null=True)    
    layer_name = models.CharField(max_length=255)
    workspace = models.CharField(max_length=255)


class village_flood_raster_Files(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    raster_file = models.FileField(upload_to='pipeline_data/flood_raster/')
    flood_map_image = models.FileField(upload_to='maps/', blank=True, null=True)
    layer_name = models.CharField(max_length=255, blank=True, null=True)
    workspace = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.village.name} - {self.layer_name}"
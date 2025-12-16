from django.db import models

# Create your models here.
class GeoserverLayers(models.Model):
    title = models.CharField(max_length=255)
    title_as = models.CharField(max_length=255, blank=True, null=True)
    title_bn = models.CharField(max_length=255, blank=True, null=True)    
    layer_name = models.CharField(max_length=255)
    workspace = models.CharField(max_length=255)
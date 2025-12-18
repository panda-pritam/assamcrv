from django.db import models
from django.conf import settings

# Create your models here.

class tblDistrict(models.Model):
    name = models.CharField(max_length=100)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    code =  models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    mobileDBDistrictID = models.CharField(max_length=100, null=True, blank=True)
    district_layer_url = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class tblCircle(models.Model):
    district = models.ForeignKey(tblDistrict, on_delete=models.CASCADE) 
    name = models.CharField(max_length=100)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.name

class tblGramPanchayat(models.Model):
    circle = models.ForeignKey(tblCircle, on_delete=models.CASCADE) 
    name = models.CharField(max_length=100)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.name

class tblVillage(models.Model):
    gram_panchayat = models.ForeignKey(tblGramPanchayat, on_delete=models.CASCADE) 
    name = models.CharField(max_length=100)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    code =  models.CharField(max_length=100,null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    

    def __str__(self):
        return self.name

class district_village_mapping(models.Model):
    district = models.ForeignKey(tblDistrict, on_delete=models.CASCADE)
    district_code = models.CharField(max_length=100, null=True, blank=True)
    circle = models.ForeignKey(tblCircle, on_delete=models.CASCADE, null=True, blank=True)
    gram_panchayat = models.ForeignKey(tblGramPanchayat, on_delete=models.CASCADE, null=True, blank=True)
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE, null=True, blank=True)
    village_code = models.CharField(max_length=100, null=True, blank=True)
    mobileDBVillageID = models.CharField(max_length=100, null=True, blank=True)
    mobileDBDistrictID = models.CharField(max_length=100, null=True, blank=True)
    layer_name = models.CharField(max_length=100, null=True, blank=True)
    userID = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.district.name} - {self.village.name}"
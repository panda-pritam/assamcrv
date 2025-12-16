from django.db import models

# Create your models here.

class tblDistrict(models.Model):
    name = models.CharField(max_length=100)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    code =  models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

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
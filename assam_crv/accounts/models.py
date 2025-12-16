

from django.db import models
from django.contrib.auth.models import AbstractUser
from village_profile.models import tblDistrict, tblVillage, tblGramPanchayat, tblCircle

# Optional: your custom Role model
class tblRoles(models.Model):
    name = models.CharField(max_length=255)
    name_bn = models.CharField(max_length=255, blank=True, null=True)
    name_as = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class tblDepartment(models.Model):
    name = models.CharField(max_length=255)
    name_bn = models.CharField(max_length=255, blank=True, null=True)
    name_as = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Custom user extending AbstractUser
class tblUser(AbstractUser):
    email = models.EmailField(unique=True)
    mobile = models.BigIntegerField(blank=True, null=True)
    district = models.ForeignKey(tblDistrict, on_delete=models.SET_NULL, null=True, blank=True)
    gram_panchayat = models.ForeignKey(tblGramPanchayat, on_delete=models.SET_NULL, null=True, blank=True)
    circle = models.ForeignKey(tblCircle, on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey(tblVillage, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(tblRoles, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(tblDepartment, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username


class tblModule(models.Model):
    name = models.CharField(max_length=255)
    name_bn = models.CharField(max_length=255, blank=True, null=True)
    name_as = models.CharField(max_length=255, blank=True, null=True)
    div_id = models.CharField(max_length=255, blank=True, null=True)
    class_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class tblModulePermission(models.Model):
    department = models.ForeignKey(tblDepartment, on_delete=models.CASCADE)
    module = models.ForeignKey(tblModule, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.department.name} - {self.module.name}"
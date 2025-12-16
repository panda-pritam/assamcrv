from django.db import models
from accounts.models import tblUser
from village_profile.models import tblDistrict, tblCircle, tblGramPanchayat, tblVillage

class tbl_Rescue_Equipment(models.Model):
    name = models.CharField(max_length=555)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    task_force = models.CharField(max_length=555, null=True)
    task_force_bn = models.CharField(max_length=555, null=True)
    task_force_as = models.CharField(max_length=555, null=True)
    specification = models.CharField(max_length=555, null=True)
    specification_bn = models.CharField(max_length=555, null=True)
    specification_as = models.CharField(max_length=555, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.task_force} - {self.specification}"

class tbl_Rescue_Equipment_Status(models.Model):
    equipment = models.ForeignKey(tbl_Rescue_Equipment, on_delete=models.CASCADE)
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(tblUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.equipment.name} - {self.village.name} - {self.count}"

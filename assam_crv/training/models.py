from django.db import models
from accounts.models import tblUser
from village_profile.models import tblDistrict, tblCircle, tblGramPanchayat, tblVillage

class tbl_Training_Activities(models.Model):
    name = models.CharField(max_length=555)
    name_bn = models.CharField(max_length=555, null=True, blank=True)
    name_as = models.CharField(max_length=555, null=True, blank=True)

    def __str__(self):
        return self.name

class tbl_Training_Activities_Status(models.Model):
    CHOICES = (
        ('Completed', 'Completed'),
        ('Scheduled', 'Scheduled'),
    )
    activity = models.ForeignKey(tbl_Training_Activities, on_delete=models.CASCADE)
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    status = models.CharField(max_length=55, choices=CHOICES, default='Scheduled')
    implemented_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    last_update = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(tblUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.activity.name} - {self.village.name} - {self.status}"

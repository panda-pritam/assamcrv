from django.db import models
from village_profile.models import tblVillage
from accounts.models import tblUser

class tblVDMP_Activity(models.Model):
    name = models.CharField(max_length=555)
    name_bn = models.CharField(max_length=100, null=True, blank=True)
    name_as = models.CharField(max_length=100, null=True, blank=True)
    order=models.IntegerField(default=None,null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

class tblVDMP_Activity_Status(models.Model):
    STATUS = (
        ('Completed', 'Completed'),
        ('In Progress', 'In Progress'),
        ('Not Started', 'Not Started'),
    )
    activity = models.ForeignKey(tblVDMP_Activity, on_delete=models.CASCADE)
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default='Not Started')
    last_update = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(tblUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.activity.name} - {self.village.name} - {self.status}"

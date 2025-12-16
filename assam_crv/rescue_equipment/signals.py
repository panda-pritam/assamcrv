
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import  tbl_Rescue_Equipment, tbl_Rescue_Equipment_Status
from village_profile.models import tblVillage

@receiver(post_save, sender=tbl_Rescue_Equipment)
def create_equipment_status_for_all_villages(sender, instance, created, **kwargs):
    if created:
        villages = tblVillage.objects.all()
        status_objects = [
            tbl_Rescue_Equipment_Status(equipment=instance, village=village)
            for village in villages
        ]
        tbl_Rescue_Equipment_Status.objects.bulk_create(status_objects)
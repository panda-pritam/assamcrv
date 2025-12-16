from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import tbl_Training_Activities, tbl_Training_Activities_Status
from village_profile.models import tblVillage

@receiver(post_save, sender=tbl_Training_Activities)
def create_status_for_all_villages(sender, instance, created, **kwargs):
    if created:
        villages = tblVillage.objects.all()
        status_objects = [
            tbl_Training_Activities_Status(activity=instance, village=village)
            for village in villages
        ]
        tbl_Training_Activities_Status.objects.bulk_create(status_objects)

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import tblVDMP_Activity, tblVDMP_Activity_Status
from village_profile.models import tblVillage

@receiver(post_save, sender=tblVDMP_Activity)
def create_status_for_all_villages(sender, instance, created, **kwargs):
    """
    Create a VDMP activity status entry for all villages on activity creation.
    Triggered automatically when a new tblVDMP_Activity instance is saved.
    """
    if created:
        villages = tblVillage.objects.all()
        status_objects = [
            tblVDMP_Activity_Status(activity=instance, village=village)
            for village in villages
        ]
        tblVDMP_Activity_Status.objects.bulk_create(status_objects, ignore_conflicts=True)

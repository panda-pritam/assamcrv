# village_profile/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from village_profile.models import tblVillage
from vdmp_progress.models import tblVDMP_Activity, tblVDMP_Activity_Status
from rescue_equipment.models import tbl_Rescue_Equipment, tbl_Rescue_Equipment_Status
from training.models import tbl_Training_Activities, tbl_Training_Activities_Status


@receiver(post_save, sender=tblVillage)
def create_related_objects_for_new_village(sender, instance, created, **kwargs):
    if not created:
        return

    # 2. Create tblVDMP_Activity_Status for all existing VDMP activities
    for activity in tblVDMP_Activity.objects.all():
        tblVDMP_Activity_Status.objects.create(
            activity=activity,
            village=instance,
        )

    # 3. Create tbl_Rescue_Equipment_Status for all existing rescue equipment
    for eqp in tbl_Rescue_Equipment.objects.all():
        tbl_Rescue_Equipment_Status.objects.create(
            equipment=eqp,
            village=instance,
        )

    # 4. Create tbl_Training_Activities_Status for all existing training activities
    for activity in tbl_Training_Activities.objects.all():
        tbl_Training_Activities_Status.objects.create(
            activity=activity,
            village=instance,
        )

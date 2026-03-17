from django.db import models

from village_profile.models import tblVillage


class MitigationInterventionMaster(models.Model):
    theme = models.CharField(max_length=200)
    subtheme = models.CharField(max_length=200)
    vulnerable_asset = models.CharField(max_length=200, blank=True)
    intervention_type = models.CharField(max_length=200, blank=True)
    intervention_name = models.TextField()
    display_note = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    area = models.DecimalField(
        max_digits=12, decimal_places=2, default=450.00
    )
    default_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    unit_cost_rs = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=50, default="active")

    def __str__(self):
        return f"{self.theme} / {self.subtheme} - {self.intervention_name[:50]}"


class MitigationPlanItem(models.Model):
    village = models.ForeignKey(
        tblVillage, on_delete=models.PROTECT, null=True, blank=True
    )
    master = models.ForeignKey(
        MitigationInterventionMaster, on_delete=models.PROTECT
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost_rs = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    estimated_cost_rs = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    target_beneficiaries = models.IntegerField(null=True, blank=True)
    priority_rank = models.IntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    location_text = models.CharField(max_length=255, blank=True)
    timeline_start = models.DateField(null=True, blank=True)
    timeline_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default="draft")

    def __str__(self):
        return f"{self.master_id} - {self.quantity}"

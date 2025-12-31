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


class tblVDMP_Activity_Import_Status(models.Model):
    activity = models.ForeignKey(tblVDMP_Activity, on_delete=models.CASCADE)
    activity_status = models.ForeignKey(tblVDMP_Activity_Status, on_delete=models.CASCADE)
    rows_imported = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_text = models.TextField(null=True, blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.activity_status} - Imported: {self.rows_imported}, Errors: {self.error_count}"


class house_type(models.Model):
    house_type_id = models.AutoField(primary_key=True)
    house_type = models.CharField(max_length=100)
    per_unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discription = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.house_type


class house_type_combination_mapping(models.Model):
    wall_type = models.CharField(max_length=100)
    roof_type = models.CharField(max_length=100)
    floor_type = models.CharField(max_length=100)
    combo_key = models.CharField(max_length=300)
    house_type = models.ForeignKey(house_type, on_delete=models.CASCADE,blank=True, null=True)
    is_New = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.combo_key} - {self.house_type}"
    

class flood_MDR_table(models.Model):
    flood_depth_m=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    MDR_value=models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)  
    house_type = models.ForeignKey(house_type, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.flood_depth_m} - {self.MDR_value}"
    

class EQ_MDR_table(models.Model):
    PGA_g=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    MDR_value=models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)  
    house_type = models.ForeignKey(house_type, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.PGA_g} - {self.MDR_value}"
    
class wind_MDR_table(models.Model):
    wind_speed_kmph=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    MDR_value=models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    house_type = models.ForeignKey(house_type, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.wind_speed_kmph} - {self.MDR_value}"


class Risk_Assessment_Result(models.Model):
    ASSET_TYPE_CHOICES = [
        ('household', 'Household'),
        ('commercial', 'Commercial'),
        ('critical_facility', 'Critical Facility'),
    ]
    
    # Reference and location data
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    reference_id = models.CharField(max_length=255, null=True, blank=True)  # Original record ID
    village_name = models.CharField(max_length=255, null=True, blank=True)
    village_code = models.CharField(max_length=255, null=True, blank=True)
    point_id = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
    
    # Asset classification
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    
    # Building characteristics
    wall_type = models.CharField(max_length=255, null=True, blank=True)
    roof_type = models.CharField(max_length=255, null=True, blank=True)
    floor_type = models.CharField(max_length=255, null=True, blank=True)
    building_length_ft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    building_width_ft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    building_area_sqft = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # House type mapping
    house_type_id = models.ForeignKey(house_type, on_delete=models.SET_NULL, null=True, blank=True)
    house_type_name = models.CharField(max_length=255, null=True, blank=True)
    # house_type_id = models.IntegerField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    replacement_cost_inr = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Hazard data
    eq_hazard = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    wind_hazard = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    flood_hazard = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    
    # MDR (Mean Damage Ratio) data
    flood_hazard_mdr = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    eq_hazard_mdr = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    wind_hazard_mdr = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    
    # Loss calculations
    flood_loss = models.DecimalField(max_digits=15, decimal_places=8, null=True, blank=True)
    eq_loss = models.DecimalField(max_digits=15, decimal_places=8, null=True, blank=True)
    wind_loss = models.DecimalField(max_digits=15, decimal_places=8, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['reference_id', 'asset_type', 'village']
        indexes = [
            models.Index(fields=['village', 'asset_type']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"{self.village_name} - {self.asset_type} - {self.point_id}"


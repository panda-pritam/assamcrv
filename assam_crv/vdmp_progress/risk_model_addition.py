class Risk_Assessment_Result(models.Model):
    ASSET_TYPE_CHOICES = [
        ('household', 'Household'),
        ('commercial', 'Commercial'),
        ('critical_facility', 'Critical Facility'),
    ]
    
    # Reference and location data
    village = models.ForeignKey('village_profile.tblVillage', on_delete=models.CASCADE)
    reference_id = models.CharField(max_length=255, null=True, blank=True)
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
    house_type = models.ForeignKey(house_type, on_delete=models.SET_NULL, null=True, blank=True)
    house_type_name = models.CharField(max_length=255, null=True, blank=True)
    house_type_id = models.IntegerField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    replacement_cost_inr = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Hazard data
    eq_hazard = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    wind_hazard = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    flood_hazard = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # MDR data
    flood_hazard_mdr = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    eq_hazard_mdr = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    wind_hazard_mdr = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Loss calculations
    flood_loss = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    eq_loss = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    wind_loss = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
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
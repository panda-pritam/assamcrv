from django.db import models
from village_profile.models import tblVillage

EQUIPMENT_CHOICES = [

         ('tractor', 'Tractor'),

         ('harvester', 'Harvester'),

         ('plough', 'Plough'),

         ('thresher', 'Thresher'),

         ('sprayer', 'Sprayer'),

         ('pump_set', 'Pump Set'),

         ('other', 'Other'),

     ]


class PRA_assets(models.Model):
     village = models.ForeignKey(tblVillage, on_delete=models.CASCADE) 
     
     village_name = models.CharField(max_length=200, blank=True, null=True)
     vill_id = models.CharField(max_length=50, blank=True, null=True)
     equipment = models.CharField(max_length=200, blank=True, null=True)   
     name_of_the_owner = models.CharField(max_length=500, blank=True, null=True)
     phone_number = models.CharField(max_length=15, blank=True, null=True)
     asset_count = models.PositiveIntegerField(blank=True, null=True)
     remark = models.TextField(blank=True, null=True)
     created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
     updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

     def __str__(self):
         return f"{self.village_name} - {self.equipment}"


class PRA_main(models.Model):

     village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
     village_code = models.CharField(
          max_length=50,
          db_index=True,
          blank=True,
          null=True
     )
     # Population details
     children_below_6_male = models.PositiveIntegerField(default=0, blank=True, null=True)
     children_below_6_female = models.PositiveIntegerField(default=0, blank=True, null=True)
     persons_with_disability = models.PositiveIntegerField(default=0, blank=True, null=True)
     persons_with_chronic_illness = models.PositiveIntegerField(default=0, blank=True, null=True)

     # Distance to facilities (in km)
     nearest_phc_km = models.FloatField(blank=True, null=True)
     nearest_chc_km = models.FloatField(blank=True, null=True)
     nearest_hospital_km = models.FloatField(blank=True, null=True)
     nearest_veterinary_clinic_km = models.FloatField(blank=True, null=True)
     nearest_post_office_km = models.FloatField(blank=True, null=True)
#     nearest_police_station_km = models.FloatField()
     nearest_bank_atm_km = models.FloatField(blank=True, null=True)
     nearest_ambulance_km = models.FloatField(blank=True, null=True)
     nearest_bus_service_km = models.FloatField(blank=True, null=True)
     main_market_km = models.FloatField(blank=True, null=True)
     nearest_ration_shop_km = models.FloatField(blank=True, null=True)
     nearest_high_school_km = models.FloatField(blank=True, null=True)
     nearest_higher_secondary_km = models.FloatField(blank=True, null=True)
     nearest_college_km = models.FloatField(blank=True, null=True)

     # Insurance & occupation

     farmers_agriculture_insurance = models.PositiveIntegerField(default=0, blank=True, null=True)
     farmers_livestock_insurance = models.PositiveIntegerField(default=0, blank=True, null=True)
     occupational_category = models.CharField(max_length=100, blank=True, null=True)


     # Disaster risk details

     flood_frequency = models.CharField(max_length=50, blank=True, null=True)
     flood_severity = models.CharField(max_length=50, blank=True, null=True)
     erosion_hazard_frequency = models.CharField(max_length=50, blank=True, null=True)
     erosion_hazard_severity = models.CharField(max_length=50, blank=True, null=True)
     strong_wind_hazard_frequency = models.CharField(max_length=50, blank=True, null=True)
     strong_wind_hazard_severity = models.CharField(max_length=50, blank=True, null=True)
     earthquake_hazard_frequency = models.CharField(max_length=50, blank=True, null=True)
     earthquake_hazard_severity = models.CharField(max_length=50, blank=True, null=True)

     # Geography

     distance_from_district_headquarter_km = models.FloatField(blank=True, null=True)
     average_elevation_msl = models.FloatField(blank=True, null=True)


     # Groups & organizations

     farmers_groups = models.TextField(blank=True, null=True)
     weavers_groups = models.TextField(blank=True, null=True)
     ngos_cgos = models.TextField(blank=True, null=True)

     # Services & schemes

     domestic_solid_waste_management = models.TextField(blank=True, null=True)

     government_schemes_contact = models.TextField(blank=True, null=True)


     # Environmental issues

     siltation = models.BooleanField(default=False, blank=True, null=True)

     water_logging_agriculture_land = models.BooleanField(default=False, blank=True, null=True)

     encroachment_of_wetlands = models.BooleanField(default=False, blank=True, null=True)

     modification_of_natural_drains = models.BooleanField(default=False, blank=True, null=True)


     created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

     updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


     def __str__(self):

         return f"Village {self.village}"




class PRA_shelter(models.Model):
     village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
     state = models.CharField(max_length=100, blank=True, null=True)
     district = models.CharField(max_length=100, blank=True, null=True)
     village_name = models.CharField(max_length=200, blank=True, null=True)
     vill_id = models.CharField(max_length=50, blank=True, null=True)
     name_of_shelter = models.CharField(max_length=500, blank=True, null=True)
     contact_person = models.CharField(max_length=200, blank=True, null=True)
     phone_number = models.CharField(max_length=15, blank=True, null=True)
     number_of_rooms = models.PositiveIntegerField(blank=True, null=True)
     capacity = models.PositiveIntegerField(blank=True, null=True)
     toilet_facility_available = models.CharField(max_length=100, blank=True, null=True)
     drinking_water_facility_available = models.CharField(max_length=100, blank=True, null=True)
     alternate_power_source = models.CharField(max_length=100, blank=True, null=True)
     created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
     updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

     def __str__(self):
         return f"{self.village_name} - {self.name_of_shelter}"
     



class FGD_livelihood_summary(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    village_name = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    dist_id = models.CharField(max_length=50, blank=True, null=True)
    vill_id = models.CharField(max_length=50, blank=True, null=True)
    
    cropping_pattern = models.TextField(blank=True, null=True)
    cropping_calendar = models.TextField(blank=True, null=True)
    livestock_and_allied_activities = models.TextField(blank=True, null=True)
    departmental_support = models.TextField(blank=True, null=True)
    challenges_in_agriculture = models.TextField(blank=True, null=True)
    challenges_in_livestock = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Agriculture & Livestock - Village {self.village}"




class LineDepartmentMaster(models.Model):
    section = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.section


class LineDepartment(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    vill_id = models.CharField(max_length=50, blank=True, null=True)
    section_master = models.ForeignKey(LineDepartmentMaster, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.section_master.section} - {self.village.name}"





class FGD_wash_summary(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    village_name = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    dist_id = models.CharField(max_length=50, blank=True, null=True)
    vill_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Drinking Water
    drinking_water_sources_access = models.TextField(blank=True, null=True)
    adequacy_reliability = models.TextField(blank=True, null=True)
    equity_inclusion = models.TextField(blank=True, null=True)
    affordability = models.TextField(blank=True, null=True)
    water_quality = models.TextField(blank=True, null=True)
    traditional_practices = models.TextField(blank=True, null=True)
    community_role_jjm_implementation = models.TextField(blank=True, null=True)
    infrastructure_damage = models.TextField(blank=True, null=True)

    # Sanitation & Hygiene
    sanitation_existing_facilities = models.TextField(blank=True, null=True)
    impact_of_floods = models.TextField(blank=True, null=True)
    erosion_impact = models.TextField(blank=True, null=True)
    hygiene_practices = models.TextField(blank=True, null=True)
    health_concerns = models.TextField(blank=True, null=True)

    # Community
    community_awareness = models.TextField(blank=True, null=True)
    community_participation_resilience = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Water & Sanitation - Village {self.village}"
from django.db import models
from village_profile.models import tblVillage


class AttributeMapping(models.Model):
    MODEL_CHOICES = [
        ('HouseholdSurvey', 'Household Survey'),
        ('Commercial', 'Commercial'),
        ('Transformer',"Transformer"),
        ('Critical_Facility',"Critical_Facility"),
        ("ElectricPole","ElectricPole"),
        ("VillageListOfAllTheDistricts","VillageListOfAllTheDistricts"),
        ("VillageRoadInfo","VillageRoadInfo"),
        ("BridgeSurvey","")


    ]
    
    mobile_db_attribute_id = models.IntegerField(null=True, blank=True)
    attribute_text = models.CharField(max_length=500, null=True, blank=True)
    alias_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=50, choices=MODEL_CHOICES)
    is_calculated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    tab_id=models.IntegerField(null=True, blank=True)
    tab_name=models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # class Meta:
    #     unique_together = ['mobile_db_attribute_id']
    
    def __str__(self):
        return f"{self.model_name} - {self.alias_name}"


class HouseholdSurvey(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    dist_code = models.CharField(max_length=255, null=True, blank=True)
    district_code = models.CharField(max_length=255, null=True, blank=True)
    village_code = models.CharField(max_length=255, null=True, blank=True)
    point_id = models.CharField(max_length=255, null=True, blank=True)
    property_owner = models.CharField(max_length=255, null=True, blank=True)
    name_of_person = models.CharField(max_length=255, null=True, blank=True)
    name_of_hohh = models.CharField(max_length=255, null=True, blank=True)
    photo = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=255, null=True, blank=True)
    data_access = models.CharField(max_length=255, null=True, blank=True)
    community = models.CharField(max_length=255, null=True, blank=True)
    social_status = models.CharField(max_length=255, null=True, blank=True)
    economic_status = models.CharField(max_length=255, null=True, blank=True)
    wall_type = models.CharField(max_length=255, null=True, blank=True)
    roof_type = models.CharField(max_length=255, null=True, blank=True)
    floor_type = models.CharField(max_length=255, null=True, blank=True)
    plinth_or_stilt = models.CharField(max_length=255, null=True, blank=True)
    plinth_or_stilt_height_ft = models.CharField(max_length=255, null=True, blank=True)
    number_of_storeys = models.CharField(max_length=255, null=True, blank=True)
    number_of_males_including_children = models.CharField(max_length=255, null=True, blank=True)
    number_of_females_including_children = models.CharField(max_length=255, null=True, blank=True)
    children_below_6_years = models.CharField(max_length=255, null=True, blank=True)
    senior_citizens = models.CharField(max_length=255, null=True, blank=True)
    pregnant_women = models.CharField(max_length=255, null=True, blank=True)
    lactating_women = models.CharField(max_length=255, null=True, blank=True)
    persons_with_disability_or_chronic_disease = models.CharField(max_length=255, null=True, blank=True)
    drinking_water_source = models.CharField(max_length=255, null=True, blank=True)
    sanitation_facility = models.CharField(max_length=255, null=True, blank=True)
    toilet_wall_material = models.CharField(max_length=255, null=True, blank=True)
    toilet_roof_material = models.CharField(max_length=255, null=True, blank=True)
    digital_media_owned = models.CharField(max_length=255, null=True, blank=True)
    house_has_electric_connection = models.CharField(max_length=255, null=True, blank=True)
    source_of_electricity = models.CharField(max_length=255, null=True, blank=True)
    own_agriculture_land = models.CharField(max_length=255, null=True, blank=True)
    area_of_agriculture_land_owned_bigha = models.CharField(max_length=255, null=True, blank=True)
    land_area_annually_cultivated_bigha = models.CharField(max_length=255, null=True, blank=True)
    crops_cultivated = models.CharField(max_length=1055, null=True, blank=True)
    specify_other = models.CharField(max_length=255, null=True, blank=True)
    number_of_crops_normally_raised_every_year = models.CharField(max_length=255, null=True, blank=True)
    livelihood_primary = models.CharField(max_length=255, null=True, blank=True)
    livelihood_secondary = models.CharField(max_length=255, null=True, blank=True)
    do_you_have_big_cattle_cattle_buffalo = models.CharField(max_length=255, null=True, blank=True)
    number_of_big_cattle_animals = models.CharField(max_length=255, null=True, blank=True)
    do_you_have_small_cattle_goat_sheep_pig = models.CharField(max_length=255, null=True, blank=True)
    number_of_small_cattle_animals = models.CharField(max_length=255, null=True, blank=True)
    do_you_have_poultry_chicken_and_duck = models.CharField(max_length=255, null=True, blank=True)
    number_of_poultry_animals = models.CharField(max_length=255, null=True, blank=True)
    approximate_income_earned_every_year_inr = models.CharField(max_length=255, null=True, blank=True)
    expense_on_education = models.CharField(max_length=255, null=True, blank=True)
    expense_on_health = models.CharField(max_length=255, null=True, blank=True)
    expense_on_food = models.CharField(max_length=255, null=True, blank=True)
    expense_on_tobacco_liquor = models.CharField(max_length=255, null=True, blank=True)
    expense_on_house_repair = models.CharField(max_length=255, null=True, blank=True)
    expense_on_festival_marriage_and_other_social_occassions = models.CharField(max_length=255, null=True, blank=True)
    amount_spent_for_agriculture_livestock = models.CharField(max_length=255, null=True, blank=True)
    loss_due_to_flood = models.CharField(max_length=255, null=True, blank=True)
    loan_availed = models.CharField(max_length=255, null=True, blank=True)
    loan_amount = models.CharField(max_length=255, null=True, blank=True)
    loan_purpose = models.CharField(max_length=255, null=True, blank=True)
    house_affected_by_flood = models.CharField(max_length=255, null=True, blank=True)
    economic_loss_to_your_house_due_to_flood = models.CharField(max_length=255, null=True, blank=True)
    amount_towards_flood_recovery_expenditure = models.CharField(max_length=255, null=True, blank=True)
    maximum_flood_height_in_house_ft = models.CharField(max_length=255, null=True, blank=True)
    year_in_which_maximum_flood_experience_in_your_house = models.CharField(max_length=255, null=True, blank=True)
    your_agriculture_affected_by_flood = models.CharField(max_length=255, null=True, blank=True)
    maximum_flood_height_experience_in_your_agriculture_ft = models.CharField(max_length=255, null=True, blank=True)
    year_in_which_max_flood_experience_in_your_agriculture_land = models.CharField(max_length=255, null=True, blank=True)
    duration_of_flood_stay_in_your_agriculture_field = models.CharField(max_length=255, null=True, blank=True)
    other_natural_hazards_directly_impacting_you_and_family = models.CharField(max_length=255, null=True, blank=True)
    house_vulnerable_to_erosion = models.CharField(max_length=255, null=True, blank=True)
    your_agriculture_field_vulnerable_to_erosion = models.CharField(max_length=255, null=True, blank=True)
    building_quality = models.CharField(max_length=255, null=True, blank=True)
    foundation_quality = models.CharField(max_length=255, null=True, blank=True)
    number_of_small_buildings_of_the_household = models.CharField(max_length=255, null=True, blank=True)
    occupa_ncy_type_of_small_building = models.CharField(max_length=255, null=True, blank=True)
    presence_of_grain_bank = models.CharField(max_length=255, null=True, blank=True)
    plinth_height_of_grain_bank_ft = models.CharField(max_length=255, null=True, blank=True)
    wall_material_of_grain_bank = models.CharField(max_length=255, null=True, blank=True)
    roof_material_of_grain_bank = models.CharField(max_length=255, null=True, blank=True)
    flood_depth_m = models.CharField(max_length=255, null=True, blank=True)
    flood_class = models.CharField(max_length=255, null=True, blank=True)
    erosion_class = models.CharField(max_length=255, null=True, blank=True)
    loan_class = models.CharField(max_length=255, null=True, blank=True)
    agrculture_land_class = models.CharField(max_length=255, null=True, blank=True)
    loan_class_1 = models.CharField(max_length=255, null=True, blank=True)
    fld_hh_class = models.CharField(max_length=255, null=True, blank=True)
    repair_class = models.CharField(max_length=255, null=True, blank=True)
    economic_loss_hh = models.CharField(max_length=255, null=True, blank=True)
    loss_agricultire_livlihood = models.CharField(max_length=255, null=True, blank=True)
    big_cattle = models.CharField(max_length=255, null=True, blank=True)
    small_cattle = models.CharField(max_length=255, null=True, blank=True)
    house_type = models.CharField(max_length=255, null=True, blank=True)
    income_class = models.CharField(max_length=255, null=True, blank=True)
    crops_diversity = models.CharField(max_length=255, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    Sanitation_Type=models.CharField(max_length=255, null=True, blank=True)
    unique_id=models.CharField(max_length=255, null=True, blank=True, unique=True)
    form_id=models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        return f"{self.village_code} - {self.point_id}"


class Commercial(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    district_code = models.CharField(max_length=255, null=True, blank=True)
    village_code = models.CharField(max_length=255, null=True, blank=True)
    district_name = models.CharField(max_length=255, null=True, blank=True)
    village_name = models.CharField(max_length=255, null=True, blank=True)
    point_id = models.CharField(max_length=255, null=True, blank=True)
    type_of_occupancy = models.CharField(max_length=255, null=True, blank=True)
    type_of_occupancy_others = models.CharField(max_length=255, null=True, blank=True)
    property_owner = models.CharField(max_length=255, null=True, blank=True)
    name_of_person = models.CharField(max_length=255, null=True, blank=True)
    photo = models.CharField(max_length=255, null=True, blank=True)
    name_of_the_building = models.CharField(max_length=255, null=True, blank=True)
    name_of_the_in_charge = models.CharField(max_length=255, null=True, blank=True)
    phone_number_of_the_in_charge = models.CharField(max_length=255, null=True, blank=True)
    wall_type = models.CharField(max_length=255, null=True, blank=True)
    floor_type = models.CharField(max_length=255, null=True, blank=True)
    roof_type = models.CharField(max_length=255, null=True, blank=True)
    plinth_above_ground = models.CharField(max_length=255, null=True, blank=True)
    plinth_above_ground_stilt_height_in_ft = models.CharField(max_length=255, null=True, blank=True)
    building_affected_by_normal_flood = models.CharField(max_length=255, null=True, blank=True)
    approximate_content_value_inr = models.CharField(max_length=255, null=True, blank=True)
    approximate_value_business_per_year = models.CharField(max_length=255, null=True, blank=True)
    average_room_width_ft = models.CharField(max_length=255, null=True, blank=True)
    average_room_length_ft = models.CharField(max_length=255, null=True, blank=True)
    building_quality = models.CharField(max_length=255, null=True, blank=True)
    foundation_quality = models.CharField(max_length=255, null=True, blank=True)
    access_road_during_flood = models.CharField(max_length=255, null=True, blank=True)
    flood_depth_m = models.CharField(max_length=255, null=True, blank=True)
    erosion_class = models.CharField(max_length=255, null=True, blank=True)
    unique_id=models.CharField(max_length=255, null=True, blank=True, unique=True)
    form_id=models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        return f"{self.district_code} - {self.village_name}"


class Transformer(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    village_name = models.CharField(max_length=255, null=True, blank=True)
    district_name = models.CharField(max_length=255, null=True, blank=True)
    district_code = models.CharField(max_length=255, null=True, blank=True)
    village_code = models.CharField(max_length=255, null=True, blank=True)
    transformer_site_address = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
    flood_depth_m = models.CharField(max_length=255, null=True, blank=True)
    flood_class = models.CharField(max_length=255, null=True, blank=True)
    erosion_class = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.district_code} - {self.village_name}"
    

class Critical_Facility(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    district_code = models.CharField(max_length=255, null=True, blank=True)
    district_name = models.CharField(max_length=255, null=True, blank=True)
    village_name = models.CharField(max_length=255, null=True, blank=True)
    village_code = models.CharField(max_length=255, null=True, blank=True)
    point_id = models.CharField(max_length=255, null=True, blank=True)
    occupancy_type = models.CharField(max_length=255, null=True, blank=True)
    photo = models.CharField(max_length=255, null=True, blank=True)
    name_of_building = models.CharField(max_length=255, null=True, blank=True)
    incharge_name = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=255, null=True, blank=True)
    wall_type = models.CharField(max_length=255, null=True, blank=True)
    floor_type = models.CharField(max_length=255, null=True, blank=True)
    roof_type = models.CharField(max_length=255, null=True, blank=True)
    plinth_or_stilt = models.CharField(max_length=255, null=True, blank=True)
    plinth_or_stilt_height_ft = models.CharField(max_length=255, null=True, blank=True)
    drinking_water_source = models.CharField(max_length=255, null=True, blank=True)
    house_has_electric_connection = models.CharField(max_length=255, null=True, blank=True)
    source_of_electricity = models.CharField(max_length=255, null=True, blank=True)
    number_of_rooms = models.CharField(max_length=255, null=True, blank=True)
    average_room_length_ft = models.CharField(max_length=255, null=True, blank=True)
    average_room_width_ft = models.CharField(max_length=255, null=True, blank=True)
    kitchen_facility = models.CharField(max_length=255, null=True, blank=True)
    toilet_facility = models.CharField(max_length=255, null=True, blank=True)
    number_of_toilets = models.CharField(max_length=255, null=True, blank=True)
    water_facility_in_toilet = models.CharField(max_length=255, null=True, blank=True)
    electricity_facility_in_toilet = models.CharField(max_length=255, null=True, blank=True)
    building_affected_by_normal_flood = models.CharField(max_length=255, null=True, blank=True)
    used_as_a_flood_emergency_shelter = models.CharField(max_length=255, null=True, blank=True)
    access_road_during_flood = models.CharField(max_length=255, null=True, blank=True)
    building_quality = models.CharField(max_length=255, null=True, blank=True)
    foundation_quality = models.CharField(max_length=255, null=True, blank=True)
    flood_depth_m = models.CharField(max_length=255, null=True, blank=True)
    flood_class = models.CharField(max_length=255, null=True, blank=True)
    erosion_class = models.CharField(max_length=255, null=True, blank=True)
    unique_id=models.CharField(max_length=255, null=True, blank=True, unique=True)
    form_id=models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        return f"{self.district_code} - {self.village_name}"


class ElectricPole(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    village_name =  models.CharField(max_length=255, null=True, blank=True)
    district_name =  models.CharField(max_length=255, null=True, blank=True)
    district_code =models.CharField(max_length=255, null=True, blank=True)
    village_code =models.CharField(max_length=255, null=True, blank=True)
    uid =models.CharField(max_length=255, null=True, blank=True)
    latitude =models.CharField(max_length=255, null=True, blank=True)
    longitude =models.CharField(max_length=255, null=True, blank=True)
    electric_pole_name =  models.CharField(max_length=255, null=True, blank=True)
    electric_pole_material =  models.CharField(max_length=255, null=True, blank=True)
    remarks_on_pole_condition =models.CharField(max_length=255, null=True, blank=True)
    photo =models.CharField(max_length=255, null=True, blank=True)
    flood_depth_m = models.CharField(max_length=255, null=True, blank=True)
    flood_class = models.CharField(max_length=100, blank=True, null=True)
    erosion_class = models.CharField(max_length=100, blank=True, null=True)
    unique_id=models.CharField(max_length=255, null=True, blank=True, unique=True)
    form_id=models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        return f"{self.electric_pole_name} - {self.village_name}"



class VillageListOfAllTheDistricts(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    district_name = models.CharField(max_length=100, blank=True, null=True)
    revenue_circle = models.CharField(max_length=100, blank=True, null=True)
    village_name = models.CharField(max_length=100, blank=True, null=True)
    district_code = models.CharField(max_length=20, blank=True, null=True)
    village_code = models.CharField(max_length=20, blank=True, null=True)
    circle_name = models.CharField(max_length=100, blank=True, null=True)
    block_name = models.CharField(max_length=100, blank=True, null=True)
    distance_from_headquarter = models.FloatField(blank=True, null=True, help_text="Distance in kilometers")
    total_area = models.FloatField(blank=True, null=True, help_text="Total area in square kilometers")
    average_elevation = models.FloatField(blank=True, null=True, help_text="Elevation in meters")
    topography = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.village_name} ({self.district_name})"

# This model is for rood affected by flood
class VillageRoadInfo(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    district_name = models.CharField(max_length=100)
    district_code = models.CharField(max_length=20)
    village_name = models.CharField(max_length=100)
    village_code = models.CharField(max_length=20) 
    road_surface_type = models.CharField(max_length=100)
    road_constructed_by = models.CharField(max_length=100)
    road_length_m = models.FloatField()
    flood_depth_m = models.FloatField(null=True, blank=True)
    flood_class = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.village_name} ({self.road_surface_type})"
    
# This model is for road affected by erosion
class VillageRoadInfoErosion(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    district_name = models.CharField(max_length=100)
    district_code = models.CharField(max_length=20)
    village_name = models.CharField(max_length=100)
    village_code = models.CharField(max_length=20)
    road_surface_type = models.CharField(max_length=100)
    road_constructed_by = models.CharField(max_length=100)
    road_length_m = models.FloatField()
    erosion_class = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.village_name} ({self.road_surface_type})"
    
    
    
class VDMP_Maps_Data(models.Model):
    village = models.OneToOneField(tblVillage, on_delete=models.CASCADE)
    distribution_of_building = models.FileField(upload_to="maps/distribution_of_building/", max_length=255, null=True, blank=True)
    road_infrastructure = models.FileField(upload_to="maps/road_infrastructure/", max_length=255, null=True, blank=True)
    landuse = models.FileField(upload_to="maps/landuse/", max_length=255, null=True, blank=True)
    flood_erosion = models.FileField(upload_to="maps/flood_erosion/", max_length=255, null=True, blank=True)
    wind_hazard = models.FileField(upload_to="maps/wind_hazard/", max_length=255, null=True, blank=True)
    earthquake_hazard = models.FileField(upload_to="maps/earthquake_hazard/", max_length=255, null=True, blank=True)
    essential_facilities = models.FileField(upload_to="maps/essential_facilities/", max_length=255, null=True, blank=True)
    electrical_infrastructure = models.FileField(upload_to="maps/electrical_infrastructure/", max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.village.name} Maps Data"



class BridgeSurvey(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    username = models.CharField(max_length=255, blank=True, null=True)
    spatial_id = models.CharField(max_length=255, blank=True, null=True)
    spatial_ref = models.CharField(max_length=255, blank=True, null=True)
    polygon_id = models.CharField(max_length=255, blank=True, null=True)
    village_code = models.CharField(max_length=255, blank=True, null=True)
    village_name = models.CharField(max_length=255, blank=True, null=True)
    district_name = models.CharField(max_length=255, blank=True, null=True)
    survey_id = models.CharField(max_length=255, blank=True, null=True)
    geometry = models.CharField(max_length=255, blank=True, null=True)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    under_id = models.CharField(max_length=255, blank=True, null=True)
    district_code = models.CharField(max_length=255, null=True, blank=True)
    point_id = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255, blank=True, null=True)
    form_id = models.CharField(max_length=255, blank=True, null=True)
    tab_id = models.CharField(max_length=255, blank=True, null=True)
    tab_name = models.CharField(max_length=255, blank=True, null=True)

    bridge_surface_type = models.CharField(max_length=255, blank=True, null=True)
    length_meters = models.CharField(max_length=255, blank=True, null=True)
    width_meters = models.CharField(max_length=255, blank=True, null=True)
    photographs = models.CharField(max_length=255, blank=True, null=True)
    bridge_pillar_material = models.CharField(max_length=255, blank=True, null=True)
    number_of_pillars = models.CharField(max_length=255, blank=True, null=True)
    deck_material = models.CharField(max_length=255, blank=True, null=True)
    condition_of_deck = models.CharField(max_length=255, blank=True, null=True)
    general_condition = models.CharField(max_length=255, blank=True, null=True)
    status_access_part = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    unique_id=models.CharField(max_length=255, null=True, blank=True, unique=True)
    form_id=models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        return f"{self.village_name} - {self.unique_id}"
    


class Risk_Assesment(models.Model):
    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE)
    village_name = models.CharField(max_length=255,blank=True, null=True)
    village_code = models.CharField(max_length=100,blank=True, null=True)
    hazard = models.CharField(max_length=100,blank=True, null=True)
    exposure_type = models.CharField(max_length=100,blank=True, null=True)
    total_exposure_value_inr_crore = models.CharField(max_length=100,blank=True, null=True)
    loss_inr_crore = models.CharField(max_length=100,blank=True, null=True)
    loss_percent_wrt_exposure_value = models.CharField(max_length=100,blank=True, null=True)

    def __str__(self):
        return f"{self.village_name} - {self.hazard}"


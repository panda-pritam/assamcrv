import os
import pandas as pd
import psycopg2
from django.db import connections
from django.conf import settings
from village_profile.models import district_village_mapping
from vdmp_dashboard.models import HouseholdSurvey
from .models import tblVDMP_Activity_Import_Status
from datetime import datetime, timedelta
import subprocess
import tempfile
import re
import logging
from .cleaning_utils import clean_survey_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_household_survey_data(activity_name, village_id, district_id, mobile_village_id, district_code, village_code, activity_status):
    """
    Process household survey data pipeline:
    1. Extract data from mobile_db
    2. Apply comprehensive data cleaning
    3. Save to HouseholdSurvey model
    """
    (f"Starting {activity_name} data processing for village_id: {village_id}")
    start_time = datetime.now()
    
    # Create import status record
    import_status = tblVDMP_Activity_Import_Status.objects.create(
        activity=activity_status.activity,
        activity_status=activity_status,
        rows_imported=0,
        error_count=0
    )
    
    # Validate input parameters
    if not mobile_village_id:
        import_status.error_count = 1
        import_status.processing_time = datetime.now() - start_time
        import_status.save()
        logger.error(f"Mobile village ID not found for village_id: {village_id}")
        raise Exception(f"Mobile village ID not found for village_id: {village_id}")
    
    (f"Using mobile_village_id: {mobile_village_id}, district_code: {district_code}")
    
    # Connect to mobile_db and extract data
    mobile_db_config = settings.DATABASES['mobile_db']
    (f"Connecting to mobile_db at {mobile_db_config['HOST']}")
    
    try:
        with psycopg2.connect(
            host=mobile_db_config['HOST'],
            port=mobile_db_config['PORT'],
            database=mobile_db_config['NAME'],
            user=mobile_db_config['USER'],
            password=mobile_db_config['PASSWORD']
        ) as conn:
            
            # Get SQL script and parameters
            sql_script, params = get_household_sql_script(mobile_village_id)
            (f"Executing SQL query with village_id parameter: {mobile_village_id}")
            
            # Execute query and get data
            df = pd.read_sql(sql_script, conn, params=params)
            (f"Extracted {len(df)} records from mobile_db")
            
            # Check if data exists
            if len(df) == 0:
                logger.error(f"No data found in mobile_db for village_id: {mobile_village_id}")
                raise Exception(f"No household survey data found for village_id: {mobile_village_id}. Please ensure data collection is completed.")
    
    except Exception as e:
        import_status.error_count = 1
        import_status.processing_time = datetime.now() - start_time
        import_status.save()
        logger.error(f"Database connection/query failed: {str(e)}")
        raise
    
    # Apply comprehensive data cleaning
    print("Starting data cleaning process")
    cleaned_df = clean_survey_data(df, district_code, village_code, activity_type="household")
    
    # Save CSV for verification in static directory
    static_dir = os.path.join(settings.BASE_DIR, 'static', 'csv_exports')
    os.makedirs(static_dir, exist_ok=True)
    csv_path = os.path.join(static_dir, f"household_survey_village_{village_id}.csv")
    cleaned_df.to_csv(csv_path, index=False)
    print(f"CSV saved for verification: {csv_path}")
    
    # Save to Django model
    ("Saving cleaned data to HouseholdSurvey model")
    records_saved = save_to_household_survey(cleaned_df, village_id, district_code)
    
    # Update import status with final results
    import_status.rows_imported = records_saved
    import_status.processing_time = datetime.now() - start_time
    import_status.save()
    
    (f"Pipeline completed successfully. Processed {records_saved} records")
    return import_status, records_saved

def get_household_sql_script(village_id):
    """Get the household SQL script with village_id parameter"""
    ("--------------- Running the SQL script ---------------")
    sql_script = """
    WITH media_urls AS (
        SELECT
            fd.spatial_id,
            fd.attribute_id,
            STRING_AGG(fd.media_id::text, ',' ORDER BY fd.media_id) AS media_ids_str
        FROM public.formdata fd
        JOIN public.attributes att
            ON fd.attribute_id = att.id
        WHERE att.widget_id = 10
          AND att.tab_id = 1
          AND fd.media_id IS NOT NULL
        GROUP BY fd.spatial_id, fd.attribute_id
    ),
    attribute_values AS (
        SELECT
            fd.form_id,
            fd.spatial_id,
            fd.attribute_id,
            CASE
                WHEN att.widget_id IN (2,4) THEN
                    STRING_AGG(DISTINCT ao.option_text, ', ' ORDER BY ao.option_text)
                WHEN att.widget_id = 10 THEN
                    'https://jkiofs.in/fastapi/PincerApps/images/test'
                    || COALESCE(mu.media_ids_str,'')
                    || '/' || fd.spatial_id
                ELSE MAX(fd.attribute_value)
            END AS value
        FROM public.formdata fd
        JOIN public.attributes att
            ON att.id = fd.attribute_id
        LEFT JOIN public.attributes_option ao
            ON ao.attribute_id = fd.attribute_id
           AND att.widget_id IN (2,4)
           AND ao.option_id = ANY (
                string_to_array(
                    regexp_replace(fd.attribute_value, '[^0-9,]', '', 'g'),
                    ','
                )::INT[]
           )
        LEFT JOIN media_urls mu
            ON mu.spatial_id = fd.spatial_id
           AND mu.attribute_id = fd.attribute_id
        WHERE att.tab_id = 1
          AND fd.spatial_id IN (
              SELECT id FROM public.spatialdata WHERE village_id = %s
          )
        GROUP BY
            fd.form_id,
            fd.spatial_id,
            fd.attribute_id,
            att.widget_id,
            mu.media_ids_str
    )
    SELECT
        s.survey_id,
        s.spatial_id,
        v.district_name,
        v.village_name,
        SPLIT_PART(s.geometry, ' ', 1) AS latitude,
        SPLIT_PART(s.geometry, ' ', 2) AS longitude,
        s.polygon_id,
        s.unique_id,
        MIN(f.form_id) AS form_id,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Name of the head of household%%' THEN av.value END) AS name_of_hohh,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Property ownership%%' THEN av.value END) AS property_owner,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Name of person%%' THEN av.value END) AS name_of_person,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Photo with coordinates%%' THEN av.value END) AS photo,
        MAX(CASE WHEN a.attribute_name ILIKE '%%phone number%%' THEN av.value END) AS mobile_number,
        MAX(CASE WHEN a.attribute_name ILIKE '%%data access in phone%%' THEN av.value END) AS data_access,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Community%%' THEN av.value END) AS community,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Social status%%' THEN av.value END) AS social_status,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Economic status%%' THEN av.value END) AS economic_status,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Wall type%%' THEN av.value END) AS wall_type,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Roof type%%' THEN av.value END) AS roof_type,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Floor type%%' THEN av.value END) AS floor_type,
        MAX(CASE WHEN a.id = 123 THEN av.value END) AS plinth_or_stilt,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Plinth above ground or Stilt height%%' THEN av.value END) AS plinth_or_stilt_height_ft,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of storeys%%' THEN av.value END) AS number_of_storeys,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of males%%' THEN av.value END) AS number_of_males_including_children,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of females%%' THEN av.value END) AS number_of_females_including_children,
        MAX(CASE WHEN a.attribute_name ILIKE '%%children age < 6%%' THEN av.value END) AS children_below_6_years,
        MAX(CASE WHEN a.attribute_name ILIKE '%%age > 60%%' THEN av.value END) AS senior_citizens,
        MAX(CASE WHEN a.attribute_name ILIKE '%%pregnant women%%' THEN av.value END) AS pregnant_women,
        MAX(CASE WHEN a.attribute_name ILIKE '%%lactating women%%' THEN av.value END) AS lactating_women,
        MAX(CASE WHEN a.attribute_name ILIKE '%%permanently disabled%%' THEN av.value END) AS persons_with_disability_or_chronic_disease,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Drinking water source%%' THEN av.value END) AS drinking_water_source,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Sanitation facility%%' THEN av.value END) AS sanitation_facility,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Toilet wall material%%' THEN av.value END) AS toilet_wall_material,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Toilet roof material%%' THEN av.value END) AS toilet_roof_material,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Digital media owned%%' THEN av.value END) AS digital_media_owned,
        MAX(CASE WHEN a.attribute_name ILIKE '%%electric connection%%' THEN av.value END) AS house_has_electric_connection,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Source of electricity%%' THEN av.value END) AS source_of_electricity,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Own agriculture land%%' THEN av.value END) AS own_agriculture_land,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Area of agriculture land owned%%' THEN av.value END) AS area_of_agriculture_land_owned_bigha,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Land.*annually cultivated%%' THEN av.value END) AS land_area_annually_cultivated_bigha,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Crops cultivated%%' THEN av.value END) AS crops_cultivated,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Specify other%%' THEN av.value END) AS specify_other,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of crops normally raised%%' THEN av.value END) AS number_of_crops_normally_raised_every_year,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Livelihood primary%%' THEN av.value END) AS livelihood_primary,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Livelihood secondary%%' THEN av.value END) AS livelihood_secondary,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Big cattle%%' THEN av.value END) AS do_you_have_big_cattle_cattle_buffalo,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of big cattle%%' THEN av.value END) AS number_of_big_cattle_animals,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Small cattle%%' THEN av.value END) AS do_you_have_small_cattle_goat_sheep_pig,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of small cattle%%' THEN av.value END) AS number_of_small_cattle_animals,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Poultry%%' THEN av.value END) AS do_you_have_poultry_chicken_and_duck,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of poultry%%' THEN av.value END) AS number_of_poultry_animals,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Approximate income earned every year%%' THEN av.value END) AS approximate_income_earned_every_year_inr,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Education.*children%%' THEN av.value END) AS expense_on_education,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Health related%%' THEN av.value END) AS expense_on_health,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Food including%%' THEN av.value END) AS expense_on_food,
        MAX(CASE WHEN a.attribute_name ILIKE '%%tobacco.*liquor%%' THEN av.value END) AS expense_on_tobacco_liquor,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Repair of house%%' THEN av.value END) AS expense_on_house_repair,
        MAX(CASE WHEN a.attribute_name ILIKE '%%festival.*marriage%%' THEN av.value END) AS expense_on_festival_marriage_and_other_social_occassions,
        MAX(CASE WHEN a.attribute_name ILIKE '%%agriculture.*livestock%%' THEN av.value END) AS amount_spent_for_agriculture_livestock,
        MAX(CASE WHEN a.attribute_name ILIKE '%%loss.*flood%%' THEN av.value END) AS loss_due_to_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%avail loan%%' THEN av.value END) AS loan_availed,
        MAX(CASE WHEN a.attribute_name ILIKE '%%loan amount%%' THEN av.value END) AS loan_amount,
        MAX(CASE WHEN a.attribute_name ILIKE '%%loan.*purpose%%' THEN av.value END) AS loan_purpose,
        MAX(CASE WHEN a.attribute_name ILIKE '%%house affected by flood%%' THEN av.value END) AS house_affected_by_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%economic loss.*house.*flood%%' THEN av.value END) AS economic_loss_to_your_house_due_to_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%flood recovery expenditure%%' THEN av.value END) AS amount_towards_flood_recovery_expenditure,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Maximum flood height.*house%%' THEN av.value END) AS maximum_flood_height_in_house_ft,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Year.*maximum flood.*house%%' THEN av.value END) AS year_in_which_maximum_flood_experience_in_your_house,
        MAX(CASE WHEN a.attribute_name ILIKE '%%agriculture affected by flood%%' THEN av.value END) AS your_agriculture_affected_by_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%flood height.*agriculture%%' THEN av.value END) AS maximum_flood_height_experience_in_your_agriculture_ft,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Year.*flood.*agriculture%%' THEN av.value END) AS year_in_which_max_flood_experience_in_your_agriculture_land,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Duration of flood%%' THEN av.value END) AS duration_of_flood_stay_in_your_agriculture_field,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Other natural hazards%%' THEN av.value END) AS other_natural_hazards_directly_impacting_you_and_family,
        MAX(CASE WHEN a.attribute_name ILIKE '%%House vulnerable to erosion%%' THEN av.value END) AS house_vulnerable_to_erosion,
        MAX(CASE WHEN a.attribute_name ILIKE '%%agriculture.*vulnerable to erosion%%' THEN av.value END) AS your_agriculture_field_vulnerable_to_erosion,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Building quality%%' THEN av.value END) AS building_quality,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Foundation quality%%' THEN av.value END) AS foundation_quality,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of small buildings%%' THEN av.value END) AS number_of_small_buildings_of_the_household,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Occupancy type of small building%%' THEN av.value END) AS occupa_ncy_type_of_small_building,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Presence of grain bank%%' THEN av.value END) AS presence_of_grain_bank,
        MAX(CASE WHEN a.attribute_name ILIKE '%%plinth height of grain bank%%' THEN av.value END) AS plinth_height_of_grain_bank_ft,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Wall material of grain bank%%' THEN av.value END) AS wall_material_of_grain_bank,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Roof material of grain bank%%' THEN av.value END) AS roof_material_of_grain_bank,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Approximate length%%' THEN av.value END) AS approximate_length_feet_of_the_house_main_building,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Approximate width%%' THEN av.value END) AS approximate_width_feet_of_the_house_main_building,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Fuel used in kitchen%%' THEN av.value END) AS fuel_used_in_kitchen,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Flood depth experienced%%' THEN av.value END) AS flood_depth_experienced_at_your_home_during_normal_flood_feet,
        MAX(CASE WHEN a.attribute_name ILIKE '%%adequate water from this source%%' THEN av.value END) AS adequate_water_from_this_source,
        MAX(CASE WHEN a.attribute_name ILIKE '%%water quality of source good all seasons%%' THEN av.value END) AS water_quality_of_source_good_all_seasons,
        MAX(CASE WHEN a.attribute_name ILIKE '%%JJM or other taped water connection%%' THEN av.value END) AS jjm_or_other_taped_water_connection,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Do you get adequate water in this connection%%' THEN av.value END) AS do_you_get_adequate_water_in_this_connection,
        MAX(CASE WHEN a.attribute_name ILIKE '%%pay monthly charges for this connection%%' THEN av.value END) AS pay_monthly_charges_for_this_connection,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Toilet constructed under any support program%%' THEN av.value END) AS toilet_constructed_under_any_support_program,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Toilet constructed year%%' THEN av.value END) AS toilet_constructed_year,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Type of toilet%%' THEN av.value END) AS type_of_toilet,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Whether wastewater of toilet flow to the open%%' THEN av.value END) AS whether_wastewater_of_toilet_flow_to_the_open,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Periodically de-sludged%%' THEN av.value END) AS periodically_de_sludged,
        MAX(CASE WHEN a.attribute_name ILIKE '%%While de-sludging where the sludge be disposed%%' THEN av.value END) AS while_de_sludging_where_the_sludge_be_disposed,
        COALESCE(MAX(CASE WHEN a.id = 185 THEN NULLIF(av.value, '')::int END), 0) AS amount_spent_for_festival_marriage_and_other_social_functions_per_year,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of big livestock died in last flood%%' THEN av.value END) AS number_of_big_livestock_died_in_last_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%No of big cattle died in most severe flood%%' THEN av.value END) AS no_of_big_cattle_died_in_most_severe_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of small livestock died in last flood%%' THEN av.value END) AS number_of_small_livestock_died_in_last_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%No of small cattle died in most severe flood%%' THEN av.value END) AS no_of_small_cattle_died_in_most_severe_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Number of poultry died in last flood%%' THEN av.value END) AS number_of_poultry_died_in_last_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%No of poultry died in most severe flood%%' THEN av.value END) AS no_of_poultry_died_in_most_severe_flood,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Approximate loss incurred to your livelihood%%' THEN av.value END) AS approximate_loss_incurred_to_your_livelihood_due_to_flood_every_year,
        MAX(CASE WHEN a.attribute_name ILIKE '%%Asset Type%%' THEN av.value END) AS asset_type
    FROM public.formdata f
    JOIN attribute_values av
        ON av.spatial_id = f.spatial_id
       AND av.attribute_id = f.attribute_id
    JOIN public.attributes a
        ON a.id = f.attribute_id
    JOIN public.spatialdata s
        ON s.id = f.spatial_id
    JOIN public.users u
        ON u.id = s.user_id
    JOIN public.villages v
        ON v.id = s.village_id
    WHERE a.tab_id = 1
      AND v.id = %s
    GROUP BY
        s.survey_id, s.spatial_id, v.district_name, v.village_name,
        s.geometry, s.polygon_id, s.unique_id
    ORDER BY s.survey_id
    """
    
    return sql_script, (village_id, village_id)

# This function is now replaced by the common cleaning utility
# Use clean_survey_data from cleaning_utils.py instead

def save_to_household_survey(df, village_id, district_code):
    """Save cleaned data to HouseholdSurvey model"""

    ("--------------- Saving Data to DB  ---------------")
    (f"Saving {len(df)} records to HouseholdSurvey model")
    
    # Clear existing data for this village
    existing_count = HouseholdSurvey.objects.filter(village_id=village_id).count()
    if existing_count > 0:
        (f"Deleting {existing_count} existing records for village_id: {village_id}")
        HouseholdSurvey.objects.filter(village_id=village_id).delete()
    
    # Create new records
    records = []
    print("Creating HouseholdSurvey records from cleaned data")
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:  # Log progress every 100 records
            print(f"Processing record {idx + 1}/{len(df)}")
        record = HouseholdSurvey(
            village_id=village_id,
            dist_code=row.get('dist_code', district_code),
            village_code=row.get('village_code', ''),
            point_id=row.get('polygon_id', ''),
            property_owner=row.get('property_owner', ''),
            name_of_person=row.get('name_of_person', ''),
            name_of_hohh=row.get('name_of_hohh', ''),
            photo=row.get('photo', ''),
            mobile_number=row.get('mobile_number', ''),
            data_access=row.get('data_access', ''),
            community=row.get('community', ''),
            social_status=row.get('social_status', ''),
            economic_status=row.get('economic_status', ''),
            wall_type=row.get('wall_type', ''),
            roof_type=row.get('roof_type', ''),
            floor_type=row.get('floor_type', ''),
            plinth_or_stilt=row.get('plinth_or_stilt', ''),
            plinth_or_stilt_height_ft=str(row.get('plinth_or_stilt_height_ft', '')),
            number_of_storeys=str(row.get('number_of_storeys', '')),
            number_of_males_including_children=str(row.get('number_of_males_including_children', '')),
            number_of_females_including_children=str(row.get('number_of_females_including_children', '')),
            children_below_6_years=str(row.get('children_below_6_years', '')),
            senior_citizens=str(row.get('senior_citizens', '')),
            pregnant_women=str(row.get('pregnant_women', '')),
            lactating_women=str(row.get('lactating_women', '')),
            persons_with_disability_or_chronic_disease=str(row.get('persons_with_disability_or_chronic_disease', '')),
            drinking_water_source=row.get('drinking_water_source', ''),
            sanitation_facility=row.get('sanitation_facility', ''),
            toilet_wall_material=row.get('toilet_wall_material', ''),
            toilet_roof_material=row.get('toilet_roof_material', ''),
            digital_media_owned=row.get('digital_media_owned', ''),
            house_has_electric_connection=row.get('house_has_electric_connection', ''),
            source_of_electricity=row.get('source_of_electricity', ''),
            own_agriculture_land=row.get('own_agriculture_land', ''),
            area_of_agriculture_land_owned_bigha=str(row.get('area_of_agriculture_land_owned_bigha', '')),
            land_area_annually_cultivated_bigha=str(row.get('land_area_annually_cultivated_bigha', '')),
            crops_cultivated=row.get('crops_cultivated', ''),
            specify_other=row.get('specify_other', ''),
            number_of_crops_normally_raised_every_year=str(row.get('number_of_crops_normally_raised_every_year', '')),
            livelihood_primary=row.get('livelihood_primary', ''),
            livelihood_secondary=row.get('livelihood_secondary', ''),
            do_you_have_big_cattle_cattle_buffalo=row.get('do_you_have_big_cattle_cattle_buffalo', ''),
            number_of_big_cattle_animals=str(row.get('number_of_big_cattle_animals', '')),
            do_you_have_small_cattle_goat_sheep_pig=row.get('do_you_have_small_cattle_goat_sheep_pig', ''),
            number_of_small_cattle_animals=str(row.get('number_of_small_cattle_animals', '')),
            do_you_have_poultry_chicken_and_duck=row.get('do_you_have_poultry_chicken_and_duck', ''),
            number_of_poultry_animals=str(row.get('number_of_poultry_animals', '')),
            approximate_income_earned_every_year_inr=str(row.get('approximate_income_earned_every_year_inr', '')),
            expense_on_education=str(row.get('expense_on_education', '')),
            expense_on_health=str(row.get('expense_on_health', '')),
            expense_on_food=str(row.get('expense_on_food', '')),
            expense_on_tobacco_liquor=str(row.get('expense_on_tobacco_liquor', '')),
            expense_on_house_repair=str(row.get('expense_on_house_repair', '')),
            expense_on_festival_marriage_and_other_social_occassions=str(row.get('amount_spent_for_festival_marriage_and_other_social_functions_per_year', row.get('expense_on_festival_marriage_and_other_social_occassions', ''))),
            amount_spent_for_agriculture_livestock=str(row.get('amount_spent_for_agriculture_livestock', '')),
            loss_due_to_flood=row.get('loss_due_to_flood', ''),
            loan_availed=row.get('loan_availed', ''),
            loan_amount=str(row.get('loan_amount', '')),
            loan_purpose=row.get('loan_purpose', ''),
            house_affected_by_flood=row.get('house_affected_by_flood', ''),
            economic_loss_to_your_house_due_to_flood=str(row.get('economic_loss_to_your_house_due_to_flood', '')),
            amount_towards_flood_recovery_expenditure=str(row.get('amount_towards_flood_recovery_expenditure', '')),
            maximum_flood_height_in_house_ft=str(row.get('maximum_flood_height_in_house_ft', '')),
            year_in_which_maximum_flood_experience_in_your_house=str(row.get('year_in_which_maximum_flood_experience_in_your_house', '')),
            your_agriculture_affected_by_flood=row.get('your_agriculture_affected_by_flood', ''),
            maximum_flood_height_experience_in_your_agriculture_ft=str(row.get('maximum_flood_height_experience_in_your_agriculture_ft', '')),
            year_in_which_max_flood_experience_in_your_agriculture_land=str(row.get('year_in_which_max_flood_experience_in_your_agriculture_land', '')),
            duration_of_flood_stay_in_your_agriculture_field=row.get('duration_of_flood_stay_in_your_agriculture_field', ''),
            other_natural_hazards_directly_impacting_you_and_family=row.get('other_natural_hazards_directly_impacting_you_and_family', ''),
            house_vulnerable_to_erosion=row.get('house_vulnerable_to_erosion', ''),
            your_agriculture_field_vulnerable_to_erosion=row.get('your_agriculture_field_vulnerable_to_erosion', ''),
            building_quality=row.get('building_quality', ''),
            foundation_quality=row.get('foundation_quality', ''),
            number_of_small_buildings_of_the_household=str(row.get('number_of_small_buildings_of_the_household', '')),
            occupa_ncy_type_of_small_building=row.get('occupa_ncy_type_of_small_building', ''),
            presence_of_grain_bank=row.get('presence_of_grain_bank', ''),
            plinth_height_of_grain_bank_ft=str(row.get('plinth_height_of_grain_bank_ft', '')),
            wall_material_of_grain_bank=row.get('wall_material_of_grain_bank', ''),
            roof_material_of_grain_bank=row.get('roof_material_of_grain_bank', ''),
            unique_id=row.get('unique_id', ''),
            form_id=str(row.get('form_id', ''))
        )
        records.append(record)
    
    # Bulk create with logging
    (f"Bulk creating {len(records)} HouseholdSurvey records")
    try:
        HouseholdSurvey.objects.bulk_create(records, batch_size=1000)
        (f"Successfully saved {len(records)} records to database")
    except Exception as e:
        logger.error(f"Failed to save records to database: {str(e)}")
        raise
    
    return len(records)
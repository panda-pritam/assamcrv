
from django.http import HttpResponseForbidden
from accounts.models import tblUser

from django.utils.translation import get_language

def translated(obj, base_field):
    lang = get_language()
    return getattr(obj, f"{base_field}_{lang}", None) or getattr(obj, base_field, None)


def is_admin_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.role.name == "ASDMA")

def apply_location_filters(queryset, district_id=None, circle_id=None, gram_panchayat_id=None, village_id=None):
    if district_id:
        queryset = queryset.filter(village__gram_panchayat__circle__district_id=district_id)
    if circle_id:
        queryset = queryset.filter(village__gram_panchayat__circle_id=circle_id)
    if gram_panchayat_id:
        queryset = queryset.filter(village__gram_panchayat_id=gram_panchayat_id)
    if village_id:
        queryset = queryset.filter(village_id=village_id)
    return queryset

def village_apply_location_filters(queryset, district_id=None, circle_id=None, gram_panchayat_id=None, village_id=None):

    if district_id:
        queryset = queryset.filter(gram_panchayat__circle__district_id= district_id)
    if circle_id:
        queryset = queryset.filter(gram_panchayat__circle_id= circle_id)
    if gram_panchayat_id:
        queryset = queryset.filter(gram_panchayat_id= gram_panchayat_id)
    if village_id:        
        queryset = queryset.filter(id=village_id)
    return queryset


def apply_role_filters(user, role, queryset):
    if user.is_superuser or role == "ASDMA":
        return queryset
    elif role == "DDMA":
        return queryset.filter(village__gram_panchayat__circle__district=user.district)
    elif role == "Circle Officer":
        return queryset.filter(village__gram_panchayat__circle=user.circle)
    elif role == "Gram Panchayat Officer":
        return queryset.filter(village__gram_panchayat=user.gram_panchayat)
    elif role == "Village Officer":
        return queryset.filter(village=user.village)
    else:
        return queryset.none()

from typing import List, Optional

def get_village_codes(
    district_id: Optional[int] = None, 
    circle_id: Optional[int] = None, 
    gram_panchayat_id: Optional[int] = None, 
    village_id: Optional[int] = None
) -> List[str]:
    """
    Returns village codes based on the hierarchy:
    district > circle > gram_panchayat > village
    """
   

    if village_id:
        villages = tblVillage.objects.filter(id=village_id)
    elif gram_panchayat_id:
        villages = tblVillage.objects.filter(gram_panchayat_id=gram_panchayat_id)
    elif circle_id:
        villages = tblVillage.objects.filter(gram_panchayat__circle_id=circle_id)
    elif district_id:
        villages = tblVillage.objects.filter(gram_panchayat__circle__district_id=district_id)
    else:
        villages = tblVillage.objects.all()  

    return list(villages.values_list('code', flat=True))



def get_filtered_users(user, district_id=None, circle_id=None, gram_panchayat_id=None, village_id=None, role_id=None, department_id=None):
    """
    Returns filtered users based on the user's role and optional filter parameters.
    Used to retrieve users accessible to the current user with hierarchical role checks.
    """
    users = tblUser.objects.none()  # Default empty queryset

    if user.is_authenticated:
        role = getattr(user.role, 'name', None)
        if user.is_superuser or role == "ASDMA":
            users = tblUser.objects.all()
        elif role == "DDMA":
            users = tblUser.objects.filter(district_id=user.district_id)
        elif role == "Circle Officer":
            users = tblUser.objects.filter(circle_id=user.circle_id)
        elif role == "Gram Panchayat Officer":
            users = tblUser.objects.filter(gram_panchayat_id=user.gram_panchayat_id)
        elif role == "Village Officer":
            users = tblUser.objects.filter(village_id=user.village_id)

    if district_id:
        users = users.filter(district_id=district_id)
    if circle_id:
        users = users.filter(circle_id=circle_id)
    if gram_panchayat_id:
        users = users.filter(gram_panchayat_id=gram_panchayat_id)
    if village_id:
        users = users.filter(village_id=village_id)
    if role_id:
        users = users.filter(role_id=role_id)
    if department_id:
        users = users.filter(department_id=department_id)

    return users


import csv
import os
import tempfile
from django.db import transaction
from googletrans import Translator
from accounts.models import tblDistrict, tblCircle, tblGramPanchayat, tblVillage

from openpyxl import load_workbook
import logging

# Set up logging
logger = logging.getLogger(__name__)

translator = Translator()

def translate_name(name, lang_code):
    """Translate name to given language code with error handling"""
    # Temporarily disable translation due to coroutine issues
    # Return original name as fallback
    return name.strip() if name else name

def clean_cell_value(cell_value):
    """Clean and convert cell value to string"""
    if cell_value is None:
        return ""
    if isinstance(cell_value, (int, float)):
        # Convert numbers to string, handle floats properly
        if isinstance(cell_value, float) and cell_value.is_integer():
            return str(int(cell_value))
        return str(cell_value)
    return str(cell_value).strip()


def read_csv_file(file_path):
    """Read CSV file with multiple encoding attempts"""
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                # Test if we can read the file
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                # Create CSV reader
                reader = csv.DictReader(csvfile)
                rows = []
                
                # Read all rows
                for row_num, row in enumerate(reader, start=1):
                    if not any(value.strip() for value in row.values() if value):
                        continue  # Skip empty rows
                    
                    # Clean row data
                    cleaned_row = {}
                    for key, value in row.items():
                        cleaned_row[key] = clean_cell_value(value)
                    
                    rows.append(cleaned_row)
                
                logger.info(f"Successfully read {len(rows)} rows from CSV file using {encoding} encoding")
                return rows
                
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Error reading CSV with {encoding}: {e}")
            continue
    
    raise ValueError(f"Could not decode CSV file with any of the supported encodings: {encodings}")

def convert_excel_to_csv(excel_path, csv_path):
    """Convert Excel file to CSV format for reliable processing"""
    try:
        logger.info(f"Converting Excel file {excel_path} to CSV format...")
        
        # Load the workbook
        workbook = load_workbook(excel_path, data_only=True, read_only=True)
        
        # Get the active sheet
        if workbook.sheetnames:
            sheet = workbook.active
            logger.info(f"Using sheet: {sheet.title}")
        else:
            raise ValueError("Excel file has no sheets")
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            row_count = 0
            for row in sheet.iter_rows(values_only=True):
                # Skip completely empty rows
                if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                    continue
                
                # Clean and convert row data
                cleaned_row = []
                for cell in row:
                    cleaned_value = clean_cell_value(cell)
                    cleaned_row.append(cleaned_value)
                
                csv_writer.writerow(cleaned_row)
                row_count += 1
        
        workbook.close()
        logger.info(f"Successfully converted Excel to CSV: {row_count} rows written")
        return True
        
    except Exception as e:
        logger.error(f"Error converting Excel to CSV: {e}")
        raise ValueError(f"Error converting Excel to CSV: {str(e)}")

def import_location_data(file_path, update_existing=True):
    """Import location data from CSV or Excel file"""
    
    # Validate file exists
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    # Get file extension
    _, ext = os.path.splitext(file_path.lower())
    
    # Convert Excel files to CSV first for more reliable processing
    csv_file_path = file_path
    temp_csv_path = None
    
    try:
        if ext in ['.xlsx', '.xls']:
            logger.info(f"Excel file detected. Converting to CSV for processing...")
            
            # Create temporary CSV file
            temp_csv_fd, temp_csv_path = tempfile.mkstemp(suffix='.csv', prefix='converted_')
            os.close(temp_csv_fd)  # Close the file descriptor, we'll use the path
            
            # Convert Excel to CSV
            convert_excel_to_csv(file_path, temp_csv_path)
            csv_file_path = temp_csv_path
            
        elif ext == '.csv':
            logger.info("CSV file detected. Processing directly...")
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Only .csv, .xlsx, and .xls files are supported.")
        
        # Now read the CSV file (either original or converted)
        rows = read_csv_file(csv_file_path)
        
        if not rows:
            raise ValueError("No data rows found in the file")
        
    except Exception as e:
        logger.error(f"File reading error: {e}")
        raise
    finally:
        # Clean up temporary CSV file if created
        if temp_csv_path and os.path.exists(temp_csv_path):
            try:
                os.remove(temp_csv_path)
                logger.info("Temporary CSV file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary CSV file: {e}")
    
    # Process the data
    success_count = 0
    error_count = 0
    total_rows = len(rows)
    
    logger.info(f"Starting to process {total_rows} rows")
    
    def get_field_value(row, field_list):
        for field in field_list:
            if field in row and row[field]:
                return row[field].strip()
        return ""
    
    for row_num, row in enumerate(rows, start=1):
        try:
            # Extract data from new Excel format
            district_name = get_field_value(row, ['District_name', 'District', 'district_name']).title()
            district_name_bn = get_field_value(row, ['District_name_bn', 'district_name_bn'])
            district_name_as = get_field_value(row, ['District_name_as', 'district_name_as'])
            district_code = get_field_value(row, ['District_Code', 'district_code'])
            
            circle_name = get_field_value(row, ['Revenue_circle', 'Circle_Name', 'circle_name']).title()
            circle_name_bn = get_field_value(row, ['Revenue_circle_bn', 'circle_name_bn'])
            circle_name_as = get_field_value(row, ['Revenue_circle_as', 'circle_name_as'])
            
            village_name = get_field_value(row, ['Village_name', 'village_name']).title()
            village_name_bn = get_field_value(row, ['Village_name_bn', 'village_name_bn'])
            village_name_as = get_field_value(row, ['Village_name_as', 'village_name_as'])
            village_code = get_field_value(row, ['Village_Code', 'village_code'])
            
            gp_name = get_field_value(row, ['Block_Name', 'block_name']).title() or village_name
            
            # Parse coordinates
            def parse_coord(value):
                try:
                    return float(value) if value else None
                except (TypeError, ValueError):
                    return None

            district_lat = parse_coord(row.get("Dist_lat"))
            district_lng = parse_coord(row.get("Dist_lng"))
            village_lat = parse_coord(row.get("Vill_lat"))
            village_lng = parse_coord(row.get("Vill_lng"))
            
            # Use English name as fallback for translations
            district_name_bn = district_name_bn or district_name
            district_name_as = district_name_as or district_name
            circle_name_bn = circle_name_bn or circle_name
            circle_name_as = circle_name_as or circle_name
            village_name_bn = village_name_bn or village_name
            village_name_as = village_name_as or village_name
            gp_name_bn = village_name_bn
            gp_name_as = village_name_as
            
            # Validate required fields
            if not all([district_name, circle_name, village_name]):
                logger.warning(f"Row {row_num}: Missing required fields - District: '{district_name}', Circle: '{circle_name}', Village: '{village_name}'")
                logger.warning(f"Row data: {row}")
                error_count += 1
                continue
            
            # Process the row
            with transaction.atomic():
                # Create/update District
                district = None
                if district_code:
                    district = tblDistrict.objects.filter(code=district_code).first()
                
                if not district:
                    district, created = tblDistrict.objects.get_or_create(
                        name=district_name,
                        defaults={
                            'code': district_code,
                            'name_bn': district_name_bn,
                            'name_as': district_name_as,
                            'latitude': district_lat,
                            'longitude': district_lng
                        }
                    )
                    if not created and update_existing:
                        district.code = district_code or district.code
                        district.name_bn = district_name_bn
                        district.name_as = district_name_as
                        district.latitude = district_lat
                        district.longitude = district_lng
                        district.save()
                elif update_existing:
                    district.name = district_name
                    district.name_bn = district_name_bn
                    district.name_as = district_name_as
                    district.latitude = district_lat
                    district.longitude = district_lng
                    district.save()
                
                # Create/update Circle
                circle, created = tblCircle.objects.get_or_create(
                    name=circle_name,
                    district=district,
                    defaults={
                        'name_bn': circle_name_bn,
                        'name_as': circle_name_as
                    }
                )
                if not created and update_existing:
                    circle.name_bn = circle_name_bn
                    circle.name_as = circle_name_as
                    circle.save()
                
                # Create/update Gram Panchayat
                gp, created = tblGramPanchayat.objects.get_or_create(
                    name=gp_name,
                    circle=circle,
                    defaults={
                        'name_bn': gp_name_bn,
                        'name_as': gp_name_as
                    }
                )
                if not created and update_existing:
                    gp.name_bn = gp_name_bn
                    gp.name_as = gp_name_as
                    gp.save()
                
                # Create/update Village
                village = None
                if village_code:
                    village = tblVillage.objects.filter(code=village_code, gram_panchayat=gp).first()
                
                if not village:
                    village, created = tblVillage.objects.get_or_create(
                        name=village_name,
                        gram_panchayat=gp,
                        defaults={
                            'code': village_code,
                            'name_bn': village_name_bn,
                            'name_as': village_name_as,
                            'latitude': village_lat,
                            'longitude': village_lng
                        }
                    )
                    if not created and update_existing:
                        village.code = village_code or village.code
                        village.name_bn = village_name_bn
                        village.name_as = village_name_as
                        village.latitude = village_lat
                        village.longitude = village_lng
                        village.save()
                elif update_existing:
                    village.name = village_name
                    village.name_bn = village_name_bn
                    village.name_as = village_name_as
                    village.latitude = village_lat
                    village.longitude = village_lng
                    village.save()
                
                success_count += 1
                logger.info(f"Successfully processed row {row_num}: {district_name} -> {circle_name} -> {gp_name} -> {village_name}")
        
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing row {row_num}: {e}")
            logger.error(f"Row data: {row}")
            continue  # Continue with next row
    
    # Final report
    logger.info(f"Import completed. Total: {total_rows}, Success: {success_count}, Errors: {error_count}")
    
    if error_count > 0:
        logger.warning(f"Warning: {error_count} rows had errors and were skipped.")
    
    if success_count == 0:
        raise ValueError("No rows were successfully imported. Please check your file format and data.")

HOUSEHOLD_MAPPING = {
    'District_Code': 'dist_code',
    'Village_Id': 'village_code',
    'Point_Id': 'point_id',
    'Property_Owner': 'property_owner',
    'Name_Of_Person': 'name_of_person',
    'Name_Of_Hohh': 'name_of_hohh',
    'Photo': 'photo',
    'Mobile_Number': 'mobile_number',
    'Data_Access': 'data_access',
    'Community': 'community',
    'Social_Status': 'social_status',
    'Economic_Status': 'economic_status',
    'Wall_Type': 'wall_type',
    'Roof_Type': 'roof_type',
    'Floor_Type': 'floor_type',
    'Plinth_Or_Stilt': 'plinth_or_stilt',
    'Plinth_Or_Stilt_Height_(Ft)': 'plinth_or_stilt_height_ft',
    'Number_Of_Storeys': 'number_of_storeys',
    'Number_Of_Males_Including_Children': 'number_of_males_including_children',
    'Number_Of_Females_Including_Children': 'number_of_females_including_children',
    'Children_Below_6_Years': 'children_below_6_years',
    'Senior_Citizens': 'senior_citizens',
    'Pregnant_Women': 'pregnant_women',
    'Lactating_Women': 'lactating_women',
    'Persons_With_Disability_Or_Chronic_Disease': 'persons_with_disability_or_chronic_disease',
    'Drinking_Water_Source': 'drinking_water_source',
    'Sanitation_Facility': 'sanitation_facility',
    'Toilet_Wall_Material': 'toilet_wall_material',
    'Toilet_Roof_Material': 'toilet_roof_material',
    'Digital_Media_Owned': 'digital_media_owned',
    'House_Has_Electric_Connection': 'house_has_electric_connection',
    'Source_Of_Electricity': 'source_of_electricity',
    'Own_Agriculture_Land': 'own_agriculture_land',
    'Area_Of_Agriculture_Land_Owned_(Bigha)': 'area_of_agriculture_land_owned_bigha',
    'Land_Area_Annually_Cultivated_(Bigha)': 'land_area_annually_cultivated_bigha',
    'Crops_Cultivated': 'crops_cultivated',
    'Specify_Other': 'specify_other',
    'Number_Of_Crops_Normally_Raised_Every_Year': 'number_of_crops_normally_raised_every_year',
    'Livelihood_Primary': 'livelihood_primary',
    'Livelihood_Secondary': 'livelihood_secondary',
    'Do_You_Have_Big_Cattle_Cattle_Buffalo': 'do_you_have_big_cattle_cattle_buffalo',
    'Number_Of_Big_Cattle_Animals': 'number_of_big_cattle_animals',
    'Do_You_Have_Small_Cattle_Goat_Sheep_Pig': 'do_you_have_small_cattle_goat_sheep_pig',
    'Number_Of_Small_Cattle_Animals': 'number_of_small_cattle_animals',
    'Do_You_Have_Poultry_Chicken_And_Duck': 'do_you_have_poultry_chicken_and_duck',
    'Number_Of_Poultry_Animals': 'number_of_poultry_animals',
    'Approximate_Income_Earned_Every_Year_Inr': 'approximate_income_earned_every_year_inr',
    'Expense_On_Education': 'expense_on_education',
    'Expense_On_Health': 'expense_on_health',
    'Expense_On_Food': 'expense_on_food',
    'Expense_On_Tobacco,_Liquor': 'expense_on_tobacco_liquor',
    'Expense_On_House_Repair': 'expense_on_house_repair',
    'Expense_On_Festival_Marriage_And_Other_Social_Occassions': 'expense_on_festival_marriage_and_other_social_occassions',
    'Amount_Spent_For_Agriculture_Livestock': 'amount_spent_for_agriculture_livestock',
    'Loss_Due_To_Flood': 'loss_due_to_flood',
    'Loan_Availed': 'loan_availed',
    'Loan_Amount': 'loan_amount',
    'Loan_Purpose': 'loan_purpose',
    'House_Affected_By_Flood': 'house_affected_by_flood',
    'Economic_Loss_To_Your_House_Due_To_Flood': 'economic_loss_to_your_house_due_to_flood',
    'Amount_Towards_Flood_Recovery_Expenditure': 'amount_towards_flood_recovery_expenditure',
    'Maximum_Flood_Height_In_House(Ft)': 'maximum_flood_height_in_house_ft',
    'Year_In_Which_Maximum_Flood_Experience_In_Your_House': 'year_in_which_maximum_flood_experience_in_your_house',
    'Your_Agriculture_Affected_By_Flood': 'your_agriculture_affected_by_flood',
    'Maximum_Flood_Height_Experience_In_Your_Agriculture(Ft)': 'maximum_flood_height_experience_in_your_agriculture_ft',
    'Year_In_Which_Max_Flood_Experience_In_Your_Agriculture_Land': 'year_in_which_max_flood_experience_in_your_agriculture_land',
    'Duration_Of_Flood_Stay_In_Your_Agriculture_Field': 'duration_of_flood_stay_in_your_agriculture_field',
    'Other_Natural_Hazards_Directly_Impacting_You_And_Family': 'other_natural_hazards_directly_impacting_you_and_family',
    'House_Vulnerable_To_Erosion': 'house_vulnerable_to_erosion',
    'Your_Agriculture_Field_Vulnerable_To_Erosion': 'your_agriculture_field_vulnerable_to_erosion',
    'Building_Quality': 'building_quality',
    'Foundation_Quality': 'foundation_quality',
    'Number_Of_Small_Buildings_Of_The_Household': 'number_of_small_buildings_of_the_household',
    'Occupa,_Ncy_Type_Of_Small,_Building': 'occupa_ncy_type_of_small_building',
    'Presence_Of_Grain_Bank': 'presence_of_grain_bank',
    'Plinth_Height_Of_Grain_Bank(Ft)': 'plinth_height_of_grain_bank_ft',
    'Wall_Material_Of_Grain_Bank': 'wall_material_of_grain_bank',
    'Roof_Material_Of_Grain_Bank': 'roof_material_of_grain_bank',
    'Flood_Depth(M)': 'flood_depth_m',
    'Flood_Class': 'flood_class',
    'Erosion_Class': 'erosion_class',
    'Loan_Class': 'loan_class',
    'Agrculture_Land_Class': 'agrculture_land_class',
    'Loan_Class.1': 'loan_class_1',
    'Fld_Hh_Class': 'fld_hh_class',
    'Repair_Class': 'repair_class',
    'Economic_Loss_Hh': 'economic_loss_hh',
    'Loss_Agricultire/Livlihood': 'loss_agricultire_livlihood',
    'Big_Cattle': 'big_cattle',
    'Small_Cattle': 'small_cattle',
    'House_Type': 'house_type',
    'Income_Class': 'income_class',
    'Crops_Diversity': 'crops_diversity',
    'Sanitation_Type':'Sanitation_Type'
}

COMMERCIAL_MAPPING = {
    'District_Code': 'district_code',
    'Village_Id': 'village_code',
    'District_Name': 'district_name',
    'Village_Name': 'village_name',
    'Point_Id': 'point_id',
    'Type_Of_Occupancy': 'type_of_occupancy',
    'Type_Of_Occupancy_Others': 'type_of_occupancy_others',
    'Property_Owner': 'property_owner',
    'Name_Of_Person': 'name_of_person',
    'Photo': 'photo',
    'Name_Of_The_Building': 'name_of_the_building',
    'Name_Of_The_In-Charge': 'name_of_the_in_charge',
    'Phone_Number_Of_The_In-Charge': 'phone_number_of_the_in_charge',
    'Wall_Type': 'wall_type',
    'Floor_Type': 'floor_type',
    'Roof_Type': 'roof_type',
    'Plinth_Above_Ground': 'plinth_above_ground',
    'Plinth_Above_Ground_Stilt_Height_In_(Ft)': 'plinth_above_ground_stilt_height_in_ft',
    'Building_Affected_By_Normal_Flood': 'building_affected_by_normal_flood',
    'Approximate_Content_Value_Inr': 'approximate_content_value_inr',
    'Approximate_Value_Business_Per_Year': 'approximate_value_business_per_year',
    'Average_Room_Width_(Ft)': 'average_room_width_ft',
    'Average_Room_Length_(Ft)': 'average_room_length_ft',
    'Building_Quality': 'building_quality',
    'Foundation_Quality': 'foundation_quality',
    'Access_Road_During_Flood': 'access_road_during_flood',
    'Flood_Depth_(m)': 'flood_depth_m',
    'Erosion_Class': 'erosion_class',
}

TRANSFORMER_MAPPING = {
    'Village_Name': 'village_name',
    'District_Name': 'district_name',
    'District_Code': 'district_code',
    'Village_Id': 'village_code',
    'Transformer_Site_Address': 'transformer_site_address',
    'Latitude': 'latitude',
    'Longitude': 'longitude',
    'Flood_Depth(m)': 'flood_depth_m',
    'Flood_Class': 'flood_class',
    'Erosion_Class': 'erosion_class',
}

CRITICAL_FACILITY = {
    'District_Code': 'district_code',
    'District_Name': 'district_name',   
    'Village_Name': 'village_name',
    'Village_Id': 'village_code',
    'Point_Id': 'point_id',
    'Occupancy_Type': 'occupancy_type',
    'Photo': 'photo',
    'Name_Of_Building': 'name_of_building',
    'Incharge_Name': 'incharge_name',
    'Mobile_Number': 'mobile_number',
    'Wall_Type': 'wall_type',
    'Floor_Type': 'floor_type',
    'Roof_Type': 'roof_type',
    'Plinth_Or_Stilt': 'plinth_or_stilt',
    'Plinth_Or_Stilt_Height_(Ft)': 'plinth_or_stilt_height_ft',
    'Drinking_Water_Source': 'drinking_water_source',
    'House_Has_Electric_Connection': 'house_has_electric_connection',
    'Source_Of_Electricity': 'source_of_electricity',
    'Number_Of_Rooms': 'number_of_rooms',
    'Average_Room_Length_(Ft)': 'average_room_length_ft',
    'Average_Room_Width_(Ft)': 'average_room_width_ft',
    'Kitchen_Facility': 'kitchen_facility',
    'Toilet_Facility': 'toilet_facility',
    'Number_Of_Toilets': 'number_of_toilets',
    'Water_Facility_In_Toilet': 'water_facility_in_toilet',
    'Electricity_Facility_In_Toilet': 'electricity_facility_in_toilet',
    'Building_Affected_By_Normal_Flood': 'building_affected_by_normal_flood',
    'Used_As_A_Flood/Emergency_Shelter': 'used_as_a_flood_emergency_shelter',
    'Access_(Road)_During_Flood': 'access_road_during_flood',
    'Building_Quality': 'building_quality',
    'Foundation_Quality': 'foundation_quality',
    'Flood_Depth(m)': 'flood_depth_m',
    'Flood_Class': 'flood_class',
    'Erosion_Class': 'erosion_class',
}

ELECTRIC_POLES = {
    'Village_Name': 'village_name',
    'District_Name': 'district_name',
    'District_Code': 'district_code',
    'Village_Id': 'village_code', 
    'Uid': 'uid',
    'Latitude': 'latitude',
    'Longitude': 'longitude',
    'Electric_Pole_Name': 'electric_pole_name',
    'Electric_Pole_Material': 'electric_pole_material',
    'Remarks_On_Pole_Condition': 'remarks_on_pole_condition',
    'Photo': 'photo',
    'Flood_Depth(m)': 'flood_depth_m',
    'Flood_Class': 'flood_class',
    'Erosion_Class': 'erosion_class',
}


VILLAGES_OF_ALL_THE_DISTRICTS = {
    'District_Name': 'district_name',
    'Revenue_circle': 'revenue_circle',
    'Village_name': 'village_name',
    'District_Code': 'district_code',
    'Village_Code': 'village_code',
    'Circle_Name': 'circle_name',
    'Block_Name': 'block_name',
    'Distance_from_Headquarter': 'distance_from_headquarter',
    'Total_Area': 'total_area',
    'Average_Elevation': 'average_elevation',
    'Topography': 'topography',

}

VILLAGE_ROAD_INFO_MAPPING = {
    'District_Name': 'district_name',
    'Village_Name': 'village_name',
    'Village_Id': 'village_code',  # this links to tblVillage via village_code
    'District_Code': 'district_code',
    'Road_Surface_Type': 'road_surface_type',
    'Road_Constructed_By': 'road_constructed_by',
    'Road_Length_(m)': 'road_length_m',
    'Flood_Depth(m)': 'flood_depth_m',
    'Flood_Class': 'flood_class'
}

VILLAGE_ROAD_INFO_EROSION = {
    'District_Name': 'district_name',
    'Village_Name': 'village_name',
    'District_Code': 'district_code',
    'Village_Id': 'village_code',  # links to tblVillage via village_code
    'Road_Surface_Type': 'road_surface_type',
    'Road_Constructed_By': 'road_constructed_by',
    'Road_Length_(m)': 'road_length_m',
    'Erosion_Class': 'erosion_class'
}

TRAINING_MASTER_LIST={
    'Activity':'name',
    'Activity_bn':"name_bn",
    "Activity_as":"name_as"
}

RESCUE_EQUEP_MASTER_LIST={
    'Task_Force':'name',
    'Task_Force_bn':'name_bn',
    'Task_Force_as':'name_as',
    'Item':"task_force",
    'Item_bn':"task_force_bn",
    'Item_as':"task_force_as",
    'Specification':'specification',
    'Specification_bn':'specification_bn',
    'Specification_as':'specification_as'
}

VDMP_ACTIVITIES={
    'Activity_Name':'name',
    'Activity_Name_bn':'name_bn',
    'Activity_Name_as':'name_as',
    'Sr. No':'order'
}


BRIDGE_SURVEY_INFO = {
    'Username': 'username',
    'spatial_id': 'spatial_id',
    'spatial_ref': 'spatial_ref',
    'polygon_id': 'polygon_id',
    'village_id': 'village_code',
    'village_name': 'village_name',
    'district_name': 'district_name',
    'survey_id': 'survey_id',
    'geometry': 'geometry',
    'user_id': 'user_id',
    'under_id': 'under_id',
    'unique_id': 'unique_id',
    'date': 'date',
    'form_id': 'form_id',
    'tab_id': 'tab_id',
    'tab_name': 'tab_name',

    'Bridge surface type': 'bridge_surface_type',
    'Length (meters)': 'length_meters',
    'Width(meters)': 'width_meters',
    'Photographs': 'photographs',
    'Bridge pillar material': 'bridge_pillar_material',
    'Number of pillars bridge has': 'number_of_pillars',
    'Deck material': 'deck_material',
    'Condition of deck': 'condition_of_deck',
    'General condition of bridge': 'general_condition',
    'Status of the access part of bridge': 'status_access_part',
    'Any other remarks': 'remarks',
}


RISK_ASSESMENT_MAPPING = {
    'Village_Name': 'village_name',
    'Vill_ID': 'village_code',
    'Hazard': 'hazard',
    'Exposure_Type': 'exposure_type',
    'Total Exposure Value (INR Crore)': 'total_exposure_value_inr_crore',
    'Loss (INR Crore)': 'loss_inr_crore',
    'Loss % wrt exposure value': 'loss_percent_wrt_exposure_value',
}



import requests

def get_lat_lon(name):
    API_KEY = "pk.0e49d17193d1898c2e3082b3c7143384"
    place = f"{name}, Assam, India"
    url = f"https://us1.locationiq.com/v1/search?key={API_KEY}&q={place}&format=json"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']
                return lat, lon
        print(f"Failed to fetch location for: {name}")
    except Exception as e:
        print(f"Error: {e} for place: {name}")
    return None, None


def store_lat_lon():
    # Update Districts
    all_districts = tblDistrict.objects.all()
    for district in all_districts:
        district_name = district.name.strip().title()
        lat, lon = get_lat_lon(district_name)

        if lat and lon:
            district.latitude = lat
            district.longitude = lon
        district.name = district_name
        district.save()
        print(f"District: {district.name}, Latitude: {lat}, Longitude: {lon}")

    # Update Circles
    all_circles = tblCircle.objects.all()
    for circle in all_circles:
        circle.name = circle.name.strip().title()
        circle.save()

    # Update Gram Panchayats
    all_grampanchayat = tblGramPanchayat.objects.all()
    for gp in all_grampanchayat:
        gp.name = gp.name.strip().title()
        gp.save()

    # Update Villages (once per district)
    all_villages = tblVillage.objects.select_related(
        "gram_panchayat", "gram_panchayat__circle", "gram_panchayat__circle__district"
    )

    for village in all_villages:
        village_name = f"{village.name}, {village.gram_panchayat.circle.district.name}"
        lat, lon = get_lat_lon(village_name)

        if lat and lon:
            village.latitude = lat
            village.longitude = lon

        village.name = village.name.strip().title()
        village.save()
        print(f"Village: {village.name}, Latitude: {lat}, Longitude: {lon}")

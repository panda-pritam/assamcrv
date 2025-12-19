import pandas as pd
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_survey_data(df, district_code, village_code, activity_type="household"):
    """
    Common data cleaning function for all VDMP activities
    
    Args:
        df: Raw dataframe from mobile_db
        district_code: District code for the village
        village_code: Village code
        activity_type: Type of activity (household, commercial, etc.)
    
    Returns:
        Cleaned dataframe with standardized columns and classifications
    """
    logger.info(f"Starting data cleaning for {activity_type} activity")
    logger.info(f"Input dataframe shape: {df.shape}")
    
    # Exclude columns from cleaning
    exclude_columns = ['latitude', 'longitude', 'unique_id', 'village_name', 'district_name', 'form_id']
    
    # Apply text and numeric cleaning
    for col in df.columns:
        if col in exclude_columns:
            logger.debug(f"Skipping cleaning for excluded column: {col}")
            continue
        
        logger.debug(f"Cleaning column: {col}")
        df[col] = df[col].apply(lambda v: _clean_text(v, col_name=col))
        df[col] = df[col].apply(lambda v: _convert_numeric(v, col_name=col))
    
    # Add standard codes
    df['dist_code'] = district_code
    df['village_code'] = village_code
    logger.info(f"Added district_code: {district_code}, village_code: {village_code}")
    
    # Apply activity-specific processing
    if activity_type == "household":
        df = _process_household_specific(df)
    elif activity_type == "commercial":
        df = _process_commercial_specific(df)
    
    logger.info(f"Cleaning completed. Output dataframe shape: {df.shape}")
    return df

def _clean_text(x, col_name=None):
    """Clean text fields matching original cleaning script"""
    if pd.isna(x) or not isinstance(x, str):
        return x
    
    x = str(x).strip()
    if x == "" or x.startswith(("http://", "https://")):
        return x
    
    # Remove all bracketed content (matching original script)
    x = re.sub(r'\([^)]*\)', '', x)
    
    # Keep common punctuation like / + & - , . and parentheses (matching original)
    x = re.sub(r'[^A-Za-z0-9\s\.\-<\(\),\/\+\&:_%\']', '', x)
    x = re.sub(r'\s+', ' ', x).strip()
    
    # Title case with special handling
    x = x.title()
    
    # Fix acronyms
    x = re.sub(r'\bTv\b', 'TV', x)
    
    # preserve OBC in community column
    if col_name and "community" in col_name.lower():
        x = re.sub(r'\bObc\b', 'OBC', x)
    
    return x

def _convert_numeric(x, col_name=None):
    """Convert numeric-like strings to float only for numeric fields"""
    if pd.isna(x) or isinstance(x, (int, float)):
        return x
    
    s = str(x).strip()
    if s == "" or s.startswith(("http://", "https://")):
        return x
    
    # Only convert if column name suggests it's numeric
    numeric_keywords = ['amount', 'number', 'height', 'income', 'expense', 'cost', 'price', 'value', 'bigha', 'year', 'age']
    if col_name and any(keyword in col_name.lower() for keyword in numeric_keywords):
        # Extract numeric value
        m = re.search(r'(-?\d+(?:\.\d+)?)', s.replace(',', ''))
        if m:
            try:
                return float(m.group(1))
            except:
                return x
    return x

def _process_household_specific(df):
    """Apply household-specific processing and classifications"""
    logger.info("Applying household-specific processing")
    
    # Unit conversions (feet to meters)
    if 'maximum_flood_height_in_house_ft' in df.columns:
        df['maximum_flood_height_meter'] = df['maximum_flood_height_in_house_ft'].apply(
            lambda x: (x * 0.3048) if pd.notna(x) and isinstance(x, (int, float)) else None
        )
        logger.debug("Converted flood height from feet to meters")
    
    if 'plinth_or_stilt_height_ft' in df.columns:
        df['plinth_or_stilt_height_meter'] = df['plinth_or_stilt_height_ft'].apply(
            lambda x: (x * 0.3048) if pd.notna(x) and isinstance(x, (int, float)) else None
        )
        logger.debug("Converted plinth height from feet to meters")
    
    # Calculate flood depth (keep as decimal)
    if 'maximum_flood_height_meter' in df.columns and 'plinth_or_stilt_height_meter' in df.columns:
        df['flood_depth_m'] = (
            df['maximum_flood_height_meter'].fillna(0) + 
            df['plinth_or_stilt_height_meter'].fillna(0)
        ).round(3)  # Keep as decimal with 3 decimal places
        logger.debug("Calculated flood depth metric")
    
    # Apply classifications
    df = _apply_classifications(df)
    
    return df

def _process_commercial_specific(df):
    """Apply commercial-specific processing"""
    logger.info("Applying commercial-specific processing")
    # Add commercial-specific logic here
    return df

def _apply_classifications(df):
    """Apply classification logic to dataframe"""
    logger.info("Applying classification logic")
    
    # Flood depth classification
    if 'flood_depth_m' in df.columns:
        df['flood_class'] = df['flood_depth_m'].apply(_classify_flood)
        logger.debug("Applied flood depth classification")
    
    # Loan classifications
    if 'loan_amount' in df.columns:
        df['loan_class'] = df['loan_amount'].apply(_classify_loan)
        df['loan_class_1'] = df['loan_amount'].apply(_classify_loan)  # Same as loan_class
        logger.debug("Applied loan classification")
    
    # Agricultural land classification
    if 'area_of_agriculture_land_owned_bigha' in df.columns:
        df['area_of_agriculture_land_owned_bigha'] = pd.to_numeric(
            df['area_of_agriculture_land_owned_bigha'], errors='coerce'
        ).fillna(0)
        df['agrculture_land_class'] = df['area_of_agriculture_land_owned_bigha'].apply(_classify_agri_land)
        logger.debug("Applied agricultural land classification")
    
    # Flood height household classification
    if 'maximum_flood_height_in_house_ft' in df.columns:
        df['fld_hh_class'] = df['maximum_flood_height_in_house_ft'].apply(_classify_flood_height)
        logger.debug("Applied flood height household classification")
    
    # Repair cost classification
    if 'expense_on_house_repair' in df.columns:
        df['repair_class'] = df['expense_on_house_repair'].apply(_classify_cost)
        logger.debug("Applied repair cost classification")
    
    # Economic loss household classification
    if 'economic_loss_to_your_house_due_to_flood' in df.columns:
        df['economic_loss_hh'] = df['economic_loss_to_your_house_due_to_flood'].apply(_classify_cost)
        logger.debug("Applied economic loss household classification")
    
    # Agriculture livelihood loss classification
    if 'amount_spent_for_agriculture_livestock' in df.columns:
        df['loss_agricultire_livelihood'] = df['amount_spent_for_agriculture_livestock'].apply(_classify_cost)
        logger.debug("Applied agriculture livelihood loss classification")
    
    # Big cattle classification
    if 'number_of_big_cattle_animals' in df.columns:
        df['big_cattle'] = df['number_of_big_cattle_animals'].apply(lambda x: _classify_cattle(x, big=True))
        logger.debug("Applied big cattle classification")
    
    # Small cattle classification
    if 'number_of_small_cattle_animals' in df.columns:
        df['small_cattle'] = df['number_of_small_cattle_animals'].apply(lambda x: _classify_cattle(x, big=False))
        logger.debug("Applied small cattle classification")
    
    # House type classification
    if 'wall_type' in df.columns and 'roof_type' in df.columns:
        df['house_type'] = df.apply(
            lambda row: _classify_house_type(row['wall_type'], row['roof_type']), axis=1
        )
        logger.debug("Applied house type classification")
    
    # Income classification
    if 'approximate_income_earned_every_year_inr' in df.columns:
        df['income_class'] = df['approximate_income_earned_every_year_inr'].apply(_classify_income)
        logger.debug("Applied income classification")
    
    # Duration classification
    # if 'duration_of_flood_stay_in_your_agriculture_field' in df.columns:
    #     df['duration_class'] = df['duration_of_flood_stay_in_your_agriculture_field'].apply(_classify_duration)
    #     logger.debug("Applied duration classification")
    
    # Erosion classification
    if 'your_agriculture_field_vulnerable_to_erosion' in df.columns:
        df['erosion_class'] = df['your_agriculture_field_vulnerable_to_erosion'].apply(_classify_erosion)
    else:
        df['erosion_class'] = None
    logger.debug("Applied erosion classification")
    
    # Flood depth from survey classification (FLOOD_CLASS2)
    if 'flood_depth_m' in df.columns:
        df['FLOOD_CLASS2'] = df['flood_depth_m'].apply(_classify_flood)
        logger.debug("Applied FLOOD_CLASS2 classification")
    
    # Sanitation type classification
    if 'sanitation_facility' in df.columns:
        df['Sanitation_Type'] = df['sanitation_facility']
        logger.debug("Applied sanitation type classification")
    
    # Crops diversity calculation (proper classification)
    if 'number_of_crops_normally_raised_every_year' in df.columns:
        df['crops_diversity'] = df['number_of_crops_normally_raised_every_year'].apply(_classify_crops_diversity)
        logger.debug("Applied crops diversity classification")
    
    return df

def _classify_flood(depth):
    """Classify flood depth into categories"""
    if pd.isna(depth): return None
    try:
        depth = int(float(depth))
        if depth < 0.3: return "0.3 m"
        elif depth < 0.5: return "0.3 - 0.5 m"
        elif depth < 1.0: return "0.5 - 1.0 m"
        else: return ">1.0 m"
    except (ValueError, TypeError):
        return None

def _classify_loan(amount):
    """Classify loan amount into categories"""
    if pd.isna(amount): return "No loan"
    try:
        amount = int(float(amount))
        if amount <= 0: return "No loan"
        if amount < 10000: return "Upto 10K"
        elif amount < 50000: return "Upto 50K"
        elif amount < 100000: return "Upto 100K"
        else: return "Morethan 100K"
    except (ValueError, TypeError):
        return "No loan"

def _classify_agri_land(area):
    """Classify agricultural land area"""
    if pd.isna(area): return None
    try:
        area = int(float(area))
        if area < 0.5: return "Lessthan 0.5 bigha"
        elif area < 1.5: return "Upto 1.5 bigha"
        elif area <= 2.5: return "Upto 2.5 bigha"
        else: return "Morethan 2.5 bigha"
    except (ValueError, TypeError):
        return None

def _classify_flood_height(height_ft):
    """Classify flood height in feet"""
    if pd.isna(height_ft): return "No Flood"
    try:
        height_ft = float(height_ft)
        if height_ft <= 0: return "No Flood"
        if height_ft < 0.5: return "Upto 0.5ft"
        elif height_ft < 1.5: return "Upto 1.5ft"
        elif height_ft < 2.5: return "Upto 2.5ft"
        else: return "Morethan 2.5ft"
    except (ValueError, TypeError):
        return "No Flood"

def _classify_cost(val):
    """Classify cost values"""
    if pd.isna(val): return "None"
    try:
        val = float(val)
        if val <= 0: return "None"
        if val < 5000: return "Upto 5K"
        elif val < 15000: return "Upto 15K"
        elif val < 25000: return "Upto 25K"
        else: return "Morethan 25K"
    except (ValueError, TypeError):
        return "None"

def _classify_cattle(num, big=True):
    """Classify cattle numbers"""
    if pd.isna(num): return "No big cattle" if big else "No small cattle"
    try:
        num = int(float(num))
        if num <= 0: return "No big cattle" if big else "No small cattle"
        if num < 4: return "Upto 3 big cattle" if big else "Upto 3 small cattle"
        elif num < 6: return "3 to 6 big cattle" if big else "3 to 6 small cattle"
        else: return "Morethan 6 big cattle" if big else "Morethan 6 small cattle"
    except (ValueError, TypeError):
        return "No big cattle" if big else "No small cattle"

def _classify_income(income):
    """Classify income levels"""
    if pd.isna(income): return None
    try:
        income = float(income)
        if income <= 50000: return "Upto 50K"
        elif income <= 150000: return "Upto 100K"
        elif income <= 250000: return "Upto 250K"
        else: return ">250K"
    except (ValueError, TypeError):
        return None

def _classify_house_type(wall, roof):
    """Classify house type based on wall and roof materials"""
    wall_map = {
        "brick with cement": "brick with cement",
        "brick without cement": "brick with cement",
        "concrete frame with infill brick walls": "brick with cement",
        "wood": "wood",
        "wood, bamboo & cow dung": "wood",
        "grass": "grass",
        "grass/leaves/plastic": "grass"
    }
    roof_map = {
        "tin": "tin", "wood": "wood", "grass": "grass",
        "concrete": "concrete", "stone slabs": "concrete", "tiles": "concrete",
        "bamboo": "thatch", "ikra": "thatch", "thatch": "thatch"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), w)
    r_norm = next((v for k, v in roof_map.items() if k in r), r)
    
    if w_norm == "brick with cement" and r_norm == "concrete":
        return "Pucca"
    elif w_norm == "brick with cement" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"
       

def _classify_agri_land(area):
    """Classify agricultural land area"""
    if pd.isna(area): return None
    try:
        area = int(float(area))
        if area < 0.5: return "Lessthan 0.5 bigha"
        elif area < 1.5: return "Upto 1.5 bigha"
        elif area <= 2.5: return "Upto 2.5 bigha"
        else: return "Morethan 2.5 bigha"
    except (ValueError, TypeError):
        return None

def _classify_flood_height(height_ft):
    """Classify flood height in feet"""
    if pd.isna(height_ft): return "No Flood"
    try:
        height_ft = float(height_ft)
        if height_ft <= 0: return "No Flood"
        if height_ft < 0.5: return "Upto 0.5ft"
        elif height_ft < 1.5: return "Upto 1.5ft"
        elif height_ft < 2.5: return "Upto 2.5ft"
        else: return "Morethan 2.5ft"
    except (ValueError, TypeError):
        return "No Flood"

def _classify_cost(val):
    """Classify cost values"""
    if pd.isna(val): return "None"
    try:
        val = float(val)
        if val <= 0: return "None"
        if val < 5000: return "Upto 5K"
        elif val < 15000: return "Upto 15K"
        elif val < 25000: return "Upto 25K"
        else: return "Morethan 25K"
    except (ValueError, TypeError):
        return "None"

def _classify_cattle(num, big=True):
    """Classify cattle numbers"""
    if pd.isna(num): return "No big cattle" if big else "No small cattle"
    try:
        num = int(float(num))
        if num <= 0: return "No big cattle" if big else "No small cattle"
        if num < 4: return "Upto 3 big cattle" if big else "Upto 3 small cattle"
        elif num < 6: return "3 to 6 big cattle" if big else "3 to 6 small cattle"
        else: return "Morethan 6 big cattle" if big else "Morethan 6 small cattle"
    except (ValueError, TypeError):
        return "No big cattle" if big else "No small cattle"

def _classify_income(income):
    """Classify income levels"""
    if pd.isna(income): return None
    try:
        income = float(income)
        if income <= 50000: return "Upto 50K"
        elif income <= 150000: return "Upto 100K"
        elif income <= 250000: return "Upto 250K"
        else: return ">250K"
    except (ValueError, TypeError):
        return None

def _classify_house_type(wall, roof):
    """Classify house type based on wall and roof materials"""
    wall_map = {
        "brick with cement": "brick with cement",
        "brick without cement": "brick with cement",
        "concrete frame with infill brick walls": "brick with cement",
        "wood": "wood",
        "wood, bamboo & cow dung": "wood",
        "grass": "grass",
        "grass/leaves/plastic": "grass"
    }
    roof_map = {
        "tin": "tin", "wood": "wood", "grass": "grass",
        "concrete": "concrete", "stone slabs": "concrete", "tiles": "concrete",
        "bamboo": "thatch", "ikra": "thatch", "thatch": "thatch"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), w)
    r_norm = next((v for k, v in roof_map.items() if k in r), r)
    
    if w_norm == "brick with cement" and r_norm == "concrete":
        return "Pucca"
    elif w_norm == "brick with cement" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"
     

def _classify_agri_land(area):
    """Classify agricultural land area"""
    if pd.isna(area): return None
    try:
        area = int(float(area))
        if area < 0.5: return "Lessthan 0.5 bigha"
        elif area < 1.5: return "Upto 1.5 bigha"
        elif area <= 2.5: return "Upto 2.5 bigha"
        else: return "Morethan 2.5 bigha"
    except (ValueError, TypeError):
        return None

def _classify_flood_height(height_ft):
    """Classify flood height in feet"""
    if pd.isna(height_ft): return "No Flood"
    try:
        height_ft = float(height_ft)
        if height_ft <= 0: return "No Flood"
        if height_ft < 0.5: return "Upto 0.5ft"
        elif height_ft < 1.5: return "Upto 1.5ft"
        elif height_ft < 2.5: return "Upto 2.5ft"
        else: return "Morethan 2.5ft"
    except (ValueError, TypeError):
        return "No Flood"

def _classify_cost(val):
    """Classify cost values"""
    if pd.isna(val): return "None"
    try:
        val = float(val)
        if val <= 0: return "None"
        if val < 5000: return "Upto 5K"
        elif val < 15000: return "Upto 15K"
        elif val < 25000: return "Upto 25K"
        else: return "Morethan 25K"
    except (ValueError, TypeError):
        return "None"

def _classify_cattle(num, big=True):
    """Classify cattle numbers"""
    if pd.isna(num): return "No big cattle" if big else "No small cattle"
    try:
        num = int(float(num))
        if num <= 0: return "No big cattle" if big else "No small cattle"
        if num < 4: return "Upto 3 big cattle" if big else "Upto 3 small cattle"
        elif num < 6: return "3 to 6 big cattle" if big else "3 to 6 small cattle"
        else: return "Morethan 6 big cattle" if big else "Morethan 6 small cattle"
    except (ValueError, TypeError):
        return "No big cattle" if big else "No small cattle"

def _classify_income(income):
    """Classify income levels"""
    if pd.isna(income): return None
    try:
        income = float(income)
        if income <= 50000: return "Upto 50K"
        elif income <= 150000: return "Upto 100K"
        elif income <= 250000: return "Upto 250K"
        else: return ">250K"
    except (ValueError, TypeError):
        return None

def _classify_house_type(wall, roof):
    """Classify house type based on wall and roof materials"""
    wall_map = {
        "brick with cement": "brick with cement",
        "brick without cement": "brick with cement",
        "concrete frame with infill brick walls": "brick with cement",
        "wood": "wood",
        "wood, bamboo & cow dung": "wood",
        "grass": "grass",
        "grass/leaves/plastic": "grass"
    }
    roof_map = {
        "tin": "tin", "wood": "wood", "grass": "grass",
        "concrete": "concrete", "stone slabs": "concrete", "tiles": "concrete",
        "bamboo": "thatch", "ikra": "thatch", "thatch": "thatch"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), w)
    r_norm = next((v for k, v in roof_map.items() if k in r), r)
    
    if w_norm == "brick with cement" and r_norm == "concrete":
        return "Pucca"
    elif w_norm == "brick with cement" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"

def _classify_duration(duration):
    """Classify flood duration"""
    if pd.isna(duration): return None
    duration_str = str(duration).strip().lower()
    if "20" in duration_str and ("more" in duration_str or ">" in duration_str):
        return ">20 Days"
    elif "15" in duration_str and "20" in duration_str:
        return "15-20 Days"
    elif "7" in duration_str and "15" in duration_str:
        return "7-15 Days"
    else:
        return duration_str

def _classify_erosion(vulnerable):
    """Classify erosion vulnerability"""
    if pd.isna(vulnerable): return "No"
    vulnerable_str = str(vulnerable).strip().lower()
    if vulnerable_str in ["yes", "y", "1", "true"]:
        return "Yes"
    else:
        return "No"
def _classify_crops_diversity(num_crops):
    """Classify crops diversity"""
    if pd.isna(num_crops): return "No crops"
    try:
        num_crops = int(float(num_crops))
        if num_crops <= 0: return "No crops"
        elif num_crops == 1: return "Single crop"
        elif num_crops <= 3: return "Low diversity"
        elif num_crops <= 5: return "Medium diversity"
        else: return "High diversity"
    except (ValueError, TypeError):
        return "No crops"
import pandas as pd
import os
import numpy as np
from django.conf import settings
from vdmp_dashboard.models import HouseholdSurvey, Commercial, Critical_Facility
from vdmp_progress.models import (house_type_combination_mapping, house_type, Risk_Assessment_Result,
                                 flood_MDR_table, EQ_MDR_table, wind_MDR_table)
from village_profile.models import tblVillage

# Import GDAL instead of rasterio
try:
    import sys
    print(f"DEBUG: Python path: {sys.path[:3]}")
    print(f"DEBUG: Attempting GDAL import...")
    from osgeo import gdal, osr
    print(f"DEBUG: GDAL imported successfully, version: {gdal.__version__}")
except ImportError as e:
    import sys
    import os
    print(f"DEBUG: GDAL import failed")
    print(f"DEBUG: Python executable: {sys.executable}")
    print(f"DEBUG: PATH environment: {os.environ.get('PATH', '')[:500]}")
    print(f"DEBUG: sys.path: {sys.path}")
    raise ImportError(f"CRITICAL: GDAL required for raster value extraction: {e}")

# Raster file paths
EQ_RASTER = os.path.join(settings.BASE_DIR, 'static', 'risk_assessment_raster', 'PGA_Raster.img')
WIND_RASTER = os.path.join(settings.BASE_DIR, 'static', 'risk_assessment_raster', 'Wind_Raster.tif')

print(f"DEBUG: EQ_RASTER path: {EQ_RASTER}")
print(f"DEBUG: WIND_RASTER path: {WIND_RASTER}")
print(f"DEBUG: EQ_RASTER exists: {os.path.exists(EQ_RASTER)}")
print(f"DEBUG: WIND_RASTER exists: {os.path.exists(WIND_RASTER)}")

def sample_raster_values_gdal(path, lats, lons, default_value=0.1):
    """
    Extract EXACT values from raster files using GDAL with bilinear interpolation
    
    This replaces the rasterio-based function with pure GDAL
    
    Args:
        path: Path to raster file
        lats: List of latitude values (EPSG:4326)
        lons: List of longitude values (EPSG:4326)
        default_value: Fallback value if extraction fails
    
    Returns:
        numpy array of extracted values
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raster file not found: {path}")
    
    # Convert to numpy arrays
    lons = np.array(lons, dtype=float).flatten()
    lats = np.array(lats, dtype=float).flatten()
    values = np.full(len(lats), np.nan)
    
    print(f"DEBUG: Extracting EXACT values from {os.path.basename(path)}")
    print(f"DEBUG: Coordinates - Lat: {lats.min():.4f} to {lats.max():.4f}, Lon: {lons.min():.4f} to {lons.max():.4f}")
    
    # Open raster dataset
    ds = gdal.Open(path, gdal.GA_ReadOnly)
    if ds is None:
        raise ValueError(f"Failed to open raster: {path}")
    
    try:
        # Get raster properties
        band = ds.GetRasterBand(1)
        geotransform = ds.GetGeoTransform()
        projection = ds.GetProjection()
        
        # print(f"DEBUG: Raster projection: {projection}")
        # print(f"DEBUG: Raster size: {ds.RasterXSize} x {ds.RasterYSize}")
        # print(f"DEBUG: Geotransform: {geotransform}")
        
        # Create coordinate transformation from WGS84 to raster's CRS
        source_srs = osr.SpatialReference()
        source_srs.ImportFromEPSG(4326)  # WGS84
        
        target_srs = osr.SpatialReference()
        target_srs.ImportFromWkt(projection)
        
        transform = osr.CoordinateTransformation(source_srs, target_srs)
        
        # Get geotransform parameters
        # geotransform[0] = top left x
        # geotransform[1] = pixel width
        # geotransform[2] = rotation, 0 if north up
        # geotransform[3] = top left y
        # geotransform[4] = rotation, 0 if north up
        # geotransform[5] = pixel height (negative value)
        origin_x = geotransform[0]
        origin_y = geotransform[3]
        pixel_width = geotransform[1]
        pixel_height = geotransform[5]
        
        valid_samples = 0
        
        # Process each coordinate
        for i in range(len(lats)):
            try:
                # Transform coordinates to raster's CRS
                point = transform.TransformPoint(lons[i], lats[i])
                x_geo, y_geo = point[0], point[1]
                
                # Convert geographic coordinates to pixel coordinates
                col_f = (x_geo - origin_x) / pixel_width
                row_f = (y_geo - origin_y) / pixel_height
                
                # Get integer pixel indices
                col = int(np.floor(col_f))
                row = int(np.floor(row_f))
                
                # Check if within raster bounds
                if col < 0 or row < 0 or col >= ds.RasterXSize - 1 or row >= ds.RasterYSize - 1:
                    continue
                
                # Read 2x2 block for bilinear interpolation
                # ReadAsArray(xoff, yoff, xsize, ysize)
                block = band.ReadAsArray(col, row, 2, 2)
                
                if block is None or block.shape != (2, 2):
                    continue
                
                # Check for nodata values
                nodata = band.GetNoDataValue()
                if nodata is not None and np.any(block == nodata):
                    continue
                
                # Bilinear interpolation
                # Calculate fractional offsets within the pixel
                dx = col_f - col
                dy = row_f - row
                
                # Interpolate along x-axis for top and bottom rows
                top = block[0, 0] * (1 - dx) + block[0, 1] * dx
                bottom = block[1, 0] * (1 - dx) + block[1, 1] * dx
                
                # Interpolate along y-axis
                values[i] = top * (1 - dy) + bottom * dy
                valid_samples += 1
                
            except Exception as e:
                # Skip this point if any error occurs
                continue
        
        # Report extraction results
        valid_values = values[~np.isnan(values)]
        if len(valid_values) > 0:
            print(f"DEBUG: SUCCESS - Extracted {valid_samples}/{len(lats)} exact values")
            print(f"DEBUG: Value range: {valid_values.min():.4f} to {valid_values.max():.4f}")
            print(f"DEBUG: Sample values: {valid_values[:5]}")
        else:
            print(f"WARNING: Failed to extract any values from {path}")
            # Use default value for all points
            values = np.full(len(lats), default_value)
    
    finally:
        # Clean up
        ds = None
    
    return values

def map_mdr_from_db(df, hazard_col, mdr_model, hazard_field):
    """
    Map hazard values to Mean Damage Ratio (MDR) using database interpolation
    
    MDR represents expected damage percentage (0.0 = no damage, 1.0 = total loss)
    Uses linear interpolation between known hazard-MDR pairs for each house type
    
    Args:
        df: DataFrame with hazard values and house_type_id
        hazard_col: Column name containing hazard values (e.g., 'flood_hazard')
        mdr_model: Database model (flood_MDR_table, EQ_MDR_table, wind_MDR_table)
        hazard_field: Field name in MDR model (e.g., 'flood_depth_m', 'PGA_g')
    
    Returns:
        DataFrame with new MDR column (e.g., 'flood_hazard_mdr')
    """
    try:
        print(f"DEBUG: Starting MDR mapping for {hazard_col}")
        out = []
        # Process each house type separately (R1, R2A, R3B, etc. have different vulnerability)
        for h_type_id in df["house_type_id"].dropna().unique():
            # Get all buildings of this house type
            sub = df[df["house_type_id"] == h_type_id].copy()
            print(f"DEBUG: Processing house type {h_type_id} with {len(sub)} records")
            
            # Get MDR lookup table from database for this house type
            # Example: For R1 + Flood, get all flood_depth_m -> MDR_value pairs
            mdr_data = mdr_model.objects.filter(house_type_id=h_type_id).values(
                hazard_field, 'MDR_value'
            ).order_by(hazard_field)  # Sort by hazard intensity (low to high)
            
            print(f"DEBUG: Found {len(mdr_data)} MDR records for house type {h_type_id}")
            
            # If no MDR data exists for this house type, set MDR to NaN
            if not mdr_data:
                print(f"DEBUG: No MDR data for house type {h_type_id}, setting to NaN")
                sub[f"{hazard_col}_mdr"] = np.nan
                out.append(sub)
                continue
            
            # Convert database records to arrays for numpy interpolation
            # hazard_values: [0.5, 1.0, 2.0, 3.0] (flood depths in meters)
            # mdr_values: [0.1, 0.3, 0.7, 0.9] (damage ratios: 10%, 30%, 70%, 90%)
            hazard_values = [float(d[hazard_field]) for d in mdr_data if d[hazard_field] is not None]
            mdr_values = [float(d['MDR_value']) for d in mdr_data if d['MDR_value'] is not None]
            
            print(f"DEBUG: Hazard range: {min(hazard_values) if hazard_values else 'None'} to {max(hazard_values) if hazard_values else 'None'}")
            print(f"DEBUG: MDR range: {min(mdr_values) if mdr_values else 'None':.6f} to {max(mdr_values) if mdr_values else 'None':.6f}")
            
            # Skip if no valid data points
            if not hazard_values or not mdr_values:
                print(f"DEBUG: No valid hazard/MDR data for house type {h_type_id}")
                sub[f"{hazard_col}_mdr"] = np.nan
                out.append(sub)
                continue
            
            # Ensure MDR values are realistic (0-100% damage)
            mdr_values = np.clip(mdr_values, 0, 1)
            
            # Prepare data for interpolation
            sub = sub.sort_values(hazard_col)
            hazard_input = sub[hazard_col].fillna(0)  # Replace NaN hazards with 0
            
            print(f"DEBUG: Input hazard range: {hazard_input.min():.4f} to {hazard_input.max():.4f}")
            
            # Check for extrapolation (values outside known range)
            min_hazard, max_hazard = min(hazard_values), max(hazard_values)
            extrapolated = (hazard_input < min_hazard) | (hazard_input > max_hazard)
            if extrapolated.any():
                print(f"Warning: {extrapolated.sum()} values extrapolated for {hazard_col} in house type {h_type_id}")
            
            # LINEAR INTERPOLATION:
            # If survey shows 1.5m flood and database has:
            # 1.0m -> 0.3 MDR, 2.0m -> 0.7 MDR
            # Result: 0.3 + (1.5-1.0)/(2.0-1.0) * (0.7-0.3) = 0.5 MDR
            interpolated_mdr = np.interp(
                hazard_input,           # Actual hazard values from survey
                hazard_values,          # Known hazard points from database
                mdr_values,             # Corresponding MDR values
                left=mdr_values[0],     # Use first MDR for values below range
                right=mdr_values[-1]    # Use last MDR for values above range
            )
            
            sub[f"{hazard_col}_mdr"] = interpolated_mdr
            print(f"DEBUG: Interpolated MDR range: {interpolated_mdr.min():.6f} to {interpolated_mdr.max():.6f}")
            print(f"DEBUG: Sample interpolated MDRs: {interpolated_mdr[:5]}")
            out.append(sub)
        
        result_df = pd.concat(out) if out else df
        print(f"DEBUG: Final {hazard_col}_mdr range: {result_df[f'{hazard_col}_mdr'].min():.6f} to {result_df[f'{hazard_col}_mdr'].max():.6f}")
        return result_df
    except Exception as e:
        print(f"Error processing MDR for {hazard_col}: {e}")
        df[f"{hazard_col}_mdr"] = np.nan
        return df

def process_hazards_and_losses(df):
    """
    Process hazard extraction, MDR mapping, and loss calculations
    
    This is the main risk calculation function that:
    1. Extracts hazard values from rasters (EQ, Wind) and survey data (Flood)
    2. Maps hazards to damage ratios using interpolation
    3. Calculates expected losses (MDR × Replacement Cost)
    """
    # Convert coordinates to numeric for raster sampling
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Get house type ID from mapped house type name
    # This links buildings to their vulnerability curves in MDR tables
    df['house_type_id'] = df['mapped_house_type'].apply(
        lambda x: get_house_type_id(x) if x != 'Other / Unknown' else None
    )
    
    # STEP 1: EXTRACT HAZARD VALUES USING GDAL
    # EQ Hazard: Peak Ground Acceleration (PGA) in 'g' units from raster (expected: 0.27-0.49)
    df['eq_hazard'] = np.round(
        sample_raster_values_gdal(EQ_RASTER, df['latitude'], df['longitude'], 0.35), 4
    )
    
    # Wind Hazard: Wind speed in km/h from raster (expected: 19-50)
    df['wind_hazard'] = np.round(
        sample_raster_values_gdal(WIND_RASTER, df['latitude'], df['longitude'], 35), 4
    )
    
    # Flood Hazard: Flood depth in meters from survey data
    df['flood_hazard'] = np.round(
        pd.to_numeric(df['flood_depth_m'], errors='coerce'), 4
    )
    
    # STEP 2: MAP HAZARDS TO DAMAGE RATIOS (MDR)
    # Each function uses interpolation to find MDR for actual hazard values
    df = map_mdr_from_db(df, 'flood_hazard', flood_MDR_table, 'flood_depth_m')
    df = map_mdr_from_db(df, 'eq_hazard', EQ_MDR_table, 'PGA_g')
    df = map_mdr_from_db(df, 'wind_hazard', wind_MDR_table, 'wind_speed_kmph')
    
    # STEP 3: CALCULATE EXPECTED LOSSES
    # Loss = Damage Ratio × Replacement Cost
    # Example: 0.3 MDR × ₹500,000 = ₹150,000 expected loss
    df['flood_loss'] = (df['flood_hazard_mdr'] * df['replacement_cost_inr']).fillna(0).round(2)
    df['eq_loss'] = (df['eq_hazard_mdr'] * df['replacement_cost_inr']).fillna(0).round(2)
    df['wind_loss'] = (df['wind_hazard_mdr'] * df['replacement_cost_inr']).fillna(0).round(2)

    
    return df

def validate_building_dimensions(length, width, area):
    """
    Validate and clean building dimensions to prevent database overflow
    Sets unrealistic values to 0 to avoid pipeline failures
    
    Args:
        length, width, area: Building dimensions
    
    Returns:
        tuple: (cleaned_length, cleaned_width, cleaned_area)
    """
    # Maximum reasonable building dimensions (in feet)
    MAX_LENGTH = 1000  # 1000 ft = ~300m (very large building)
    MAX_WIDTH = 1000   # 1000 ft = ~300m
    MAX_AREA = 100000  # 100,000 sqft = ~9,300 sqm (huge building)
    
    # Convert to numeric and handle NaN
    length = pd.to_numeric(length, errors='coerce')
    width = pd.to_numeric(width, errors='coerce')
    area = pd.to_numeric(area, errors='coerce')
    
    # Check for unrealistic values and set to 0
    if pd.isna(length) or length <= 0 or length > MAX_LENGTH:
        length = 0
    if pd.isna(width) or width <= 0 or width > MAX_WIDTH:
        width = 0
    if pd.isna(area) or area <= 0 or area > MAX_AREA:
        area = 0
        
    # If area is 0 but length/width are valid, recalculate area
    if area == 0 and length > 0 and width > 0:
        calculated_area = length * width
        if calculated_area <= MAX_AREA:
            area = calculated_area
    
    return length, width, area

def get_house_type_id(house_type_name):
    """Get house type ID from house type name"""
    try:
        house_obj = house_type.objects.filter(house_type=house_type_name).first()
        return house_obj.house_type_id if house_obj else None
    except:
        return None

def get_house_type_mapping(wall, roof, floor):
    """
    Map building material combinations to house types and unit costs
    
    Uses fuzzy matching to handle data entry variations:
    1. Exact match: "tin" matches "tin" exactly
    2. Partial match: "tin sheet" contains "tin"
    
    Args:
        wall, roof, floor: Building material strings from survey
    
    Returns:
        tuple: (house_type_name, unit_cost_per_sqft)
        Example: ("R5A Tin House", 1200.0)
    """
    # Handle missing data
    if pd.isna(wall) or pd.isna(roof) or pd.isna(floor):
        return "Other / Unknown", 0.0
    
    # Normalize input strings (lowercase, remove extra spaces)
    wall_clean = str(wall).strip().lower()
    roof_clean = str(roof).strip().lower()
    floor_clean = str(floor).strip().lower()
    
    try:
        # STEP 1: Try exact match first (most reliable)
        # Example: "bamboo" + "thatch" + "mud" -> "R4 Bamboo House"
        mapping = house_type_combination_mapping.objects.filter(
            wall_type__iexact=wall_clean,
            roof_type__iexact=roof_clean,
            floor_type__iexact=floor_clean
        ).first()
        
        if mapping and mapping.house_type:
            return mapping.house_type.house_type, float(mapping.house_type.per_unit_cost)
        
        # STEP 2: Try partial matching (handles variations)
        # Example: "bamboo wall" contains "bamboo"
        mapping = house_type_combination_mapping.objects.filter(
            wall_type__icontains=wall_clean,
            roof_type__icontains=roof_clean,
            floor_type__icontains=floor_clean
        ).first()
        
        if mapping and mapping.house_type:
            return mapping.house_type.house_type, float(mapping.house_type.per_unit_cost)
            
        # No match found - return default
        return "Other / Unknown", 0.0
    except:
        return "Other / Unknown", 0.0

def process_household_data(village_id):
    """Process household survey data for risk assessment"""
    if not HouseholdSurvey.objects.filter(village_id=village_id).exists():
        return None, "No household survey data found"
    
    village = tblVillage.objects.get(id=village_id)
    households = HouseholdSurvey.objects.filter(village_id=village_id).values(
        'id', 'wall_type', 'roof_type', 'floor_type', 'building_area_sqft', 
        'flood_class', 'flood_depth_m', 'point_id', 'latitude', 'longitude'
    )
    
    df = pd.DataFrame(households)
    df['reference_id'] = df['id']
    df['village_name'] = village.name
    df['village_code'] = village.code
    df['asset_type'] = 'household'
    
    # For households, we don't have separate length/width, so set to None
    df['building_length_ft'] = None
    df['building_width_ft'] = None
    
    # Map house types and rates
    df[['mapped_house_type', 'unit_rate_inr']] = df.apply(
        lambda x: pd.Series(get_house_type_mapping(x['wall_type'], x['roof_type'], x['floor_type'])), axis=1
    )
    
    # For households, validate existing building_area_sqft
    df['building_area_sqft'] = df.apply(
        lambda row: validate_building_dimensions(0, 0, pd.to_numeric(row['building_area_sqft'], errors='coerce'))[2], axis=1
    )
    df['replacement_cost_inr'] = df['building_area_sqft'] * df['unit_rate_inr']
    
    # Process hazards and losses
    df = process_hazards_and_losses(df)
    
    # Save to database
    save_risk_results(df, village_id, 'household')
    
    return df, None

def process_commercial_data(village_id):
    """Process commercial data for risk assessment"""
    if not Commercial.objects.filter(village_id=village_id).exists():
        return None, "No commercial data found"
    
    village = tblVillage.objects.get(id=village_id)
    commercial = Commercial.objects.filter(village_id=village_id).values(
        'id', 'wall_type', 'roof_type', 'floor_type', 'flood_depth_m', 
        'point_id', 'latitude', 'longitude', 'average_room_length_ft', 'average_room_width_ft'
    )
    
    df = pd.DataFrame(commercial)
    df['reference_id'] = df['id']
    df['village_name'] = village.name
    df['village_code'] = village.code
    df['asset_type'] = 'commercial'
    
    # Calculate area from room dimensions with validation
    length = pd.to_numeric(df['average_room_length_ft'], errors='coerce').fillna(0)
    width = pd.to_numeric(df['average_room_width_ft'], errors='coerce').fillna(0)
    area = length * width
    
    # Apply validation to clean unrealistic values
    df[['building_length_ft', 'building_width_ft', 'building_area_sqft']] = df.apply(
        lambda row: pd.Series(validate_building_dimensions(
            pd.to_numeric(row['average_room_length_ft'], errors='coerce'),
            pd.to_numeric(row['average_room_width_ft'], errors='coerce'),
            pd.to_numeric(row['average_room_length_ft'], errors='coerce') * pd.to_numeric(row['average_room_width_ft'], errors='coerce')
        )), axis=1
    )
    
    # Map house types and rates
    df[['mapped_house_type', 'unit_rate_inr']] = df.apply(
        lambda x: pd.Series(get_house_type_mapping(x['wall_type'], x['roof_type'], x['floor_type'])), axis=1
    )
    df['replacement_cost_inr'] = df['building_area_sqft'] * df['unit_rate_inr']
    
    # Process hazards and losses
    df = process_hazards_and_losses(df)
    
    # Save to database
    save_risk_results(df, village_id, 'commercial')
    
    return df, None

def process_critical_facility_data(village_id):
    """Process critical facility data for risk assessment"""
    if not Critical_Facility.objects.filter(village_id=village_id).exists():
        return None, "No critical facility data found"
    
    village = tblVillage.objects.get(id=village_id)
    facilities = Critical_Facility.objects.filter(village_id=village_id).values(
        'id', 'wall_type', 'roof_type', 'floor_type', 'flood_depth_m', 'flood_class',
        'point_id', 'latitude', 'longitude', 'average_room_length_ft', 'average_room_width_ft'
    )
    
    df = pd.DataFrame(facilities)
    df['reference_id'] = df['id']
    df['village_name'] = village.name
    df['village_code'] = village.code
    df['asset_type'] = 'critical_facility'
    
    # Calculate area with validation
    df[['building_length_ft', 'building_width_ft', 'building_area_sqft']] = df.apply(
        lambda row: pd.Series(validate_building_dimensions(
            pd.to_numeric(row['average_room_length_ft'], errors='coerce'),
            pd.to_numeric(row['average_room_width_ft'], errors='coerce'),
            pd.to_numeric(row['average_room_length_ft'], errors='coerce') * pd.to_numeric(row['average_room_width_ft'], errors='coerce')
        )), axis=1
    )
    
    # Map house types and rates
    df[['mapped_house_type', 'unit_rate_inr']] = df.apply(
        lambda x: pd.Series(get_house_type_mapping(x['wall_type'], x['roof_type'], x['floor_type'])), axis=1
    )
    df['replacement_cost_inr'] = df['building_area_sqft'] * df['unit_rate_inr']
    
    # Process hazards and losses
    df = process_hazards_and_losses(df)
    
    # Save to database
    save_risk_results(df, village_id, 'critical_facility')
    
    return df, None

def save_risk_results(df, village_id, asset_type):
    """Save risk assessment results to database with optimized batch processing"""
    village = tblVillage.objects.get(id=village_id)
    
    # Clear existing results for this village and asset type
    Risk_Assessment_Result.objects.filter(village_id=village_id, asset_type=asset_type).delete()
    
    # Create new results in optimized batches
    results = []
    batch_size = 500
    
    for _, row in df.iterrows():
        # Get house type object if mapped
        house_type_obj = None
        if row['mapped_house_type'] != 'Other / Unknown':
            house_type_obj = house_type.objects.filter(house_type=row['mapped_house_type']).first()
        
        # Helper function to convert NaN to None for DecimalFields and handle overflow
        def safe_decimal(value, field_type='default'):
            if pd.isna(value):
                return None
            val = float(value)
            
            # Different limits for different field types based on database schema
            if field_type == 'mdr':  # MDR fields: max_digits=10, decimal_places=8
                max_value = 99.99999999  # 10^2 - 1 with 8 decimal places
            elif field_type == 'hazard':  # Hazard fields: max_digits=10, decimal_places=8  
                max_value = 99.99999999
            elif field_type == 'loss':  # Loss fields: max_digits=15, decimal_places=8
                max_value = 9999999.99999999  # 10^7 - 1 with 8 decimal places
            else:  # Default fields: max_digits=12, decimal_places=2
                max_value = 9999999999.99
            
            if abs(val) > max_value:
                print(f"WARNING: Value {val} exceeds {field_type} field limit, capping at {max_value}")
                return max_value if val > 0 else -max_value
            return val
        
        result = Risk_Assessment_Result(
            village=village,
            reference_id=str(row['reference_id']),
            village_name=row['village_name'],
            village_code=row['village_code'],
            point_id=row.get('point_id'),
            latitude=row.get('latitude'),
            longitude=row.get('longitude'),
            asset_type=asset_type,
            wall_type=row.get('wall_type'),
            roof_type=row.get('roof_type'),
            floor_type=row.get('floor_type'),
            building_length_ft=safe_decimal(row.get('building_length_ft')),
            building_width_ft=safe_decimal(row.get('building_width_ft')),
            building_area_sqft=safe_decimal(row.get('building_area_sqft')),
            house_type_id=house_type_obj,
            house_type_name=row['mapped_house_type'],
            unit_cost=safe_decimal(row['unit_rate_inr']),
            replacement_cost_inr=safe_decimal(row['replacement_cost_inr']),
            # Hazard data
            eq_hazard=safe_decimal(row.get('eq_hazard'), 'hazard'),
            wind_hazard=safe_decimal(row.get('wind_hazard'), 'hazard'),
            flood_hazard=safe_decimal(row.get('flood_hazard'), 'hazard'),
            # MDR data
            flood_hazard_mdr=safe_decimal(row.get('flood_hazard_mdr'), 'mdr'),
            eq_hazard_mdr=safe_decimal(row.get('eq_hazard_mdr'), 'mdr'),
            wind_hazard_mdr=safe_decimal(row.get('wind_hazard_mdr'), 'mdr'),
            # Loss data
            flood_loss=safe_decimal(row.get('flood_loss'), 'loss'),
            eq_loss=safe_decimal(row.get('eq_loss'), 'loss'),
            wind_loss=safe_decimal(row.get('wind_loss'), 'loss')
        )
        results.append(result)
        
        # Batch insert when batch size reached
        if len(results) >= batch_size:
            Risk_Assessment_Result.objects.bulk_create(results, batch_size=batch_size)
            results = []
    
    # Insert remaining results
    if results:
        Risk_Assessment_Result.objects.bulk_create(results, batch_size=batch_size)

def export_to_csv(df, filename, village_id):
    """Export dataframe to CSV"""
    output_dir = os.path.join(settings.MEDIA_ROOT, 'risk_assessment')
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, f"{filename}_village_{village_id}.csv")
    df.to_csv(filepath, index=False)
    return filepath

def run_risk_assessment_pipeline(village_id):
    """Main pipeline function with debug logging"""
    print(f"DEBUG: Pipeline started for village_id: {village_id}")
    results = {}
    
    try:
        print("DEBUG: Processing household data")
        household_df, error = process_household_data(village_id)
        if household_df is not None:
            print(f"DEBUG: Household data processed successfully, {len(household_df)} records")
            csv_path = export_to_csv(household_df, 'household_risk_assessment', village_id)
            results['household'] = {'status': 'success', 'csv_path': csv_path, 'records': len(household_df)}
        else:
            print(f"DEBUG: No household data found: {error}")
            results['household'] = {'status': 'no_data', 'message': error}
    except Exception as e:
        print(f"DEBUG: Household processing error: {str(e)}")
        results['household'] = {'status': 'error', 'message': str(e)}
    
    try:
        print("DEBUG: Processing commercial data")
        commercial_df, error = process_commercial_data(village_id)
        if commercial_df is not None:
            print(f"DEBUG: Commercial data processed successfully, {len(commercial_df)} records")
            csv_path = export_to_csv(commercial_df, 'commercial_risk_assessment', village_id)
            results['commercial'] = {'status': 'success', 'csv_path': csv_path, 'records': len(commercial_df)}
        else:
            print(f"DEBUG: No commercial data found: {error}")
            results['commercial'] = {'status': 'no_data', 'message': error}
    except Exception as e:
        print(f"DEBUG: Commercial processing error: {str(e)}")
        results['commercial'] = {'status': 'error', 'message': str(e)}
    
    try:
        print("DEBUG: Processing critical facility data")
        facility_df, error = process_critical_facility_data(village_id)
        if facility_df is not None:
            print(f"DEBUG: Critical facility data processed successfully, {len(facility_df)} records")
            csv_path = export_to_csv(facility_df, 'critical_facility_risk_assessment', village_id)
            results['critical_facility'] = {'status': 'success', 'csv_path': csv_path, 'records': len(facility_df)}
        else:
            print(f"DEBUG: No critical facility data found: {error}")
            results['critical_facility'] = {'status': 'no_data', 'message': error}
    except Exception as e:
        print(f"DEBUG: Critical facility processing error: {str(e)}")
        results['critical_facility'] = {'status': 'error', 'message': str(e)}
    
    print(f"DEBUG: Pipeline completed with results: {results}")
    return results
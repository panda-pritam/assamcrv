# Risk Assessment Pipeline

## Overview

The Risk Assessment Pipeline calculates potential losses for buildings and infrastructure based on hazard exposure and structural vulnerability. It processes household, commercial, and critical facility data to determine expected damage and financial losses from floods, earthquakes, and wind hazards.

## Core Models and Data Structure

### 1. house_type_combination_mapping
**Location**: `vdmp_progress.models`

Maps building material combinations to standardized house types for vulnerability assessment.

**Purpose**:
- Links wall, roof, and floor material combinations to house types
- Enables consistent vulnerability classification
- Handles data entry variations through fuzzy matching

**Key Fields**:
- `wall_type`: Wall construction material (e.g., "bamboo", "brick", "concrete")
- `roof_type`: Roof material (e.g., "thatch", "tin", "concrete")
- `floor_type`: Floor material (e.g., "mud", "cement", "tiles")
- `combo_key`: Unique combination identifier
- `house_type`: Linked house type for vulnerability curves
- `is_New`: Flag for newly discovered combinations requiring classification

### 2. house_type
**Location**: `vdmp_progress.models`

Defines standardized building types with associated costs and vulnerability characteristics.

**Purpose**:
- Stores house type definitions (R1, R2A, R3B, etc.)
- Provides unit construction costs for replacement cost calculations
- Links to vulnerability curves in MDR tables

**Key Fields**:
- `house_type_id`: Unique identifier
- `house_type`: Type name (e.g., "R1 Bamboo House", "R5A Tin House")
- `per_unit_cost`: Construction cost per square foot (INR)

### 3. MDR (Mean Damage Ratio) Tables

Three separate tables store vulnerability curves for different hazards:

#### flood_MDR_table
- `house_type_id`: Building type
- `flood_depth_m`: Flood depth in meters
- `MDR_value`: Expected damage ratio (0.0 = no damage, 1.0 = total loss)

#### EQ_MDR_table  
- `house_type_id`: Building type
- `PGA_g`: Peak Ground Acceleration in 'g' units
- `MDR_value`: Expected damage ratio

#### wind_MDR_table
- `house_type_id`: Building type
- `wind_speed_kmph`: Wind speed in km/h
- `MDR_value`: Expected damage ratio

## Risk Calculation Process

### Step 1: Hazard Value Extraction

**Function**: `process_hazards_and_losses(df, district_id)`

**Hazard Sources**:
1. **Earthquake Hazard**: Extracted from raster files using GDAL
   - Source: District-specific or state-level EQ raster files
   - Unit: Peak Ground Acceleration (PGA) in 'g'
   - Expected Range: 0.27-0.49g

2. **Wind Hazard**: Extracted from raster files using GDAL
   - Source: District-specific or state-level wind raster files
   - Unit: Wind speed in km/h
   - Expected Range: 19-50 km/h

3. **Flood Hazard**: From survey data
   - Source: `flood_depth_m` field from survey
   - Unit: Flood depth in meters
   - Range: 0-10+ meters

**Raster Value Extraction**:
**Function**: `sample_raster_values_gdal(path, lats, lons, default_value)`

Uses GDAL with bilinear interpolation for precise value extraction:
- Transforms coordinates from WGS84 to raster CRS
- Performs bilinear interpolation between pixel values
- Handles coordinate system transformations automatically
- Provides fallback values for failed extractions

### Step 2: Vulnerability Assessment

**Function**: `map_mdr_from_db(df, hazard_col, mdr_model, hazard_field)`

**Process**:
1. **House Type Mapping**: Links buildings to vulnerability curves
2. **Linear Interpolation**: Calculates MDR for actual hazard values
3. **Extrapolation Handling**: Uses boundary values for out-of-range hazards

**Example Calculation**:
```
Survey Data: 1.5m flood depth, R1 Bamboo House
Database: 1.0m → 0.3 MDR, 2.0m → 0.7 MDR
Interpolation: 0.3 + (1.5-1.0)/(2.0-1.0) × (0.7-0.3) = 0.5 MDR
Result: 50% expected damage
```

### Step 3: Loss Calculation

**Formula**: `Loss = MDR × Replacement Cost`

**Replacement Cost Calculation**:
```
Replacement Cost = Building Area (sqft) × Unit Cost (INR/sqft)
```

**Example**:
```
Building: 1000 sqft, R5A Tin House (₹1200/sqft)
Replacement Cost: 1000 × 1200 = ₹1,200,000
Flood MDR: 0.3 (30% damage)
Expected Loss: 0.3 × ₹1,200,000 = ₹360,000
```

## Building Material Mapping

### Function: `get_house_type_mapping(wall, roof, floor)`

**Mapping Strategy**:
1. **Exact Match**: Direct material combination lookup
2. **Partial Match**: Fuzzy matching for data entry variations
3. **Fallback**: "Other / Unknown" for unmapped combinations

**Example Mappings**:
- Bamboo + Thatch + Mud → R4 Bamboo House
- Brick + Tin + Cement → R5A Tin House  
- Concrete + Concrete + Tiles → R1 Concrete House

**Unmapped Combination Handling**:
- Automatically saves new combinations to database
- Flags with `is_New=True` for manual classification
- Continues processing with default values

## Asset Type Processing

### 1. Household Survey Processing
**Function**: `process_household_data(village_id)`

**Data Sources**: `HouseholdSurvey` model
**Key Fields**:
- Building dimensions: `building_length_feet`, `building_width_feet`, `building_area_sqft`
- Materials: `wall_type`, `roof_type`, `floor_type`
- Hazard data: `flood_depth_m`
- Location: `latitude`, `longitude`

### 2. Commercial Data Processing  
**Function**: `process_commercial_data(village_id)`

**Data Sources**: `Commercial` model
**Key Fields**:
- Room dimensions: `average_room_length_ft`, `average_room_width_ft`
- Materials: `wall_type`, `roof_type`, `floor_type`
- Hazard data: `flood_depth_m`

### 3. Critical Facility Processing
**Function**: `process_critical_facility_data(village_id)`

**Data Sources**: `Critical_Facility` model
**Similar processing to commercial with facility-specific considerations**

## Data Validation and Quality Control

### Building Dimension Validation
**Function**: `validate_building_dimensions(length, width, area)`

**Validation Rules**:
- Maximum length: 1000 ft (≈300m)
- Maximum width: 1000 ft (≈300m)  
- Maximum area: 100,000 sqft (≈9,300 sqm)
- Sets unrealistic values to 0 to prevent database overflow
- Recalculates area from length/width if area is missing

### Data Quality Checks
- Coordinate validation for raster extraction
- MDR value bounds checking (0.0 to 1.0)
- Replacement cost overflow prevention
- Missing data handling with appropriate defaults

## Results Storage

### Risk_Assessment_Result Model
**Function**: `save_risk_results(df, village_id, asset_type)`

**Stored Data**:
- **Building Information**: Dimensions, materials, house type
- **Hazard Values**: EQ, wind, flood intensities
- **Vulnerability**: MDR values for each hazard
- **Loss Estimates**: Expected financial losses
- **Metadata**: Village, coordinates, asset type

**Optimization Features**:
- Batch processing (500 records per batch)
- Decimal field overflow protection
- Existing data cleanup before new inserts

## Pipeline Execution

### Main Function: `run_risk_assessment_pipeline(village_id, model_name)`

**Supported Model Types**:
- `'household'`: Process household survey data
- `'commercial'`: Process commercial building data  
- `'critical'`: Process critical facility data

**Execution Flow**:
1. Data extraction from appropriate model
2. Material mapping and house type assignment
3. Building dimension validation
4. Hazard value extraction from rasters
5. MDR calculation through interpolation
6. Loss calculation and validation
7. Results storage in database

**Error Handling**:
- Graceful handling of missing data
- Detailed logging for troubleshooting
- Partial success reporting
- Automatic fallback values

## Configuration Requirements

### Geospatial Data
- **EQ Raster Files**: District-level or state-level earthquake hazard maps
- **Wind Raster Files**: District-level or state-level wind hazard maps
- **Coordinate System**: WGS84 (EPSG:4326) input, automatic CRS transformation

### Database Configuration
- Complete house type definitions with unit costs
- Comprehensive material combination mappings
- Populated MDR tables for all house types and hazards
- Raster file path configuration in database

### Performance Considerations
- GDAL-based raster processing for efficiency
- Batch database operations
- Memory-efficient DataFrame processing
- Optimized interpolation algorithms

## Usage Example

```python
# Run risk assessment for specific asset type
results = run_risk_assessment_pipeline(
    village_id=123,
    model_name='household'
)

# Results structure
{
    'household': {
        'status': 'success',
        'records': 150
    }
}
```

## Output and Reporting

### Generated Data
- **Hazard Exposure**: Precise hazard values for each building
- **Vulnerability Assessment**: MDR values based on building type
- **Loss Estimates**: Expected financial losses in INR
- **Risk Profiles**: Complete risk assessment per building

### Export Capabilities
- CSV export for verification and analysis
- Database storage for dashboard integration
- Batch processing results tracking

This pipeline provides comprehensive risk assessment capabilities, enabling evidence-based disaster risk management and loss estimation for insurance, planning, and mitigation purposes.
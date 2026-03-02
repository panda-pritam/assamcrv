# Data Pipeline: Mobile DB to Portal DB

## Overview

This document describes the data pipeline process that transfers survey data from the mobile database to the portal database. The pipeline handles multiple survey types including household surveys, commercial surveys, physical vulnerability surveys, and others category data.

## Core Models

### 1. district_village_mapping
**Location**: `village_profile.models`

This table stores the mapping between mobile DB village/district IDs and portal DB IDs.

**Purpose**: 
- Maps mobile DB village ID to portal DB village ID
- Maps mobile DB district ID to portal DB district ID
- Essential for data synchronization between mobile and portal databases

**Key Fields**:
- `mobile_village_id`: Village ID from mobile database
- `portal_village_id`: Corresponding village ID in portal database
- `mobile_district_id`: District ID from mobile database
- `portal_district_id`: Corresponding district ID in portal database

### 2. AttributeMapping
**Location**: `vdmp_dashboard.models`

This table defines the field mappings and data transformation rules for each model.

**Purpose**:
- Maps portal DB model fields to mobile DB attributes (questions)
- Defines calculated fields and their computation logic
- Stores tab information for SQL generation
- Controls data transformation rules

**Key Fields**:
- `model_name`: Target portal DB model name
- `field_name`: Portal DB field name
- `mobile_db_attribute_id`: Source mobile DB attribute/question ID
- `is_calculated`: Boolean indicating if field value comes from cleaning functions
- `tab_id`: Mobile DB tab identifier
- `tab_name`: Mobile DB tab name
- `is_active`: Controls if mapping is currently used

## Pipeline Trigger

### Entry Point
**Function**: `update_vdmp_activity_status(request, status_id)`
**Location**: `assam_crv\vdmp_progress\views.py`

**Trigger Conditions**:
- When survey status is marked as "complete"
- Supported survey types:
  - Household Survey
  - Physical Vulnerability Survey
  - Commercial Survey
  - Critical Facility Survey
  - Others (Transformer, Electric Pole, etc.)

## Pipeline Process Flow

### 1. Data Extraction
**Function**: `process_survey_data()`
**Location**: `assam_crv\vdmp_progress\data_pipeline.py`

**Parameters**:
- `activity_name`: Type of survey (household, commercial, etc.)
- `village_id`: Portal DB village ID
- `district_id`: Portal DB district ID
- `mobile_village_id`: Mobile DB village ID
- `district_code`: District code
- `village_code`: Village code
- `activity_status`: Survey completion status
- `district_name`: District name
- `village_name`: Village name

**Process**:
1. Connects to mobile database using configuration
2. Generates dynamic SQL query based on survey type
3. Executes query and retrieves data as DataFrame
4. Validates data existence

### 2. Dynamic SQL Generation
**Function**: `get_dynamic_sql_script(village_id, model_name='HouseholdSurvey')`
**Location**: `assam_crv\vdmp_progress\dynamic_sql.py`

**Purpose**:
- Generates SQL queries dynamically based on AttributeMapping configuration
- Handles different survey types with appropriate JOIN conditions
- Filters data by village_id and active status

**Special Handling**:
- **Others Category**: Uses separate function `get_others_sql_script()` due to different data structure
- **Asset Type Filtering**: Others data is filtered by `assets_type` field for proper categorization

### 3. Data Cleaning and Enhancement
**Function**: `clean_survey_data(df, district_code, village_code, activity_type="household", village_id=None)`
**Location**: `assam_crv\vdmp_progress\cleaning_utils.py`

**Key Processes**:
1. **Flood Depth Calculation**: Extracts flood depth values from raster files based on coordinates
2. **Erosion Value Calculation**: Determines erosion values and classifications
3. **Data Validation**: Validates coordinates, required fields, and data types
4. **Field Standardization**: Standardizes field names and formats
5. **Calculated Fields**: Computes derived values like building areas, loss calculations

**Important Enhancements**:
- Flood depth mapping from geospatial raster data
- Erosion classification and buffer calculations
- Building dimension calculations (area, volume)
- Loss estimation for agriculture and livelihood

### 4. Data Persistence
**Function**: `save_to_model_dynamic(df, village_id, district_code, model_name)`
**Location**: `assam_crv\vdmp_progress\data_pipeline.py`

**Process**:
1. Dynamically identifies target model class
2. Retrieves field mappings from AttributeMapping
3. Transforms DataFrame records to model instances
4. Handles create/update operations using `update_or_create()`
5. Tracks success/error counts

**Special Cases**:
- **Household Survey**: Includes building dimensions and flood-related fields
- **Others Category**: Routes data to appropriate models (Transformer, ElectricPole) based on `assets_type`

## Others Category Handling

The "Others" category requires special handling due to its multi-entity nature:

**Supported Asset Types**:
- Transformer
- Electric Pole
- Other infrastructure assets

**Process Flow**:
1. Extract all others data using `get_others_sql_script()`
2. Apply cleaning with erosion calculations
3. Filter by `assets_type` field
4. Route to appropriate model:
   - Transformer data → `Transformer` model
   - Electric pole data → `ElectricPole` model

**Function**: `save_others_to_models(df, village_id, district_code)`

## Error Handling and Monitoring

### Import Status Tracking
- Each pipeline execution creates an import status record
- Tracks processing time, record counts, and error status
- Provides audit trail for data synchronization

### Error Scenarios
1. **No Data Found**: Raises exception if mobile DB has no data for village
2. **Database Connection Issues**: Handles connection failures gracefully
3. **Model Save Errors**: Tracks and reports individual record failures
4. **Validation Errors**: Logs validation issues without stopping pipeline

### Logging and Debugging
- Comprehensive logging at each pipeline stage
- CSV export for data verification
- Progress tracking for large datasets
- Error details for troubleshooting

## Configuration Requirements

### Database Connections
- Mobile DB configuration in Django settings
- Portal DB as default Django database

### Geospatial Data
- Flood depth raster files
- Erosion classification data
- Coordinate system compatibility

### Model Mappings
- Complete AttributeMapping configuration for each survey type
- Active status management for field mappings
- Tab ID and name configuration for SQL generation

## Performance Considerations

- Batch processing for large datasets
- Progress tracking every 100 records
- Temporary file creation for verification
- Connection pooling for database operations
- Memory-efficient DataFrame operations

## Usage Example

```python
# Trigger pipeline from view
process_survey_data(
    activity_name="household survey",
    village_id=123,
    district_id=45,
    mobile_village_id=35,
    district_code="AS01",
    village_code="V001",
    activity_status="complete",
    district_name="Sample District",
    village_name="Sample Village"
)
```

This pipeline ensures reliable, traceable, and efficient data transfer from mobile data collection to the portal database with comprehensive data enhancement and validation.
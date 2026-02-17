# VDMP Pipeline, Mobile Mapping, Risk Assessment, and VDMP Logic

## Scope
This document describes how mobile survey data is fetched and processed, how mobile DB attributes map to web DB columns, how risk assessment works, and the VDMP progress/dashboard logic.

## 1) Mobile survey data pipeline (fetch and process)

### Trigger points
- VDMP progress status is updated to Completed in `assam_crv/vdmp_progress/views.py` (see `update_vdmp_activity_status`).
- The server checks existing data per activity and village. If data exists, it returns HTTP 409 and the UI can call `delete_and_rerun_pipeline`.
- If no data exists, the activity pipeline runs.

### Common pipeline flow
Implemented in `assam_crv/vdmp_progress/data_pipeline.py`.

1. Resolve village mapping
   - Uses `district_village_mapping` to map web village ID to mobile DB village ID, district code, village code.
2. Generate dynamic SQL
   - Uses `assam_crv/vdmp_progress/dynamic_sql.py:get_dynamic_sql_script`.
   - SQL is built from `vdmp_dashboard.AttributeMapping` to pivot mobile attributes into columns.
3. Fetch data from mobile DB
   - Uses `psycopg2` and `settings.DATABASES['mobile_db']`.
   - Pulls `formdata`, `attributes`, `attributes_option`, `spatialdata`, `villages`.
4. Clean data
   - `cleaning_utils.clean_survey_data` performs type cleanup, normalization, and hazard classification fields.
5. Save to web DB
   - `save_to_model_dynamic` maps the cleaned DataFrame into the Django model using `AttributeMapping`.
   - Uses `update_or_create` keyed by `unique_id` and `form_id`.
6. Track status
   - Writes import results to `tblVDMP_Activity_Import_Status`.

### Activity-specific branches
- Household survey
  - Runs `process_survey_data` for HouseholdSurvey.
  - Triggers `run_risk_assessment_pipeline(village_id, 'household')`.
- Physical vulnerability survey
  - Requires household data to exist.
  - Currently uses `process_survey_data('others', ...)` which splits Transformer and ElectricPole data.
  - Runs risk assessment for commercial and critical.
- Road survey
  - Runs `cleaning_utils.process_road_data_pipeline` for flood and erosion road data.
- Agriculture survey
  - Runs `cleaning_utils.process_all_agriculture_hazards` for flood, erosion, wind, and EQ agriculture layers.
- GIS maps
  - Validates GIS data availability (flood raster per village, wind/eq rasters with fallback, riverbuffer optional).
  - Runs `run_gis_risk_assessment_pipeline`, which:
    - Extracts flood depth and erosion values for household, commercial, critical, transformer, and electric pole.
    - Re-runs risk assessment for household, commercial, and critical.
    - Runs road flood/erosion processing and agriculture hazard processing.

## 2) Mobile DB to web DB attribute mapping

### Mapping model
Defined in `assam_crv/vdmp_dashboard/models.py`:
- `AttributeMapping`
  - `mobile_db_attribute_id`: attribute ID in mobile DB.
  - `attribute_text`: optional text used for ILIKE matching.
  - `alias_name`: web column alias (used as DataFrame column name).
  - `model_name`: target Django model (HouseholdSurvey, Commercial, etc).
  - `tab_id`: mobile DB tab id used in query.
  - `is_active`, `is_calculated`: filter for active mappings.

### How the mapping is used
1. SQL generation
   - `get_dynamic_sql_script` reads active mappings for the target model.
   - For each mapping, it generates a SQL expression:
     - If `attribute_text` is set: `CASE WHEN a.attribute_name ILIKE '%text%' THEN av.value`.
     - Else: `CASE WHEN a.id = mobile_db_attribute_id THEN av.value`.
2. Query output
   - Each `alias_name` becomes a column in the query result.
   - Multi-select widgets (widget_id 2 or 4) use `attributes_option` to expand option values.
   - Media widgets (widget_id 10) generate media URLs.
3. Save to web DB
   - `save_to_model_dynamic` reads active mappings again and assigns `alias_name` values to the model fields.
   - This keeps mobile and web schemas decoupled; only mapping records need updates when attributes change.

### Special case: Others tab
- `get_others_sql_script` uses `build_dynamic_selects_from_mappings('others')` with a fixed tab id (14).
- Results are split into Transformer and ElectricPole models by `assets_type`.

### Mapping utilities
Management commands exist for seeding or syncing mapping records:
- `assam_crv/vdmp_dashboard/management/commands/import_csv.py`
- `assam_crv/vdmp_dashboard/management/commands/populate_mappings.py`
- `assam_crv/vdmp_dashboard/management/commands/sync_attributes.py`

## 3) Risk assessment pipeline

Implemented in `assam_crv/vdmp_progress/risk_assessment_pipeline.py`.

### Inputs
- Survey data from HouseholdSurvey, Commercial, Critical_Facility.
- House type and cost mappings from:
  - `house_type_combination_mapping`
  - `house_type`
- MDR tables:
  - `flood_MDR_table`, `EQ_MDR_table`, `wind_MDR_table`
- Hazard rasters:
  - district raster files from `layers` models (fallback to `MEDIA_ROOT/pipeline_data`).

### Steps
1. Extract survey rows by asset type.
2. Map building materials (wall, roof, floor) to house types and unit costs.
3. Validate building dimensions to avoid unrealistic values.
4. Compute replacement cost = area * unit cost.
5. Extract hazards:
   - EQ hazard from raster (PGA).
   - Wind hazard from raster.
   - Flood hazard from survey flood depth.
6. Map hazards to MDR using linear interpolation by house type.
7. Compute losses: `loss = MDR * replacement_cost`.
8. Save to `Risk_Assessment_Result` (clears prior results for the same village and asset type).

### Outputs
- `Risk_Assessment_Result` rows per asset and per hazard.
- Used by VDMP dashboards and reports for exposure and loss views.

## 4) VDMP section logic

### VDMP Progress (activity completion)
- Views in `assam_crv/vdmp_progress/views.py`.
- Admin updates activity status to Completed, which triggers the pipeline.
- If data exists, HTTP 409 is returned and the UI can call `delete_and_rerun_pipeline` to remove old data.
- Pipelines update activity import status and then save the VDMP activity status.

### GIS Maps completion behavior
- When activity name contains `gis maps` and status is set to Completed:
  - `validate_gis_data_availability` runs; missing required rasters returns HTTP 400 and status is not saved.
  - River buffer/erosion gaps are warnings only; pipeline continues.
  - On success, `run_gis_risk_assessment_pipeline` executes and status is saved with a success response.

### GIS Maps pipeline flow
```mermaid
flowchart TD
    A[VDMP status set to Completed for GIS Maps] --> B[validate_gis_data_availability]
    B -->|Errors: missing flood/wind/eq raster| C[HTTP 400; status not saved]
    B -->|Warnings only (river buffer optional)| D[run_gis_risk_assessment_pipeline]
    D --> E[Extract flood depth + erosion for survey models]
    E --> F[Run risk assessment: household/commercial/critical]
    F --> G[Process road flood + erosion]
    G --> H[Process agriculture hazards]
    H --> I[Save status success response]
```

### VDMP Dashboard (survey uploads and reports)
- Views in `assam_crv/vdmp_dashboard/views.py`.
- `/api/upload_data_vdmp` supports manual bulk uploads for survey and GIS data.
- Uploads are stored in dedicated models (HouseholdSurvey, Commercial, Critical_Facility, BridgeSurvey, Transformer, ElectricPole, VillageRoadInfo, Risk_Assesment, etc).
- Summary endpoints aggregate village-level metrics for dashboards and reports.

## Reference files
- `assam_crv/vdmp_progress/views.py`
- `assam_crv/vdmp_progress/data_pipeline.py`
- `assam_crv/vdmp_progress/dynamic_sql.py`
- `assam_crv/vdmp_progress/risk_assessment_pipeline.py`
- `assam_crv/vdmp_dashboard/models.py`
- `assam_crv/vdmp_dashboard/views.py`
- `assam_crv/village_profile/models.py`

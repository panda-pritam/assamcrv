# Assam CRV Project Overview

## Purpose
Assam CRV (Community Risk and Vulnerability) supports the Assam State Disaster Management Authority with village-level risk profiling, surveys, and progress tracking. It consolidates administrative hierarchy, survey data, GIS layers, and operational monitoring into a single web platform.

## Primary Users
- Admin/ASDMA: Manage master data, activities, and system-wide monitoring.
- District/Circle/GP/Village users: View and update data within assigned jurisdiction.

## High-Level Flow
1. Users log in and access modules based on role and location.
2. Administrative hierarchy (district -> circle -> gram panchayat -> village) drives filtering.
3. Survey and activity status data are collected and stored per village.
4. VDMP progress and dashboard views aggregate data for charts and reports.
5. GIS layers and GeoServer data provide spatial context.

## Core Modules
- accounts: authentication, users, roles, departments, module permissions.
- village_profile: admin hierarchy and village master data.
- vdmp_progress: VDMP activities and progress status per village.
- vdmp_dashboard: survey data, bulk uploads, risk assessment, and reports.
- layers: GeoServer layer configuration for map views.
- field_images: field documentation images by village and category.
- training: training activity master and status tracking.
- rescue_equipment: equipment master and village availability status.
- task_force: village task force team records.
- shapefiles: unmanaged PostGIS spatial datasets.

## Stepwise Flows by Module

### accounts (Authentication and User Management)
1. User logs in via `/login/` and session is created.
2. Profile page (`/profile/`) shows user and location data.
3. Admin can create/update users via `/api/register_user/` and `/api/users/<id>/update/`.
4. User roles and departments determine module access.
5. `tblModulePermission` controls which modules are visible.

### village_profile (Administrative Hierarchy)
1. Admin uses CRUD APIs to create districts, circles, GPs, and villages.
2. Users and data records link to `tblDistrict`, `tblCircle`, `tblGramPanchayat`, `tblVillage`.
3. Location filters use `/api/get_districts`, `/api/get_circles`, `/api/get_gram_panchayats`, `/api/get_villages`.
4. Bulk import uses CSV endpoint `/api/add_district_crlcle_gp_vill_by_csv`.

### vdmp_progress (Activity Tracking)
1. Admin page loads status data from `GET /api/admin_get_vdmp_activity_status`.
2. Admin edits a row and sets Status = Completed.
3. Frontend calls `PATCH /api/update_vdmp_activity_status/<id>/`.
4. Backend checks if data already exists for the activity and village:
   - Household survey -> `HouseholdSurvey` rows.
   - Physical vulnerability -> `Commercial`, `Critical_Facility`, `BridgeSurvey` rows.
   - Road -> `VillageRoadInfo` or `VillageRoadInfoErosion` rows.
5. If data exists, backend returns 409 and the UI prompts to delete and re-run.
6. If user confirms, frontend calls `POST /api/delete_and_rerun_pipeline/<id>/` to delete old data,
   then re-calls the update API to trigger a fresh import.

#### Household Survey Import
1. Lookup `district_village_mapping` for mobile village id and codes.
2. Connect to `mobile_db` using `settings.DATABASES['mobile_db']`.
3. Execute dynamic SQL for the household survey data.
4. Clean data using `clean_survey_data`.
5. Save into `HouseholdSurvey` and track import status.
6. Run `run_risk_assessment_pipeline(village_id, 'household')`.

#### Physical Vulnerability Survey Import
1. Require household data to exist (otherwise 400 error).
2. Import `Commercial`, `Critical_Facility`, `BridgeSurvey`, and `Others` datasets.
3. Track per-activity import results and totals.
4. Run risk assessment for commercial and critical.

#### Road Survey Import
1. Run road data pipeline for flood/erosion.
2. Save into `VillageRoadInfo` and `VillageRoadInfoErosion`.
3. Update activity status and return success.

### vdmp_dashboard (Survey Data, Reports, Risk)
1. Bulk data upload via `/api/upload_data_vdmp`.
2. Data stored in survey models (household, commercial, critical, transformer, electric pole, bridges).
3. Dashboard endpoints aggregate counts and statistics per village.
4. `GET /api/get_household_summary_data` uses GeoServer WFS for road length calculations.
5. Reports generated via `/api/download_report` using stored survey data.

### training (Training Activities)
1. Admin defines training activities via `/api/create_training_activity`.
2. Status entries created per village via `/api/create_training_activity_status`.
3. Admin updates status, which updates `tbl_Training_Activities_Status`.
4. Chart data computed via `/api/training_chart_data`.

### rescue_equipment (Equipment Availability)
1. Admin defines equipment types (`tbl_Rescue_Equipment`).
2. Village equipment status created/updated per village via status endpoints.
3. Summary and chart data retrieved via `/api/rescue_equipment_chart_data/`.

### task_force (Village Team Records)
1. Task force members created via `/api/taskforce/` (POST).
2. Members associated with a village and team type.
3. Lists and stats available via `/api/taskforce/` and `/api/taskforce_chart_data`.

### field_images (Field Documentation)
1. Users upload images via `/api/field-images/`.
2. Images are linked to villages and categories.
3. Limits: max 2 images per category per village.

### layers (GeoServer Layer Config)
1. Admin defines GeoServer layers in `GeoserverLayers` table.
2. Client calls `/api/getLayers/` to fetch layer metadata.
3. Map UI uses returned workspace/layer names to render WMS/WFS layers.

### shapefiles (Spatial Data)
1. PostGIS contains shapefile-derived tables (unmanaged by Django).
2. These are used for map overlays and exposure analysis.
3. Accessed through GeoServer WMS/WFS services.

## GIS and GeoServer
- GeoServer provides map layers (WMS/WFS) for spatial overlays.
- layers app reads GeoServer layer config from GeoserverLayers model.
- vdmp_dashboard uses GeoServer WFS for road length statistics.

## Key Pages
- /: Main dashboard (summary charts).
- /vdmp_progress/: VDMP progress dashboard (charts and detailed table).
- /administrator/vdmp_progress: Admin management for VDMP activities and status.
- /vdmp_dashboard: Village risk and survey dashboard.
- /map/: GIS map view with GeoServer layers.

## Database Overview (Key Tables)
- accounts_tbluser: user and role assignment.
- village_profile_tbldistrict, tblcircle, tblgrampanchayat, tblvillage.
- vdmp_progress_tblvdmp_activity, vdmp_progress_tblvdmp_activity_status.
- vdmp_dashboard_*: HouseholdSurvey, Commercial, Critical_Facility, BridgeSurvey, Transformer, ElectricPole, VillageRoadInfo, Risk_Assessment.
- field_images_fieldimage: village image uploads.

## Configuration
- Environment variables in assam_crv/.env for Django and DB connections.
- Two DB connections:
  - default: main PostGIS DB
  - mobile_db: mobile survey source DB
- GIS libs (GDAL/GEOS) are required for GeoDjango.

## Typical Local Run
- Activate conda env with GDAL/GEOS.
- Install dependencies from req.txt.
- Run migrations and start server:
  - python .\assam_crv\manage.py migrate
  - python .\assam_crv\manage.py runserver

## Notes and Risks
- Duplicate migration for geojson_file exists in village_profile; use fake migration if needed.
- Mobile DB access is required for automated imports in VDMP progress.
- GeoServer must be reachable for map layers and some dashboard stats.

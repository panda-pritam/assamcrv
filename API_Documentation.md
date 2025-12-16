# Assam CRV API Documentation

## Overview
This document provides a comprehensive list of all APIs available in the Assam State Disaster Management Authority (ASDMA) Community Risk and Vulnerability (CRV) system. The system uses Django REST Framework and includes both REST APIs and traditional Django views.

---

## API Categories

### 1. **Authentication & User Management APIs** (`accounts` app)

#### User Authentication
- **POST** `/login/` - User login
- **GET** `/logout/` - User logout
- **GET** `/profile/` - Get user profile page

#### User Management APIs
- **POST** `/api/register_user/` - Register new user
- **GET** `/api/users_list/` - List all users
- **GET** `/api/users/<int:user_id>/` - Get specific user profile
- **PUT** `/api/users/<int:user_id>/update/` - Update user profile
- **DELETE** `/api/users/<int:user_id>/delete/` - Delete user
- **POST** `/api/change-password/` - Change user password
- **POST** `/api/update-profile/` - Update current user profile

#### Department Management APIs
- **POST** `/api/departments/create/` - Create new department
- **PUT** `/api/departments/<int:department_id>/update/` - Update department
- **DELETE** `/api/departments/<int:department_id>/delete/` - Delete department
- **GET** `/api/departments/` - List all departments
- **GET** `/api/get_modules_permission/` - Get module permissions

---

### 2. **Administrative Hierarchy APIs** (`village_profile` app)

#### Location Data APIs
- **GET** `/api/get_districts` - Get districts (filtered)
- **GET** `/api/get_circles` - Get circles (filtered)
- **GET** `/api/get_gram_panchayats` - Get gram panchayats (filtered)
- **GET** `/api/get_villages` - Get villages (filtered)
- **GET** `/api/villages_by_district` - Get villages by district

#### Complete Location Lists
- **GET** `/api/get_all_districts` - Get all districts
- **GET** `/api/get_all_villages` - Get all villages
- **GET** `/api/get_all_circles` - Get all circles
- **GET** `/api/get_all_gram_panchayats` - Get all gram panchayats

#### Location Management (CRUD)
- **POST** `/api/create_district` - Create new district
- **POST** `/api/create_circle` - Create new circle
- **POST** `/api/create_gram_panchayat` - Create new gram panchayat
- **POST** `/api/create_village` - Create new village

- **PUT** `/api/<int:district_id>/update_district` - Update district
- **PUT** `/api/<int:circle_id>/update_circle` - Update circle
- **PUT** `/api/<int:gram_panchayat_id>/update_gram_panchayat` - Update gram panchayat
- **PUT** `/api/<int:village_id>/update_village` - Update village

- **DELETE** `/api/<int:district_id>/delete_district` - Delete district
- **DELETE** `/api/<int:circle_id>/delete_circle` - Delete circle
- **DELETE** `/api/<int:gram_panchayat_id>/delete_gram_panchayat` - Delete gram panchayat
- **DELETE** `/api/<int:village_id>/delete_village` - Delete village

#### Utility APIs
- **POST** `/api/update_locations` - Bulk update locations
- **GET** `/api/get_village_count` - Get village count statistics
- **GET** `/api/get_location_counts` - Get location hierarchy counts
- **POST** `/api/add_district_crlcle_gp_vill_by_csv` - Bulk import via CSV
- **GET** `/api/count_of_villages_with_survey` - Count villages with survey data

---

### 3. **GIS & Mapping APIs** (`layers` app) - **USES GEOSERVER**

#### Map Display
- **GET** `/map/` - Show map page (HTML view)

#### GeoServer Integration APIs
- **GET** `/api/getLayers/` - **Get GeoServer layers configuration**
  - **GeoServer Usage**: Fetches layer metadata from `GeoserverLayers` model
  - **Returns**: Layer titles, workspace names, layer names for map rendering
  - **Purpose**: Configures map layers from GeoServer WMS/WFS services

---

### 4. **Field Documentation APIs** (`field_images` app)

#### Field Images Management (REST API)
- **GET** `/api/field-images/` - List field images
- **POST** `/api/field-images/` - Upload field image
- **GET** `/api/field-images/<int:id>/` - Get specific field image
- **PUT** `/api/field-images/<int:id>/` - Update field image
- **DELETE** `/api/field-images/<int:id>/` - Delete field image

**Features**:
- Image categorization (Livelihood, Infrastructure, etc.)
- Village-wise organization
- Maximum 2 images per category per village
- Multi-language support

---

### 5. **Training Management APIs** (`training` app)

#### Training Activities
- **GET** `/training_activities` - Training activities page (HTML)
- **GET** `/api/get_training_activity_status` - Get training status by village
- **POST** `/api/create_training_activity` - Create new training activity
- **PUT** `/api/update_training_activity/<int:activity_id>/` - Update training activity
- **DELETE** `/api/delete_training_activity/<int:activity_id>/` - Delete training activity

#### Training Status Management
- **POST** `/api/create_training_activity_status` - Create training status
- **PUT** `/api/update_training_activity_status/<int:status_id>/` - Update training status
- **DELETE** `/api/delete_training_activity_status/<int:status_id>/` - Delete training status
- **GET** `/api/administrator/get_training_activity_status` - Admin view of training status

#### Analytics & Utilities
- **GET** `/api/training_chart_data` - Training progress charts data
- **GET** `/api/activities_dropdown` - Training activities dropdown data

---

### 6. **Rescue Equipment APIs** (`rescue_equipment` app)

#### Equipment Management
- **GET** `/rescue_equipment` - Rescue equipment page (HTML)
- **GET** `/api/get_rescue_equipment_status` - Get equipment status by village
- **GET** `/api/admin_get_rescue_equipment_status` - Admin view of equipment status

#### Equipment Master Data (CRUD)
- **POST** `/api/create_rescue_equipment/` - Create new equipment type
- **GET** `/api/get_rescue_equipment/<int:equipment_id>/` - Get specific equipment
- **GET** `/api/get_all_rescue_equipments/` - Get all equipment types
- **PUT** `/api/update_rescue_equipment/<int:equipment_id>/` - Update equipment
- **DELETE** `/api/delete_rescue_equipment/<int:equipment_id>/` - Delete equipment

#### Equipment Status Management
- **POST** `/api/create_rescue_equipment_status/` - Create equipment status
- **PUT** `/api/update_rescue_equipment_status/<int:status_id>/` - Update equipment status
- **DELETE** `/api/delete_rescue_equipment_status/<int:status_id>/` - Delete equipment status

#### Analytics & Utilities
- **GET** `/api/dropdown_rescue_equipment/` - Equipment dropdown data
- **GET** `/api/rescue_equipment_chart_data/` - Equipment charts data
- **GET** `/api/equipments_dropdown/` - Equipment types dropdown

---

### 7. **Task Force Management APIs** (`task_force` app)

#### Task Force Management (REST API)
- **GET** `/task_force/` - Task force page (HTML)
- **GET** `/api/taskforce/` - List task force members
- **POST** `/api/taskforce/` - Create task force member
- **GET** `/api/taskforce/<int:id>/` - Get specific task force member
- **PUT** `/api/taskforce/<int:id>/` - Update task force member
- **DELETE** `/api/taskforce/<int:id>/` - Delete task force member

#### Analytics & Utilities
- **GET** `/api/taskforce_chart_data` - Task force statistics
- **GET** `/api/team_types_dropdown/` - Team types dropdown data

---

### 8. **VDMP Progress APIs** (`vdmp_progress` app)

#### VDMP Progress Management
- **GET** `/vdmp_progress/` - VDMP progress page (HTML)
- **GET** `/api/get_vdmp_activity_status_data` - Get VDMP activity status data
- **GET** `/api/vdmp_activity_status` - Get VDMP activity status
- **GET** `/api/admin_get_vdmp_activity_status` - Admin view of VDMP status

#### VDMP Activity Management (CRUD)
- **POST** `/api/create_vdmp_activity` - Create VDMP activity
- **PUT** `/api/update_vdmp_activity/<int:activity_id>/` - Update VDMP activity
- **DELETE** `/api/delete_vdmp_activity/<int:activity_id>/` - Delete VDMP activity

#### VDMP Status Management
- **PUT** `/api/update_vdmp_activity_status/<int:status_id>/` - Update activity status
- **DELETE** `/api/delete_vdmp_activity_status/<int:status_id>/` - Delete activity status
- **GET** `/api/dropdown_vdmp_activity` - VDMP activities dropdown

---

### 9. **VDMP Dashboard APIs** (`vdmp_dashboard` app) - **USES GEOSERVER**

#### Dashboard Views
- **GET** `/vdmp_dashboard` - VDMP dashboard page (HTML)

#### Data Management APIs
- **POST** `/api/upload_data_vdmp` - **Bulk upload survey data**
  - **Supported Types**: household, transformer, critical_facility, commercial, electric_poles, etc.
  - **File Formats**: CSV, Excel
  - **Features**: Create/Update existing records, validation, error reporting

- **POST** `/api/delete_vdmp_data` - Delete VDMP data by village and type

#### Analytics & Reporting APIs - **USES GEOSERVER**
- **GET** `/api/get_household_summary_data` - **Comprehensive village statistics**
  - **GeoServer Usage**: Fetches road network data via WFS service
  - **WFS Endpoint**: `http://localhost:8080/geoserver/assam/ows`
  - **Layer**: `assam:road_network`
  - **Purpose**: Calculates total road length for infrastructure statistics
  - **Returns**: Demographics, housing, infrastructure, vulnerability data

#### Report Generation
- **GET** `/report` - Generate PDF report (HTML view)
- **GET** `/api/download_report` - Download village VDMP report (PDF)
- **GET** `/api/download_excels_format` - Download Excel templates (ZIP)

---

### 10. **Dashboard & Analytics APIs** (`dashboard` app)

#### Main Dashboard
- **GET** `/` - Home dashboard page (HTML)
- **GET** `/api/dashboard_chart_data/` - Dashboard statistics and charts data

---

## GeoServer Integration Summary

The system integrates with GeoServer for spatial data management and analysis:

### **APIs Using GeoServer:**

1. **`/api/getLayers/` (layers app)**
   - **Purpose**: Map layer configuration
   - **GeoServer Component**: Layer metadata management
   - **Data Source**: `GeoserverLayers` model

2. **`/api/get_household_summary_data` (vdmp_dashboard app)**
   - **Purpose**: Infrastructure statistics calculation
   - **GeoServer Component**: WFS (Web Feature Service)
   - **Service URL**: `http://localhost:8080/geoserver/assam/ows`
   - **Layer**: `assam:road_network`
   - **Operation**: Spatial query for road length calculation
   - **CQL Filters**: Village-based spatial filtering

### **Spatial Data Models (PostGIS):**
- `ShapefileElectricPole` - Electric pole locations
- `ShapefileTransformer` - Transformer locations  
- `PraBoundary` - Village boundary polygons
- `ExposureRiver` - River exposure analysis
- `ExposureRoadVillage` - Road exposure analysis

### **GeoServer Configuration:**
- **Database**: PostGIS (PostgreSQL with spatial extensions)
- **Workspace**: `assam`
- **SRID**: 4326 (WGS84)
- **Services**: WMS, WFS
- **Authentication**: Basic (configured in settings)

---

## API Response Formats

### **Success Response Format:**
```json
{
    "status": "success",
    "data": {...},
    "message": "Operation completed successfully"
}
```

### **Error Response Format:**
```json
{
    "status": "error",
    "error": "Error description",
    "details": {...}
}
```

### **Pagination Format (for list APIs):**
```json
{
    "count": 100,
    "next": "http://example.com/api/endpoint/?page=2",
    "previous": null,
    "results": [...]
}
```

---

## Authentication & Permissions

### **Authentication Methods:**
- Session-based authentication (Django sessions)
- Login required for most APIs
- User location-based filtering

### **Permission Levels:**
- **Admin Users**: Full CRUD access to all data
- **District Users**: Access to district-level data
- **Circle Users**: Access to circle-level data
- **Village Users**: Access to village-level data

### **Location-based Filtering:**
APIs automatically filter data based on user's assigned location:
- District → Circle → Gram Panchayat → Village hierarchy
- Users can only access data within their jurisdiction

---

## File Upload APIs

### **Supported File Types:**
- **Images**: JPG, PNG (field_images app)
- **Documents**: PDF (VDMP reports)
- **Data Files**: CSV, Excel (bulk uploads)

### **Upload Endpoints:**
- `/api/field-images/` - Field image uploads
- `/api/upload_data_vdmp` - Bulk survey data uploads

### **File Storage:**
- **Media Files**: Stored in `/media/` directory
- **Field Images**: `/media/field_images/`
- **Maps**: `/media/maps/`

---

## Bulk Operations

### **Bulk Upload APIs:**
- `/api/upload_data_vdmp` - Survey data (CSV/Excel)
- `/api/add_district_crlcle_gp_vill_by_csv` - Administrative data (CSV)

### **Bulk Download APIs:**
- `/api/download_excels_format` - Excel templates (ZIP)
- `/api/download_report` - PDF reports

### **Supported Data Types for Bulk Upload:**
- household, transformer, critical_facility
- commercial, electric_poles, bridge_survey
- villagesOfAllTheDistricts, road_flood, road_erosion
- risk_assessment

---

## Real-time Features

### **Auto-update Fields:**
- `last_update` - Automatically updated on record changes
- `updated_by` - Tracks user who made changes
- `upload_datetime` - File upload timestamps

### **Status Tracking:**
- Training activities: Completed, Scheduled
- VDMP activities: Completed, In Progress, Not Started
- Equipment status: Count tracking with timestamps

---

## Multi-language Support

### **Supported Languages:**
- English (en)
- Assamese (as)
- Bengali (bn)
- Bodo (brx)

### **Multi-language Fields:**
Most models include language variants:
- `name` (English)
- `name_as` (Assamese)
- `name_bn` (Bengali)

### **Translation APIs:**
- Automatic language detection based on user preferences
- `translated()` utility function for dynamic language selection
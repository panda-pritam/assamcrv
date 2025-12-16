# Assam CRV Database Schema Documentation

## Overview
This document provides a comprehensive overview of the database schema for the Assam State Disaster Management Authority (ASDMA) Community Risk and Vulnerability (CRV) system. The system is built using Django with PostGIS for spatial data management.

---

## Apps and Models

### 1. **accounts** App - User Management & Authentication

#### tblRoles
- **Purpose**: Defines user roles in the system
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=255) - Role name in English
  - `name_bn` (CharField, max_length=255, nullable) - Role name in Bengali
  - `name_as` (CharField, max_length=255, nullable) - Role name in Assamese
  - `details` (TextField, nullable) - Role description

#### tblDepartment
- **Purpose**: Manages government departments
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=255) - Department name in English
  - `name_bn` (CharField, max_length=255, nullable) - Department name in Bengali
  - `name_as` (CharField, max_length=255, nullable) - Department name in Assamese
  - `details` (TextField, nullable) - Department description

#### tblUser (Custom User Model)
- **Purpose**: Extended user model with location and role information
- **Extends**: AbstractUser
- **Fields**:
  - All AbstractUser fields (username, password, email, etc.)
  - `email` (EmailField, unique=True)
  - `mobile` (BigIntegerField, nullable)
  - `district` (ForeignKey to tblDistrict, nullable)
  - `gram_panchayat` (ForeignKey to tblGramPanchayat, nullable)
  - `circle` (ForeignKey to tblCircle, nullable)
  - `village` (ForeignKey to tblVillage, nullable)
  - `role` (ForeignKey to tblRoles, nullable)
  - `department` (ForeignKey to tblDepartment, nullable)
- **Relations**:
  - Many-to-One with tblDistrict, tblCircle, tblGramPanchayat, tblVillage, tblRoles, tblDepartment

#### tblModule
- **Purpose**: System modules/features management
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=255) - Module name in English
  - `name_bn` (CharField, max_length=255, nullable) - Module name in Bengali
  - `name_as` (CharField, max_length=255, nullable) - Module name in Assamese
  - `div_id` (CharField, max_length=255, nullable) - HTML div identifier
  - `class_name` (CharField, max_length=255, nullable) - CSS class name

#### tblModulePermission
- **Purpose**: Department-wise module access permissions
- **Fields**:
  - `id` (AutoField, PK)
  - `department` (ForeignKey to tblDepartment)
  - `module` (ForeignKey to tblModule)
- **Relations**:
  - Many-to-One with tblDepartment and tblModule

---

### 2. **village_profile** App - Administrative Hierarchy

#### tblDistrict
- **Purpose**: District-level administrative units
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=100) - District name in English
  - `name_bn` (CharField, max_length=100, nullable) - District name in Bengali
  - `name_as` (CharField, max_length=100, nullable) - District name in Assamese
  - `code` (CharField, max_length=100) - District code
  - `latitude` (FloatField, nullable) - Geographic latitude
  - `longitude` (FloatField, nullable) - Geographic longitude

#### tblCircle
- **Purpose**: Circle-level administrative units under districts
- **Fields**:
  - `id` (AutoField, PK)
  - `district` (ForeignKey to tblDistrict)
  - `name` (CharField, max_length=100) - Circle name in English
  - `name_bn` (CharField, max_length=100, nullable) - Circle name in Bengali
  - `name_as` (CharField, max_length=100, nullable) - Circle name in Assamese
- **Relations**:
  - Many-to-One with tblDistrict

#### tblGramPanchayat
- **Purpose**: Gram Panchayat level administrative units
- **Fields**:
  - `id` (AutoField, PK)
  - `circle` (ForeignKey to tblCircle)
  - `name` (CharField, max_length=100) - GP name in English
  - `name_bn` (CharField, max_length=100, nullable) - GP name in Bengali
  - `name_as` (CharField, max_length=100, nullable) - GP name in Assamese
- **Relations**:
  - Many-to-One with tblCircle

#### tblVillage
- **Purpose**: Village-level administrative units (lowest level)
- **Fields**:
  - `id` (AutoField, PK)
  - `gram_panchayat` (ForeignKey to tblGramPanchayat)
  - `name` (CharField, max_length=100) - Village name in English
  - `name_bn` (CharField, max_length=100, nullable) - Village name in Bengali
  - `name_as` (CharField, max_length=100, nullable) - Village name in Assamese
  - `code` (CharField, max_length=100, nullable) - Village code
  - `latitude` (FloatField, nullable) - Geographic latitude
  - `longitude` (FloatField, nullable) - Geographic longitude
- **Relations**:
  - Many-to-One with tblGramPanchayat

---

### 3. **field_images** App - Field Documentation

#### FieldImage
- **Purpose**: Stores field images with categorization and village association
- **Fields**:
  - `id` (AutoField, PK)
  - `village` (ForeignKey to tblVillage) - Associated village
  - `image` (ImageField, upload_to='field_images/') - Image file
  - `upload_datetime` (DateTimeField, auto_now_add=True) - Upload timestamp
  - `category` (CharField, max_length=50, choices=CATEGORY_CHOICES) - Image category
  - `name` (CharField, max_length=100, nullable) - Optional image name
  - `uploaded_by` (ForeignKey to tblUser, nullable) - User who uploaded
- **Category Choices**:
  - Livelihood
  - Educational facilities
  - River bank protection/erosion
  - Infrastructure
  - Housing
  - PRA and field consultations
  - PRA Map
- **Relations**:
  - Many-to-One with tblVillage and tblUser
- **Constraints**: Maximum 2 images per category per village

---

### 4. **layers** App - GIS Layer Management

#### GeoserverLayers
- **Purpose**: Manages GeoServer layer configurations for mapping
- **Fields**:
  - `id` (AutoField, PK)
  - `title` (CharField, max_length=255) - Layer title in English
  - `title_as` (CharField, max_length=255, nullable) - Layer title in Assamese
  - `title_bn` (CharField, max_length=255, nullable) - Layer title in Bengali
  - `layer_name` (CharField, max_length=255) - GeoServer layer name
  - `workspace` (CharField, max_length=255) - GeoServer workspace

---

### 5. **rescue_equipment** App - Emergency Equipment Management

#### tbl_Rescue_Equipment
- **Purpose**: Defines types of rescue equipment
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=555) - Equipment name in English
  - `name_bn` (CharField, max_length=100, nullable) - Equipment name in Bengali
  - `name_as` (CharField, max_length=100, nullable) - Equipment name in Assamese
  - `task_force` (CharField, max_length=555, nullable) - Associated task force in English
  - `task_force_bn` (CharField, max_length=555, nullable) - Task force in Bengali
  - `task_force_as` (CharField, max_length=555, nullable) - Task force in Assamese
  - `specification` (CharField, max_length=555, nullable) - Equipment specs in English
  - `specification_bn` (CharField, max_length=555, nullable) - Specs in Bengali
  - `specification_as` (CharField, max_length=555, nullable) - Specs in Assamese

#### tbl_Rescue_Equipment_Status
- **Purpose**: Tracks equipment availability by village
- **Fields**:
  - `id` (AutoField, PK)
  - `equipment` (ForeignKey to tbl_Rescue_Equipment)
  - `village` (ForeignKey to tblVillage)
  - `count` (IntegerField, default=0) - Equipment count
  - `last_update` (DateTimeField, auto_now=True) - Last update timestamp
  - `updated_by` (ForeignKey to tblUser, nullable) - User who updated
- **Relations**:
  - Many-to-One with tbl_Rescue_Equipment, tblVillage, and tblUser

---

### 6. **task_force** App - Community Task Force Management

#### TaskForce
- **Purpose**: Manages village-level task force members
- **Fields**:
  - `id` (AutoField, PK)
  - `village` (ForeignKey to tblVillage) - Associated village
  - `fullname` (CharField, max_length=150) - Member full name
  - `father_name` (CharField, max_length=150) - Father's name
  - `gender` (CharField, max_length=10, choices=['Male', 'Female', 'Other'])
  - `occupation` (CharField, max_length=150, nullable) - Member occupation
  - `position_responsibility` (CharField, max_length=50, choices=['Team member', 'Team leader'])
  - `mobile_number` (CharField, max_length=15) - Contact number
  - `team_type` (CharField, max_length=50, choices=TeamType.choices) - Team category
- **Team Type Choices**:
  - VLCDMC
  - Search & rescue
  - Relief management team
  - Shelter Management team
  - First Aid team
  - Water & Sanitation
- **Relations**:
  - Many-to-One with tblVillage

---

### 7. **training** App - Training Activity Management

#### tbl_Training_Activities
- **Purpose**: Defines training activity types
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=555) - Activity name in English
  - `name_bn` (CharField, max_length=555, nullable) - Activity name in Bengali
  - `name_as` (CharField, max_length=555, nullable) - Activity name in Assamese

#### tbl_Training_Activities_Status
- **Purpose**: Tracks training activity status by village
- **Fields**:
  - `id` (AutoField, PK)
  - `activity` (ForeignKey to tbl_Training_Activities)
  - `village` (ForeignKey to tblVillage)
  - `status` (CharField, max_length=55, choices=['Completed', 'Scheduled'], default='Scheduled')
  - `implemented_date` (DateField, nullable) - Date of implementation
  - `remarks` (TextField, nullable) - Additional notes
  - `last_update` (DateTimeField, auto_now=True) - Last update timestamp
  - `updated_by` (ForeignKey to tblUser, nullable) - User who updated
- **Relations**:
  - Many-to-One with tbl_Training_Activities, tblVillage, and tblUser

---

### 8. **vdmp_progress** App - VDMP Activity Tracking

#### tblVDMP_Activity
- **Purpose**: Defines VDMP (Village Disaster Management Plan) activities
- **Fields**:
  - `id` (AutoField, PK)
  - `name` (CharField, max_length=555) - Activity name in English
  - `name_bn` (CharField, max_length=100, nullable) - Activity name in Bengali
  - `name_as` (CharField, max_length=100, nullable) - Activity name in Assamese
  - `order` (IntegerField, nullable) - Activity sequence order
  - `is_active` (BooleanField, default=True) - Activity status

#### tblVDMP_Activity_Status
- **Purpose**: Tracks VDMP activity progress by village
- **Fields**:
  - `id` (AutoField, PK)
  - `activity` (ForeignKey to tblVDMP_Activity)
  - `village` (ForeignKey to tblVillage)
  - `status` (CharField, max_length=20, choices=['Completed', 'In Progress', 'Not Started'], default='Not Started')
  - `last_update` (DateTimeField, auto_now=True) - Last update timestamp
  - `updated_by` (ForeignKey to tblUser, nullable) - User who updated
- **Relations**:
  - Many-to-One with tblVDMP_Activity, tblVillage, and tblUser

---

### 9. **vdmp_dashboard** App - Survey Data Management

#### HouseholdSurvey
- **Purpose**: Comprehensive household survey data
- **Fields**: 80+ fields covering demographics, housing, livelihood, vulnerability, etc.
- **Key Fields**:
  - `village` (ForeignKey to tblVillage)
  - `village_code`, `point_id` - Identifiers
  - `property_owner`, `name_of_hohh` - Household details
  - Housing characteristics (wall_type, roof_type, floor_type, etc.)
  - Demographics (males, females, children, senior citizens, etc.)
  - Livelihood and economic data
  - Flood and erosion vulnerability data
  - `last_updated` (DateTimeField, auto_now=True)

#### Commercial
- **Purpose**: Commercial building survey data
- **Fields**: Commercial property details, flood impact, business value, etc.
- **Key Relations**: Many-to-One with tblVillage

#### Critical_Facility
- **Purpose**: Critical infrastructure survey (schools, hospitals, etc.)
- **Fields**: Facility details, capacity, flood resilience, etc.
- **Key Relations**: Many-to-One with tblVillage

#### ElectricPole
- **Purpose**: Electric pole infrastructure data
- **Fields**: Location, material, condition, flood impact
- **Key Relations**: Many-to-One with tblVillage

#### Transformer
- **Purpose**: Electrical transformer infrastructure
- **Fields**: Location, flood depth, erosion class
- **Key Relations**: Many-to-One with tblVillage

#### BridgeSurvey
- **Purpose**: Bridge infrastructure survey
- **Fields**: Bridge specifications, condition, materials
- **Key Relations**: Many-to-One with tblVillage

#### VillageRoadInfo / VillageRoadInfoErosion
- **Purpose**: Road infrastructure affected by flood/erosion
- **Fields**: Road type, length, flood/erosion impact
- **Key Relations**: Many-to-One with tblVillage

#### VDMP_Maps_Data
- **Purpose**: Stores village-specific map files
- **Fields**: Various map types (FileField) - building distribution, infrastructure, hazards, etc.
- **Key Relations**: One-to-One with tblVillage

#### Risk_Assesment
- **Purpose**: Village-level risk assessment data
- **Fields**: Hazard type, exposure value, loss calculations
- **Key Relations**: Many-to-One with tblVillage

---

### 10. **shapefiles** App - Spatial Data (PostGIS)

#### ShapefileElectricPole
- **Purpose**: Spatial electric pole data from shapefiles
- **Fields**:
  - `gid` (IntegerField, PK)
  - `latitude`, `longitude` (DecimalField) - Coordinates
  - `geom` (PointField, SRID=4326) - PostGIS geometry
  - Various attribute fields (name, material, flood data, etc.)
- **Note**: Unmanaged model (existing database table)

#### ShapefileTransformer
- **Purpose**: Spatial transformer data from shapefiles
- **Fields**: Similar to ShapefileElectricPole with transformer-specific attributes
- **Note**: Unmanaged model

#### PraBoundary
- **Purpose**: Village boundary polygons with analysis data
- **Fields**: Village info, area calculations, infrastructure counts
- **Note**: Unmanaged model

#### ExposureRiver / ExposureRoadVillage
- **Purpose**: River and road exposure analysis data
- **Fields**: Exposure metrics, erosion/accretion data
- **Note**: Unmanaged models

---

## Database Relationships Summary

### Hierarchical Structure:
```
tblDistrict (1) → (N) tblCircle (1) → (N) tblGramPanchayat (1) → (N) tblVillage
```

### User Management:
```
tblUser → tblDistrict/tblCircle/tblGramPanchayat/tblVillage
tblUser → tblRoles, tblDepartment
tblDepartment → tblModulePermission ← tblModule
```

### Village-Centric Data:
```
tblVillage (1) → (N) FieldImage
tblVillage (1) → (N) TaskForce
tblVillage (1) → (N) tbl_Rescue_Equipment_Status
tblVillage (1) → (N) tbl_Training_Activities_Status
tblVillage (1) → (N) tblVDMP_Activity_Status
tblVillage (1) → (N) HouseholdSurvey, Commercial, Critical_Facility, etc.
tblVillage (1) → (1) VDMP_Maps_Data
```

---

## Key Features

1. **Multi-language Support**: Most models support English, Bengali, and Assamese
2. **Spatial Data**: PostGIS integration for geographic data
3. **Audit Trail**: Most models track last_update and updated_by
4. **File Management**: Support for image and document uploads
5. **Hierarchical Administration**: District → Circle → Gram Panchayat → Village
6. **Comprehensive Surveys**: Detailed household, commercial, and infrastructure data
7. **Risk Assessment**: Flood, erosion, and other hazard data
8. **Task Force Management**: Community-based disaster response teams
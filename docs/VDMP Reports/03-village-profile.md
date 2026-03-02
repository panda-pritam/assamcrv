# Chapter 3: Village Profile - VDMP Report

## Overview

The Village Profile chapter provides comprehensive baseline information about the village, including location details, socio-economic characteristics, livelihood patterns, asset profiles, and infrastructure inventory. This chapter forms the foundation for understanding village context and vulnerability factors.

## Main Function: `draw_village_profile(elements, village_id)`

**Purpose**: Generates detailed village profile with multiple sections and data tables
**Location**: `village_profile.py`

**Chapter Structure**:
- 3.1 Location Details
- 3.2 Socio-Economic Profile  
- 3.3 Livelihood Profile
- 3.4 Asset Profile
- 3.5 Infrastructure
- 3.6 Access to Other Facilities
- 3.7 Land Use

## Section 3.1: Location Details

### Function: `getVillageLocationDetails(village_id)`
**Database Tables**: `tblVillage`, `PRA_main`, `lulc` (PostGIS)

**Content**:
- **Administrative Hierarchy**: Revenue village, Block, Revenue circle, District
- **Geographic Information**: Distance from district HQ, total area, elevation
- **Spatial Calculations**: Area derived from LULC geometry

**Key Calculations**:
```sql
-- Village area from LULC polygons
SELECT COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000,0)
FROM public.lulc
WHERE "Vill_ID" = village_code
```

**Data Hierarchy**:
1. **Primary**: PostGIS spatial calculations
2. **Fallback**: PRA_main survey data
3. **Default**: "N/A" for missing information

## Section 3.2: Socio-Economic Profile

### 3.2.1 Demographic Profile
**Function**: `getVillageDemographic(village_id)`
**Database**: `HouseholdSurvey`

**Metrics Calculated**:
- **Population Statistics**: Male, female, total population
- **Household Count**: Total surveyed households
- **Family Size**: Average persons per household
- **Gender Ratio**: Females per 1,000 males

**Robust Aggregation**:
```python
totals = households.aggregate(
    total_males=Coalesce(
        Sum(Cast(Cast('number_of_males_including_children', FloatField()), IntegerField())),
        0
    ),
    total_females=Coalesce(
        Sum(Cast(Cast('number_of_females_including_children', FloatField()), IntegerField())),
        0
    )
)
```

### 3.2.2 Socio-Economic Status Matrix
**Function**: `getSocialEconomicStatusData(village_id)`
**Database**: `HouseholdSurvey`

**Cross-Tabulation Analysis**:
- **Social Categories**: Differently Abled, Married Male, Single Man, Single Woman, Widow
- **Economic Categories**: AAY, APL, AY, BPL, PHH
- **Output**: Matrix showing household distribution across social-economic dimensions

**Normalization Functions**:
```python
def normalize_social_status(value):
    # Maps various text inputs to standardized categories
    
def map_economic_status(economic):
    # Maps economic status variations to standard codes
```

**Summary Statistics**:
- BPL percentage
- PHH percentage  
- Widow-headed households
- Married male-headed households

## Section 3.3: Livelihood Profile

### 3.3.1 Agricultural Land Holding
**Function**: `getAgricultureLandHoldingData(village_id)`
**Database**: `HouseholdSurvey`

**Land Categories**:
- **< 0.5 bigha**: Marginal farmers
- **0.5-1.5 bigha**: Small farmers
- **1.5-2.5 bigha**: Medium farmers
- **> 2.5 bigha**: Large farmers

**Ownership Types**:
- **Owned**: Direct ownership
- **Leased**: Tenant farming
- **No Land**: Landless laborers

**Analysis Logic**:
```python
def get_bucket(area):
    area_float = float(area)
    if area_float < 0.5: return 'u05'
    elif area_float < 1.5: return '0515'
    elif area_float <= 2.5: return '1525'
    else: return 'a25'
```

### 3.3.2 Income Distribution
**Function**: `getIncomeGroupData(village_id)`
**Database**: `HouseholdSurvey`

**Income Brackets**:
- **≤ INR 50,000**: Low income
- **INR 50,001-150,000**: Lower middle income
- **INR 150,001-250,000**: Middle income
- **> INR 250,000**: Higher income

**Data Processing**:
```python
households = households.annotate(
    income_clean=Replace(
        Replace('approximate_income_earned_every_year_inr', Value(','), Value('')),
        Value(' '), Value('')
    )
).annotate(
    income_amt=Case(
        When(income_clean__regex=r'^\d+$',
             then=Cast('income_clean', IntegerField())),
        default=None,
        output_field=IntegerField()
    )
)
```

### 3.3.3 Expenditure Analysis
**Function**: `getAverageExpenditureBreakdownData(village_id)`
**Database**: `HouseholdSurvey`

**Expenditure Categories**:
- Agriculture and livestock
- Festival and marriage
- House repair
- Tobacco and liquor
- Education
- Health
- Food

**Percentage Calculation**:
```python
def safe_decimal(value):
    # Robust conversion of string fields to Decimal
    clean_value = ''.join(c for c in str(value) if c.isdigit() or c == '.')
    return Decimal(clean_value) if clean_value else Decimal('0')
```

### 3.3.4 Livelihood Distribution
**Function**: `getPrimaryLivelihoodDistributionData(village_id, type)`
**Database**: `HouseholdSurvey`

**Livelihood Categories**:
- Agriculture
- Fishing
- Livestock
- Manual labour
- Weaving
- Service
- Shop
- No job

**Dual Analysis**: Primary and secondary economic activities

### 3.3.5 Crop Cultivation Patterns
**Function**: `getCropCultivationData(village_id)`
**Database**: `HouseholdSurvey`

**Crop Diversity Analysis**:
- One crop (monoculture)
- Two crops (limited diversity)
- More than 2 crops (diversified)
- No agriculture (non-farming households)

**Processing Logic**:
```python
crop_list = [c.strip() for c in crops.split(',') 
             if c.strip() and c.strip() not in ('none', 'null', 'n/a')]
crop_count = len(crop_list)
```

### 3.3.6 Livestock Ownership
**Function**: `getLivestockOwnershipData(village_id)`
**Database**: `HouseholdSurvey`

**Livestock Categories**:
- **Big Cattle**: Buffalo, cows
- **Small Cattle**: Goats, sheep, pigs

**Count Classifications**:
- 0 animals
- < 3 animals
- 3-6 animals
- > 6 animals

### 3.3.7 FGD Livelihood Data
**Function**: `getFGDLivelihoodData(village_id)`
**Database**: `FGD_livelihood_summary`

**Qualitative Information**:
- **Cropping Pattern**: Seasonal crop rotation
- **Cropping Calendar**: Planting and harvesting schedules
- **Agricultural Challenges**: Constraints and issues
- **Livestock Activities**: Animal husbandry practices
- **Departmental Support**: Government assistance programs

## Section 3.4: Asset Profile

### 3.4.1 Housing Typology
**Function**: `getHousingTypologyData(village_id)`
**Database**: `HouseholdSurvey`

**House Classifications**:
- **Kachcha**: Traditional materials (bamboo, mud, thatch)
- **Semi Pucca**: Mixed materials (brick walls, tin roof)
- **Pucca**: Permanent materials (brick, concrete)

**Detailed Definitions**:
- **Kachcha Variants**: Mud house, Ikra house, Chang house, Bamboo house, Tin house
- **Semi Pucca Types**: Mud floor vs cement floor variants
- **Pucca Standard**: Brick with cement + concrete + cement

### 3.4.2 Digital Access
**Function**: `getDigitalAccessData(village_id)`
**Database**: `HouseholdSurvey`

**Digital Media Categories**:
- Mobile phone only
- TV only
- Radio only
- Radio and mobile phone
- TV and mobile phone
- None

### 3.4.3 Water and Sanitation
**Functions**: 
- `getDrinkingWaterSourceData(village_id)`
- `getAdequacyOfDrinkingWaterData(village_id)`
- `getJJMHouseConnect(village_id)`
- `getSanitationFacilities(village_id)`
- `getHouseholdToiletsType(village_id)`
- `getDe_sludgeMaterial(village_id)`

**Water Source Analysis**:
- Source identification and distribution
- Adequacy assessment
- JJM (Jal Jeevan Mission) connectivity

**Sanitation Assessment**:
- Toilet ownership (own vs shared/none)
- Toilet types (single pit, twin pit)
- Sludge disposal methods

### 3.4.4 Electricity Access
**Functions**:
- `getElectricityconnection(village_id)`
- `getElectricitySource(village_id)`

**Electricity Analysis**:
- Connection availability (yes/no)
- Source types (grid, solar, combined)

## Section 3.5: Infrastructure

### 3.5.1 Road Infrastructure
**Function**: `getRoadLengthByTypologyData(village_id, workspace, layer)`
**Database**: `road_network` (PostGIS), GeoServer WFS fallback

**Road Surface Types**:
- Bituminous
- Cement block
- Earthen
- Other surface types

**Data Sources**:
1. **Primary**: PostGIS database queries
2. **Fallback**: GeoServer WFS requests

**Length Calculation**:
```sql
-- Database approach
SELECT "RSur_Type", SUM("Length") AS total_length
FROM public.road_network
WHERE "Vill_ID" = village_code
GROUP BY "RSur_Type"
```

### 3.5.2 Power Infrastructure
**Function**: `getPowerInfrastructureData_Total(village_id)`
**Database**: `electricpoles`, `transformer` (PostGIS)

**Infrastructure Count**:
- Electric posts and network
- Transformers

**Query Logic**:
```sql
-- Check table existence then count
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema='public' AND table_name='electricpoles'
)
```

## Section 3.6: Access to Other Facilities

### Function: `getFacilityAccessData(village_id)`
**Database**: `PRA_main`

**Facility Distance Analysis**:
- Higher secondary school
- College
- Post office
- Police station
- Banks
- PHC (Primary Health Center)
- CHC (Community Health Center)
- Private clinic/hospital
- Ambulance service
- Bus service
- Main markets
- Veterinary hospitals

**Distance Formatting**:
```python
def format_distance(distance):
    if distance is None: return "N/A"
    return f"{distance:.0f} km" if float(distance).is_integer() else f"{distance:.1f} km"
```

## Section 3.7: Land Use

### Function: `getLULCData(village_id, workspace, layer, onlymax=False)`
**Database**: `lulc` (PostGIS), GeoServer WFS fallback

**Land Use Categories**:
- Agriculture land (includes fallow land)
- Built-up area
- Water bodies
- Forest/vegetation
- Other land uses

**Area Calculations**:
```sql
SELECT "Class_name", SUM("Area_SqM") as total_area
FROM public.lulc
WHERE "Vill_ID" = village_code
GROUP BY "Class_name"
```

**Normalization**:
```python
def normalize_landuse_name(name):
    # Merge fallow into agriculture
    if name in ["fallow land", "agriculture land"]:
        return "Agriculture land"
    return name.capitalize()
```

## Visual Elements and Maps

### Map Integration
**Database**: `VdmpVillageMapData`, `VdmDistrictMapData`

**Village-Level Maps**:
- Distribution of buildings
- Road infrastructure
- Land use
- Flood and erosion
- Essential facilities
- Electrical infrastructure

**District-Level Maps**:
- Wind hazard
- Earthquake hazard

**Image Handling**:
```python
# Primary: Database-stored images
img_field = map_file_fields.get('distribution_of_building')
if img_field:
    img_path = f"{MEDIA_ROOT}/{img_field}"
    img = ReportLabImage(img_path, width=450, height=image_height)

# Fallback: GeoServer-generated images
else:
    layers = ['assam:building_footprint']
    img = get_geoserver_image_as_rl_image(layers, village_id=village_id)
```

## Data Processing Utilities

### Robust Numeric Conversion
**Function**: `safe_decimal(value)`
**Purpose**: Convert string fields to numeric values safely

```python
def safe_decimal(value):
    clean_value = ''.join(c for c in str(value) if c.isdigit() or c == '.')
    return Decimal(clean_value) if clean_value else Decimal('0')
```

### Percentage Normalization
**Function**: `normalize_percentages(counts, total, decimals=0)`
**Purpose**: Ensure percentages sum to exactly 100%

```python
def normalize_percentages(counts, total, decimals=0):
    raw = [(c / total) * 100 for c in counts]
    rounded = [round(p, decimals) for p in raw]
    
    # Adjust last non-zero value to make total = 100%
    diff = round(100 - sum(rounded), decimals)
    for i in reversed(range(len(rounded))):
        if counts[i] > 0:
            rounded[i] = round(rounded[i] + diff, decimals)
            break
```

### Text Normalization
**Functions**: Various normalization functions for categorical data

**Examples**:
```python
def normalize_social_status(value):
    # Maps text variations to standard categories
    
def normalize_toilet_type(value):
    # Standardizes toilet type classifications
    
def normalize_electricity_source(value):
    # Categorizes electricity sources
```

## Table Styling and Layout

### Custom Table Styles
**Utility**: `create_styled_table()`

**Common Style Patterns**:
```python
custom_styles = [
    ('ALIGN', (0, 1), (0, -1), 'RIGHT'),      # Right-align S.No.
    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Bold S.No.
    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),     # Right-align numbers
    ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'), # Bold totals
]
```

### Complex Table Layouts
**Example**: Livestock ownership table with merged headers
```python
custom_styles2 = [
    ('SPAN', (2, 0), (3, 0)),  # Merge 'HH with big cattle' columns
    ('SPAN', (4, 0), (5, 0)),  # Merge 'HH with small cattle' columns
    ('SPAN', (0, 0), (0, 1)),  # Merge S.No. cells
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
```

## Error Handling and Data Quality

### Graceful Degradation
- **Missing Data**: "N/A" or "No data available" messages
- **Database Errors**: Exception handling with fallback values
- **Empty Queries**: Default table structures maintained

### Data Validation
- **Coordinate Validation**: Range checks for spatial data
- **Numeric Validation**: Safe conversion with error handling
- **Text Cleaning**: Standardization of categorical responses

### Fallback Mechanisms
- **Database to GeoServer**: Spatial data fallback chain
- **Survey to PRA**: Data source prioritization
- **Default Values**: Consistent fallback values

## Performance Optimizations

### Database Efficiency
- **Select Related**: Optimized joins for related models
- **Aggregation**: Database-level calculations
- **Batch Processing**: Efficient query patterns

### Memory Management
- **Lazy Evaluation**: QuerySets evaluated when needed
- **Image Handling**: Efficient image loading and processing
- **Resource Cleanup**: Proper disposal of temporary resources

## Integration with Report System

### Map File Management
**Integration**: Links with village and district map data
```python
village_maps = VdmpVillageMapData.objects.filter(village_id=village_id).values(
    'distribution_of_building',
    'road_infrastructure', 
    'landuse',
    'essential_facilities',
    'electrical_infrastructure'
).first()
```

### Cross-Chapter Data Sharing
- **Global Variables**: `VILLAGE_SUMMARY_DATA` for cross-reference
- **Consistent Metrics**: Shared calculation methods
- **Data Validation**: Consistent error handling patterns

## Visual Documentation

### Figure Integration
- **Figure 3-1**: Distribution of residential buildings
- **Figure 3-2**: Essential facilities
- **Figure 3-3**: Road infrastructure map
- **Figure 3-4**: Power infrastructure
- **Figure 3-5**: Land use map

### Legend Management
- **GeoServer Legends**: Automatic legend generation
- **Custom Legends**: Manual legend definitions
- **Color Coding**: Consistent visual representation

This comprehensive village profile provides stakeholders with detailed baseline information essential for understanding village context, identifying vulnerabilities, and planning appropriate disaster risk management interventions.
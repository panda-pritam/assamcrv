# Chapter 2: Village Summary - VDMP Report

## Overview

The Village Summary chapter provides a comprehensive overview of village characteristics, risk assessment, and key findings. It serves as an executive summary that presents critical information in tabular format for quick reference and decision-making.

## Main Function: `village_summary(elements, village_id)`

**Purpose**: Orchestrates the generation of all summary tables and sections
**Location**: `village_summary.py`

**Process Flow**:
1. Creates chapter heading "2 Summary Village Details"
2. Generates multiple summary tables through section configuration
3. Adds contact information sections
4. Applies consistent styling and formatting

## Summary Table Sections

### 1. General Summary
**Function**: `generate_general_summary_table(village_id)`
**Database Tables**: `tblVillage`, `lulc` (PostGIS)

**Content**:
- Date of baseline data collection
- Revenue village name
- Geographic area (calculated from LULC geometry)
- Administrative hierarchy (Block, Revenue circle, District)

**Key Calculations**:
```sql
-- Village area calculation
SELECT COALESCE(
    SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000.0, 0
) AS area_sqkm
FROM public.lulc
WHERE "Vill_ID" = village_code
```

**Data Sources**:
- Village hierarchy: `tblVillage` with related models
- Area calculation: PostGIS spatial operations on LULC data

### 2. Socio-Economic Summary
**Function**: `generate_socio_economic_summary_table(village_id)`
**Database Tables**: `HouseholdSurvey`, `lulc`

**Content Analysis**:

#### Population Statistics
- **Total Population**: Sum of males and females from household survey
- **Total Households**: Count of surveyed households
- **Calculation**: Uses `safe_int_sum()` for robust numeric conversion

#### Housing Characteristics
- **Dominant House Type**: Statistical mode of house construction types
- **Categories**: Kachcha, Semi Pucca, Pucca
- **Presentation**: Percentage of dominant type

**Implementation**:
```python
house_counts = {
    'Kachcha': kachcha_count,
    'Semi Pucca': semi_pucca_count, 
    'Pucca': pucca_count
}
max_house_type = max(house_counts, key=house_counts.get)
```

#### Land Use Analysis
- **Major Land Use**: Dominant land use category from LULC data
- **Calculation**: Area-weighted analysis of land use classes
- **Format**: "Land use type X% of total area"

#### Occupational Profile
- **Dominant Occupation**: Most common primary livelihood
- **Analysis**: Statistical mode of livelihood categories
- **Presentation**: Percentage engaged in dominant occupation

#### Sanitation Facilities
- **Focus**: Households with own toilets
- **Categories**: Pucca, Semi Pucca, Kachcha toilets
- **Analysis**: Percentage breakdown of toilet types

### 3. Hazard Assessment
**Function**: `getHazardAssessment(village_id)`
**Database Tables**: `PRA_main` (Participatory Rural Appraisal)

**Content Structure**:
- **Hazard Types**: Flood, Erosion, Strong Wind, Earthquake
- **Assessment Dimensions**: Frequency and Severity
- **Data Source**: Community-based hazard assessment

**Table Format**:
```
Hazard Type    | Frequency | Severity
Flood hazard   | Annual    | High
Erosion hazard | Seasonal  | Medium
```

### 4. Vulnerability Assessment
**Function**: `getVulnerabilityAssessment(village_id)`
**Database Tables**: `HouseholdSurvey`, `Critical_Facility`, `VillageRoadInfo`, `erosion_accretion`

**Vulnerability Indicators**:

#### Economic Vulnerability
- **BPL Households**: Below Poverty Line percentage
- **Priority Households**: Special assistance category percentage

#### Population Vulnerability
- **Vulnerable Groups**: Children, seniors, disabled, pregnant/lactating women
- **Calculation**: Sum of vulnerable population categories
- **Presentation**: Total count and percentage of population

#### Infrastructure Vulnerability
- **Flood Vulnerable Houses**: Houses with flood depth ≥ 0.5m
- **Erosion Vulnerable Houses**: Houses reporting erosion risk
- **School Vulnerability**: Educational facilities at flood risk

#### Road Infrastructure Risk
- **Flood Vulnerable Roads**: Road length in high flood zones
- **Erosion Vulnerable Roads**: Road segments in erosion-prone areas
- **Data Sources**: `VillageRoadInfo`, `VillageRoadInfoErosion`

#### River Bank Erosion
**Function**: `get_eroding_river_bank(village_id)`
**Database**: `erosion_accretion` (PostGIS)

**Analysis**:
```sql
SELECT "Length_km", "Class"
FROM public.erosion_accretion
WHERE "Vill_ID" = village_code
```

**Output**: "X km out of Y km" format showing eroding vs total river bank

#### Livelihood Vulnerability Index (LVI)
**Function**: `get_lvi_score(village_id)`
**Components**: Exposure, Sensitivity, Adaptive Capacity

**Calculation**:
```python
lvi_score = (exposure_score + sensitivity_score + adaptive_score) / 3
```

**Classification**:
- Very Low: ≤ 0.20
- Low: 0.21-0.40
- Medium: 0.41-0.60
- High: 0.61-0.80
- Very High: > 0.80

### 5. Risk Assessment
**Function**: `getRiskAssessment(village_id)`
**Database Tables**: `Risk_Assessment_Result`, `VillageRoadInfo`, `villageAgricultureLandFloodInfo`

**Risk Categories**:

#### Building Assets
- **Residential**: Household survey-based buildings
- **Commercial**: Commercial establishments
- **Critical Facilities**: Schools, health centers, community buildings

#### Infrastructure Assets
- **Roads**: Transportation network risk
- **Agriculture**: Crop and farmland vulnerability

**Hazard Scenarios**:
- **Flood**: Historical flood year (community-identified)
- **Earthquake**: 475-year return period
- **Strong Wind**: 100-year return period

**Loss Calculations**:
```python
# Convert to crores (10 million INR)
loss_crores = total_loss / 10000000

# Format for display
formatted_loss = f"INR {format_indian_number(int(loss_crores * 10000000))}"
```

### 6. Mitigation Intervention
**Function**: `getMitigationIntervention(village_id)`
**Purpose**: Summary of recommended risk reduction measures

## Contact Information Sections

### 2.1 Important Contact Details
**Function**: `getDistrictLevelOfficialsData(village_id)`
**Database**: `LineDepartment`

**Content**:
- Village-level officials and contacts
- District-level emergency contacts
- Departmental representatives

**Query Logic**:
```python
officials = LineDepartment.objects.filter(
    village_id=village_id,
    official_number__iexact='yes'
).select_related('section_master')
```

### 2.2 Emergency Toll Free Contact Information
**Function**: `getEmergencyTollFreeContactData(village_id)`
**Database**: `LineDepartment`

**Standard Emergency Numbers**:
- Police Station: 100
- Fire Station: 102
- Ambulance: 108
- District Emergency: 1077/1079

## Data Processing Utilities

### Numeric Data Handling
**Function**: `safe_int_sum(field_name)`
**Purpose**: Robust conversion of string fields to numeric values

**Process**:
1. Trim whitespace
2. Convert empty strings to NULL
3. Cast to float, then integer
4. Sum with zero fallback

### Text Processing
**Function**: `mode_value(field)`
**Purpose**: Find most common value in categorical fields

**Implementation**:
```python
row = (qs.exclude(**{f"{field}__isnull": True})
       .exclude(**{f"{field}__exact": ""})
       .values(field)
       .annotate(cnt=Count(field))
       .order_by("-cnt")
       .first())
```

### Number Formatting
**Function**: `format_indian_number(num)`
**Purpose**: Format numbers with Indian numbering system (lakhs, crores)

## Table Styling and Layout

### Table Configuration
**Function**: `draw_Village_summery_tables(elements, table_sections, village_id)`

**Section Structure**:
```python
table_sections = [
    {
        "heading": "General Summary",
        "getter_function": generate_general_summary_table,
        "col_width": [200, 300]
    },
    # ... other sections
]
```

### Custom Styling
- **Header Spanning**: First row spans all columns for section title
- **Bold Labels**: Left column uses bold formatting
- **Responsive Widths**: Column widths optimized for content
- **Consistent Spacing**: Standardized padding and margins

## Error Handling and Fallbacks

### Data Availability
- **Missing Data**: Graceful handling with "N/A" or "No data" messages
- **Empty Queries**: Fallback to default values
- **Database Errors**: Exception handling with safe defaults

### Robust Calculations
- **Division by Zero**: Checks for non-zero denominators
- **Type Conversion**: Safe numeric conversion with fallbacks
- **Null Handling**: Explicit null value management

## Performance Optimizations

### Database Queries
- **Select Related**: Optimized joins for related models
- **Aggregation**: Database-level calculations where possible
- **Caching**: Reuse of calculated values within function scope

### Memory Management
- **Lazy Evaluation**: QuerySets evaluated only when needed
- **Efficient Loops**: Minimized database hits in iterations

## Usage Integration

The village summary integrates with the main report generation through:

1. **Chapter Sequencing**: Called after preliminary sections
2. **Data Dependencies**: Uses village_id for all data retrieval
3. **Style Consistency**: Applies global styling from `global_styles.py`
4. **Page Management**: Includes strategic page breaks for layout

This comprehensive summary provides stakeholders with essential village information, risk profiles, and emergency contacts in a structured, easily digestible format that supports informed decision-making for disaster risk management.
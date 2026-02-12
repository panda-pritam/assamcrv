# VDMP Dashboard API Changes Summary

## Overview
Modified the `get_household_summary_data` API to implement new logic for hazard metrics calculation as per requirements.

## Changes Made

### 1. River Erosion Length Calculation
**Old Logic:** Used GeoServer WFS service to fetch erosion data  
**New Logic:** Uses `VillageRoadInfoErosion` model to calculate total road length affected by erosion

**Implementation:**
- Filters roads with `erosion_class` in ['High', 'Severe', 'high', 'severe']
- Sums `road_length_m` field
- Converts to kilometers
- Returns formatted string: `"{value} km"`

**Code Location:** `views.py` lines ~730-740

### 2. Flood Depth Calculations (Average & Maximum)
**Source:** `HouseholdSurvey.flood_depth_m` field

**Implementation:**
- Uses existing `safe_avg()` and `safe_max()` functions
- Filters out null, empty, and '0' values
- Converts meters to feet (1m = 3.28084 feet)
- Returns rounded values to 1 decimal place

**Code Location:** `views.py` lines ~850-865

### 3. Maximum Wind Speed
**Source:** Wind.tif raster file located at `media/pipeline_data/wind_raster/Wind.tif`

**Implementation:**
- New function `get_max_wind_speed()` added
- Uses GDAL library to read raster file
- Extracts maximum value from raster band
- Handles NoData values properly
- Returns value in km/hour
- Fallback to 51 km/hour if file not found or error occurs

**Code Location:** `views.py` lines ~900-930

### 4. Flood Vulnerable Houses
**Old Logic:** Checked `flood_class` field for specific values  
**New Logic:** Uses `flood_depth_m > 0.5` meters

**Implementation:**
- Filters households where `flood_depth_m > 0.5`
- Excludes null and empty values
- Casts field to FloatField for proper comparison
- Returns count of vulnerable houses

**Code Location:** `views.py` lines ~870-878

### 5. Erosion Vulnerable Houses
**Old Logic:** Checked for numeric values (100, 150)  
**New Logic:** Uses text values 'High' and 'Severe'

**Implementation:**
- Filters households with `erosion_class` in ['High', 'Severe', 'high', 'severe']
- Returns count of vulnerable houses

**Code Location:** `views.py` lines ~880-883

### 6. Flood Vulnerable Roads
**Old Logic:** Used `flood_class` field with specific text values  
**New Logic:** Uses `flood_depth_m > 0.5` meters

**Implementation:**
- Filters roads from `VillageRoadInfo` where `flood_depth_m > 0.5`
- Sums `road_length_m` field
- Converts to kilometers
- Returns value with 2 decimal places

**Code Location:** `views.py` lines ~895-900

### 7. Erosion Vulnerable Roads
**Logic:** Uses `erosion_class` field with 'High' and 'Severe' values

**Implementation:**
- Filters roads from `VillageRoadInfoErosion` with `erosion_class` in ['High', 'Severe', 'high', 'severe']
- Sums `road_length_m` field
- Converts to kilometers
- Returns value with 2 decimal places

**Code Location:** `views.py` lines ~902-906

## Frontend Changes

### JavaScript (vdmp_dashboard.js)
- Added `max_wind_speed` to hazardFields mapping
- Formatter: `(val) => ${val} km/hour`

### HTML (dashboard.html)
- Added `id="max_wind_speed"` to wind velocity display element
- Changed from hardcoded "51 km/hour" to dynamic value

## Dependencies Added
```python
from osgeo import gdal
import numpy as np
```

## API Response Structure
The API now returns:
```json
{
  "river_erosion_length_km": "X.XX km",
  "avg_flood_depth": X.X,  // in feet
  "max_flood_depth": X.X,  // in feet
  "max_wind_speed": X.X,   // in km/hour
  "flood_vulnerable_houses": X,
  "erosion_vulnerable_houses": X,
  "flood_vulnerable_roads": X.XX,  // in km
  "erosion_vulnerable_roads": X.XX  // in km
}
```

## Testing Recommendations
1. Verify Wind.tif file exists and is readable
2. Test with different location filters (district, circle, gram panchayat, village)
3. Verify flood_depth_m values are properly filtered (> 0.5)
4. Check erosion_class text matching (case-insensitive)
5. Validate unit conversions (meters to feet, meters to kilometers)
6. Test with null/empty data scenarios

## Notes
- GeoServer WFS logic for road length calculation has been commented out (not removed)
- All erosion class comparisons are case-insensitive
- Wind speed defaults to 51 km/hour if raster file is unavailable
- All length values are converted to kilometers with 2 decimal precision
- Flood depth values are converted to feet with 1 decimal precision

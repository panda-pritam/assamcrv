# GIS Risk Assessment Pipeline: Roads and Agriculture

## Overview

The GIS Risk Assessment Pipeline (`run_gis_risk_assessment_pipeline`) is a comprehensive geospatial analysis system that processes multiple hazard types (flood, earthquake, wind, erosion) for roads and agriculture infrastructure. Unlike the building-focused risk assessment, this pipeline uses advanced GIS techniques including zonal statistics, vector-raster intersections, and PostGIS spatial queries.

## Core Infrastructure Models

### Road Infrastructure Models

#### 1. VillageRoadInfo (Flood Hazard)
**Purpose**: Stores road segments with flood hazard exposure and damage calculations

**Key Fields**:
- `road_surface_type`: Road construction material (concrete, asphalt, gravel, etc.)
- `road_constructed_by`: Construction agency
- `road_length_m`: Length of road segment in meters
- `road_width_m`: Width of road in meters
- `flood_depth_m`: Flood depth from raster analysis
- `flood_hazard_mdr`: Mean Damage Ratio for flood hazard
- `replacement_cost_inr`: Reconstruction cost
- `flood_loss`: Expected flood damage (INR)

#### 2. VillageRoadInfoEQ (Earthquake Hazard)
**Purpose**: Road vulnerability to seismic hazards

**Key Fields**:
- `eq_hazard`: Peak Ground Acceleration (PGA) in 'g'
- `eq_hazard_mdr`: Earthquake damage ratio
- `eq_loss`: Expected earthquake damage

#### 3. VillageRoadInfoWind (Wind Hazard)
**Purpose**: Road exposure to wind hazards

**Key Fields**:
- `wind_hazard`: Wind speed in km/h
- `wind_hazard_mdr`: Wind damage ratio
- `wind_loss`: Expected wind damage

#### 4. VillageRoadInfoErosion (Erosion Risk)
**Purpose**: Road segments vulnerable to riverbank erosion

**Key Fields**:
- `erosion_class`: Risk classification (Severe, High, Medium, Low)
- `latitude`, `longitude`: Road segment coordinates

### Agriculture Infrastructure Models

#### 1. villageAgricultureLandFloodInfo
**Purpose**: Agricultural land flood vulnerability assessment

**Key Fields**:
- `total_area_sqm`: Agricultural area in square meters
- `flood_depth_m`: Maximum flood depth from zonal statistics
- `flood_class`: Flood severity classification
- `unit_cost_per_sqm`: Agricultural productivity value per sqm
- `total_replacement_cost_inr`: Total agricultural value
- `flood_hazard_mdr`: Crop damage ratio
- `flood_loss`: Expected crop losses

#### 2. villageAgricultureLandWindInfo
**Purpose**: Agricultural wind damage assessment

**Key Fields**:
- `wind_hazard`: Wind speed affecting crops
- `wind_hazard_mdr`: Crop wind damage ratio
- `wind_loss`: Expected wind-related crop losses

#### 3. villageAgricultureLandEQInfo
**Purpose**: Agricultural earthquake impact assessment

**Key Fields**:
- `eq_hazard`: Seismic intensity (PGA)
- `eq_hazard_mdr`: Agricultural earthquake damage ratio
- `eq_loss`: Expected seismic losses

#### 4. villageAgricultureLandErosionInfo
**Purpose**: Agricultural land erosion vulnerability

**Key Fields**:
- `erosion_class`: Erosion risk level
- `total_area_sqm`: Affected agricultural area

## GIS Processing Methodology

### 1. Road Risk Assessment Process

#### A. Zonal Line Length Analysis
**Function**: `process_road_flood_zonal_length()`

**Process Flow**:
1. **Raster to Grid Conversion**: Convert flood raster to vector grid polygons
   - Each pixel becomes a polygon with flood depth value
   - Maintains spatial precision for intersection analysis

2. **Road Vector Loading**: Load road network from PostGIS
   - Handles both uppercase and lowercase column naming conventions
   - Extracts road attributes (surface type, width, construction cost)

3. **Coordinate System Transformation**: 
   - Input: WGS84 (EPSG:4326)
   - Processing: UTM Zone 46N (EPSG:32646) for accurate length calculations

4. **Vector-Raster Intersection**:
   - Intersect road lines with flood grid polygons
   - Each intersection represents road length within specific flood depth

5. **Length Calculation**: Calculate precise road length per flood zone
   ```
   Road Length in Flood Zone = Intersection Geometry Length (meters)
   ```

6. **Aggregation**: Group by flood depth and road characteristics
   - Combines multiple road segments in same flood zone
   - Preserves road type and construction details

#### B. Replacement Cost Calculation
```
Replacement Cost = Road Length (m) × Road Width (m) × Unit Cost (INR/sqm)
```

#### C. Damage Assessment
**Function**: `get_road_flood_mdr()`
- Uses `roadFloodMDRMapping` table for damage curves
- Linear interpolation between known flood depth-MDR pairs
- Accounts for different road surface types

### 2. Agriculture Risk Assessment Process

#### A. Land Use Data Integration
**Function**: `load_village_agriculture_lulc()`

**Data Source**: PostGIS LULC (Land Use Land Cover) table
**Query**:
```sql
SELECT id, "Vill_ID", "Class_name", "Area_SqM", geom
FROM public.lulc
WHERE "Vill_ID" = village_code
  AND "Class_name" IN ('Agriculture Land', 'Fallow Land')
```

#### B. Zonal Statistics Analysis
**Function**: `get_zonal_stats_gdal()`

**Process**:
1. **Polygon-Raster Intersection**: For each agricultural polygon:
   - Extract raster values within polygon boundaries
   - Calculate mean, max, min hazard values
   - Count valid pixels for data quality assessment

2. **Hazard Value Assignment**:
   - **Flood**: Uses maximum flood depth within polygon
   - **Wind**: Uses mean wind speed
   - **Earthquake**: Uses mean PGA value

3. **Fallback Mechanisms**:
   - **Centroid Sampling**: If no valid pixels, sample at polygon centroid
   - **Village-Level Fallback**: Use clipped raster statistics if no coverage

#### C. Agricultural Loss Calculation

**Cost Calculation**:
```
Replacement Cost = Area (sqm) × Unit Cost per sqm
```

**Unit Costs**: Retrieved from `AgricultureLandCostMaping` model

**Damage Assessment**:
- **Flood MDR**: `agricultureLandFloodMDRMapping`
- **Wind MDR**: `agricultureLandWindMDRMapping`  
- **Earthquake MDR**: `agricultureLandEQMDRMapping`

**Loss Formula**:
```
Expected Loss = Replacement Cost × MDR
```

### 3. Erosion Risk Assessment

#### A. River Buffer Analysis
**Function**: `get_erosion_buffer_for_polygon()`

**PostGIS Query**:
```sql
SELECT MIN("BUFF_DIST") AS min_buffer
FROM public.riverbuffer
WHERE ST_Intersects(
    ST_Transform(ST_SetSRID(polygon_wkt, 4326), 32646),
    ST_Transform(ST_SetSRID(geom, 4326), 32646)
)
```

**Buffer Classifications**:
- **0-50m**: Severe risk
- **50-100m**: High risk  
- **100-150m**: Medium risk
- **>150m or No intersection**: Low risk

#### B. Road Erosion Processing
**Function**: `_process_road_erosion_data()`

**Process**:
1. **Centroid-Based Analysis**: Calculate road segment centroids
2. **Buffer Intersection**: Find minimum buffer distance for each road
3. **Risk Classification**: Apply erosion risk categories
4. **Coordinate Extraction**: Store lat/lon for mapping

## Pipeline Execution Flow

### Main Function: `run_gis_risk_assessment_pipeline(village_obj, village_code)`

#### Step 1: Data Validation
**Function**: `validate_gis_data_availability()`

**Validation Checks**:
- **Mandatory**: Flood raster (village-level)
- **Mandatory**: Wind raster (district-level with state fallback)
- **Mandatory**: Earthquake raster (district-level with state fallback)
- **Optional**: River buffer data (erosion analysis)

#### Step 2: Flood and Erosion Extraction
**Process**: Extract hazard values for all survey models
- Updates existing records with raster-derived values
- Applies classification schemes
- Handles missing data gracefully

#### Step 3: Building Risk Assessment
- Runs standard risk assessment pipeline for buildings
- Processes household, commercial, critical facility data

#### Step 4: Road Risk Assessment (Currently Commented)
```python
# Road flood analysis
process_road_flood_zonal_length(village_obj, village_code, flood_raster_path)

# Road erosion analysis  
_process_road_erosion_data(conn, village_obj, village_code, ...)
```

#### Step 5: Agriculture Risk Assessment (Currently Commented)
```python
process_all_agriculture_hazards(
    village_obj.id, village_code, district_name, 
    district_code, village_obj.name
)
```

## Advanced GIS Techniques

### 1. Raster-to-Vector Grid Conversion
**Function**: `raster_to_grid_gdf()`

**Purpose**: Convert raster pixels to vector polygons for precise intersection analysis

**Process**:
1. **Pixel Iteration**: Loop through each raster pixel
2. **Boundary Calculation**: Calculate geographic bounds for each pixel
3. **Polygon Creation**: Create vector polygon for each pixel
4. **Value Assignment**: Assign raster value to polygon attribute

### 2. Coordinate System Management
**Function**: `reproject_for_length()`

**Transformations**:
- **Input**: WGS84 (EPSG:4326) - Geographic coordinates
- **Processing**: UTM Zone 46N (EPSG:32646) - Projected coordinates
- **Reason**: Accurate distance/area calculations require projected CRS

### 3. Spatial Overlay Operations
**Function**: `intersect_roads_with_grid()`

**GeoPandas Operation**:
```python
intersections = gpd.overlay(roads_utm, grid_utm, how="intersection")
```

**Result**: Each output geometry represents road segment within specific hazard zone

### 4. Zonal Statistics with GDAL
**Function**: `get_zonal_stats_gdal()`

**Advanced Features**:
- **Memory Raster Creation**: Creates temporary mask raster
- **Polygon Rasterization**: Converts vector polygon to raster mask
- **Masked Statistics**: Calculates statistics only within polygon area
- **NoData Handling**: Properly excludes invalid raster values

## Data Quality and Validation

### 1. Coordinate Validation
- **Range Checks**: Latitude (-90 to 90), Longitude (-180 to 180)
- **NaN Detection**: Explicit handling of missing coordinates
- **Extent Validation**: Ensures coordinates fall within raster bounds

### 2. Raster Quality Checks
- **File Existence**: Validates raster file accessibility
- **Geotransform Validation**: Ensures valid spatial reference
- **NoData Handling**: Proper treatment of invalid pixels

### 3. Fallback Mechanisms
- **District to State**: Falls back to state-level rasters if district unavailable
- **Polygon to Centroid**: Uses centroid sampling if zonal stats fail
- **Village-Level Statistics**: Uses overall village statistics as last resort

## Performance Optimizations

### 1. Batch Processing
- **Database Operations**: Bulk create/update operations
- **Spatial Queries**: Optimized PostGIS queries with spatial indexes
- **Memory Management**: Efficient GDAL memory usage

### 2. Spatial Indexing
- **PostGIS**: Leverages spatial indexes for buffer queries
- **GDAL**: Efficient raster access patterns
- **GeoPandas**: Optimized spatial overlay operations

### 3. Data Caching
- **Raster Loading**: Reuses loaded raster datasets
- **Vector Data**: Caches village boundaries and road networks
- **Database Connections**: Connection pooling for spatial queries

## Configuration Requirements

### 1. Geospatial Data
- **Flood Rasters**: Village-level flood depth maps
- **Hazard Rasters**: District/state-level wind and earthquake maps
- **Vector Data**: Road networks, village boundaries, LULC polygons
- **Buffer Zones**: River buffer polygons for erosion analysis

### 2. Database Setup
- **PostGIS Extension**: Required for spatial operations
- **Spatial Indexes**: On geometry columns for performance
- **Coordinate Systems**: Proper SRID configuration

### 3. Software Dependencies
- **GDAL**: Raster processing and coordinate transformations
- **GeoPandas**: Vector spatial operations
- **PostGIS**: Spatial database queries
- **Shapely**: Geometric operations

## Usage Example

```python
# Run complete GIS risk assessment
run_gis_risk_assessment_pipeline(
    village_obj=village_instance,
    village_code="280_6"
)

# Run individual components
process_road_flood_zonal_length(village_obj, village_code, flood_raster_path)
process_all_agriculture_hazards(village_id, village_code, district_name, district_code, village_name)
```

## Output and Results

### 1. Road Infrastructure Results
- **Flood Exposure**: Road length by flood depth zones
- **Damage Assessment**: Expected losses by road type
- **Erosion Risk**: Road segments in erosion-prone areas
- **Replacement Costs**: Infrastructure reconstruction estimates

### 2. Agriculture Results
- **Crop Vulnerability**: Agricultural area by hazard intensity
- **Production Losses**: Expected crop damage by hazard type
- **Economic Impact**: Financial losses to agricultural sector
- **Risk Mapping**: Spatial distribution of agricultural risks

### 3. Spatial Outputs
- **Risk Maps**: Hazard exposure visualization
- **Loss Estimates**: Economic impact assessment
- **Priority Areas**: High-risk infrastructure identification
- **Mitigation Planning**: Data for risk reduction strategies

This GIS-focused pipeline provides comprehensive spatial risk assessment capabilities for critical infrastructure, enabling evidence-based disaster risk management and infrastructure planning decisions.
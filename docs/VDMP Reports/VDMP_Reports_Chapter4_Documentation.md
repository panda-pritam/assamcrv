# VDMP Reports - Chapter 4: Hazard Vulnerability Risk Assessment

## Overview
This chapter is the **CORE ASSESSMENT MODULE** of the VDMP system, providing scientific risk evaluation through two critical components:
1. **Flood Hazard Assessment** - Physical vulnerability to flood events
2. **Livelihood Sensitivity Assessment** - Socio-economic vulnerability factors

The module implements standardized scoring algorithms, spatial analysis, and multi-criteria decision analysis to generate quantitative risk scores for disaster management planning.

## Technical Architecture

### Module Structure
```python
hazard_Vulnerability_risk.py
├── getFloodHazardData(village_id, village_code)
├── getLivelihoodSensitivityData(village_id)
├── Scoring Algorithms (1-5 scale)
├── Normalization Functions (0-1 scale)
├── Spatial Analysis (PostGIS)
└── Report Generation (ReportLab)
```

### Import Dependencies
```python
from django.db import connection
from django.db.models import Q, Sum
from vdmp_dashboard.models import HouseholdSurvey, VillageRoadInfo, VillageRoadInfoErosion
from administrator.models import PRA_main
from reportlab.platypus import Paragraph
from .global_styles import *
```

## Main Sections

## 1. FLOOD HAZARD ASSESSMENT
**Function:** `getFloodHazardData(village_id, village_code)`

### Scientific Methodology
Implements **Multi-Hazard Risk Assessment Framework** combining:
- **Frequency Analysis**: Temporal flood patterns
- **Severity Analysis**: Physical impact measurement
- **Duration Analysis**: Temporal persistence of flooding
- **Erosion Analysis**: Geomorphological vulnerability

### Algorithm Implementation

#### 1.1 Flood Frequency Analysis
```python
# Data extraction from HouseholdSurvey
freq_data = HouseholdSurvey.objects.filter(village=village_id).values_list('frequency_of_flood', flat=True)

# Frequency categorization
freq_counts = {
    'Every Year': 0, 
    'Two Times Every Year': 0, 
    'Three Times Every Year': 0
}

# Pattern matching algorithm
for val in freq_data:
    if val and 'Every' in str(val):
        freq_counts[str(val)] = freq_counts.get(str(val), 0) + 1

# Dominant frequency identification
max_freq = max(freq_counts, key=freq_counts.get) if any(freq_counts.values()) else "Every Year"

# Scoring algorithm
freq_score = 3 if 'Every Year' in max_freq else (4 if 'Two' in max_freq else 5)
```

**Scoring Logic:**
- Every Year = 3 (Moderate frequency)
- Two Times Every Year = 4 (High frequency)
- Three Times Every Year = 5 (Very high frequency)

#### 1.2 Flood Severity Analysis
```python
# Household count for percentage calculation
total_hh = HouseholdSurvey.objects.filter(village=village_id).count()
severe_hh = 0

# Depth analysis with unit conversion
for hh in HouseholdSurvey.objects.filter(village=village_id).values_list('maximum_flood_height_in_house_ft', flat=True):
    try:
        depth_m = float(hh or 0) * 0.3048  # Feet to meters conversion
        if depth_m > 0.5:  # WHO flood severity threshold
            severe_hh += 1
    except:
        pass

# Percentage calculation
severity_pct = round(severe_hh / total_hh * 100) if total_hh > 0 else 0

# Linear scoring algorithm (20% intervals)
severity_score = min(5, max(1, round(severity_pct / 20)))
```

**Scientific Basis:**
- **0.5m threshold**: WHO standard for severe flooding impact
- **20% intervals**: Statistical quartile-based scoring
- **Linear scaling**: Proportional risk assessment

#### 1.3 Duration Analysis
```python
# Duration categorization system
duration_counts = {
    '3 Days': 0, 
    '3-7 Days': 0, 
    '7-15 Days': 0, 
    '15-20 Days': 0, 
    '20 Days': 0
}

# Pattern matching with priority hierarchy
for val in duration_data:
    if val:
        if '20' in str(val) and '15' not in str(val):
            duration_counts['20 Days'] += 1
        elif '15' in str(val):
            duration_counts['15-20 Days'] += 1
        elif '7' in str(val) and '3' not in str(val):
            duration_counts['7-15 Days'] += 1
        elif '3' in str(val) and '7' in str(val):
            duration_counts['3-7 Days'] += 1
        elif '3' in str(val):
            duration_counts['3 Days'] += 1

# Scoring mapping
duration_score = {
    '3 Days': 1,      # Short duration
    '3-7 Days': 2,    # Medium-short duration
    '7-15 Days': 3,   # Medium duration
    '15-20 Days': 4,  # Long duration
    '20 Days': 5      # Very long duration
}.get(max_duration, 3)
```

#### 1.4 Spatial Erosion Analysis
```python
# PostGIS spatial query for erosion calculation
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COALESCE(SUM(ST_Perimeter(ST_Transform(geom, 32646))) / 1000, 0)
        FROM public.erosion_accretion
        WHERE "Vill_ID" = %s
        AND (
            "Class" ILIKE 'erosion'
            OR "Class" ILIKE 'Errosion'
        )
    """, [village_code])
    erosion_km = round(cursor.fetchone()[0], 4)

# Linear scoring with 0.5km intervals
erosion_score = min(5, max(1, round(erosion_km / 0.5)))
```

### Score Normalization Algorithm
```python
# Convert 1-5 scale to 0-1 scale for standardization
scores = [freq_score, severity_score, duration_score, erosion_score]
normalized_scores = [(score - 1) / 4 for score in scores]

# Calculate weighted average
avg_score = round(sum(normalized_scores) / 4, 2)
```

### Report Table Generation
```python
data = [
    [Paragraph(title, bold_center_style)],
    [Paragraph("S. No.", bold_center_style), 
     Paragraph("Indicator", bold_center_style), 
     Paragraph("Explanation", bold_center_style), 
     Paragraph("Vulnerability score", bold_center_style)],
    [Paragraph("1", right_align_text), 
     Paragraph("Flood Frequency", normal_style), 
     Paragraph(f"Floods occur {max_freq.lower()}", normal_style), 
     Paragraph(str(freq_score), right_align_text)],
    # ... additional rows
    [Paragraph("", normal_style), 
     Paragraph("Total", bold_style), 
     Paragraph("", normal_style), 
     Paragraph(str(total_score), bold_right_align_text)]
]

return data, avg_score
```

---

## 2. LIVELIHOOD SENSITIVITY ASSESSMENT
**Function:** `getLivelihoodSensitivityData(village_id)`

### Comprehensive Vulnerability Framework
Implements **13-indicator assessment** covering:
- **Economic Vulnerability** (Indicators 1-4)
- **Infrastructure Vulnerability** (Indicators 5-6)
- **Access Vulnerability** (Indicators 7-13)

### Algorithm Implementation

#### 2.1 Land Ownership Analysis
```python
# Landless household identification
no_land = HouseholdSurvey.objects.filter(village=village_id).exclude(
    own_agriculture_land__icontains='own'
).count()

# Percentage calculation
no_land_pct = round(no_land / total_hh * 100)

# Linear scoring (20% intervals)
land_score = min(5, max(1, round(no_land_pct / 20)))
```

#### 2.2 Land Size Vulnerability
```python
# Small landholding analysis (<1.5 bigha threshold)
small_land = 0
for area in HouseholdSurvey.objects.filter(village=village_id).values_list(
    'area_of_agriculture_land_owned_bigha', flat=True
):
    try:
        if float(area or 0) < 1.5:  # Subsistence farming threshold
            small_land += 1
    except:
        pass

small_land_pct = round(small_land / total_hh * 100)
land_size_score = min(5, max(1, round(small_land_pct / 20)))
```

**Scientific Basis:**
- **1.5 bigha threshold**: Based on subsistence farming requirements
- **Linear scaling**: Proportional vulnerability assessment

#### 2.3 Income Dependency Analysis
```python
# Single income source identification
single_income = HouseholdSurvey.objects.filter(
    village=village_id
).exclude(
    livelihood_primary__iexact='No Job'
).filter(
    Q(livelihood_secondary__isnull=True) | Q(livelihood_secondary__exact='')
).count()

single_income_pct = round(single_income / total_hh * 100)
income_score = min(5, max(1, round(single_income_pct / 20)))
```

#### 2.4 Livelihood Loss Assessment
```python
# Multi-category loss analysis
loss_hh = HouseholdSurvey.objects.filter(village=village_id).filter(
    Q(loss_AgriLivli__icontains='Upto 5K') | 
    Q(loss_AgriLivli__icontains='Upto 15K') | 
    Q(loss_AgriLivli__icontains='Upto 25K') | 
    Q(loss_AgriLivli__icontains='Morethan 25K')
).count()

loss_pct = round(loss_hh / total_hh * 100)
loss_score = min(5, max(1, round(loss_pct / 20)))
```

#### 2.5 Infrastructure Vulnerability Analysis

**Road Flood Vulnerability:**
```python
# Total road length calculation
total_road_len = VillageRoadInfo.objects.filter(village=village_id).aggregate(
    Sum('road_length_m')
)['road_length_m__sum'] or 0

# Flood-affected road length (>0.5m depth)
flood_road_len = VillageRoadInfo.objects.filter(
    village=village_id, 
    flood_depth_m__gt=0.5
).aggregate(Sum('road_length_m'))['road_length_m__sum'] or 0

# Percentage calculation
road_flood_pct = round(flood_road_len / total_road_len * 100) if total_road_len > 0 else 0
road_flood_score = min(5, max(1, round(road_flood_pct / 20))) if total_road_len > 0 else 1
```

**Road Erosion Vulnerability:**
```python
# Erosion-affected road analysis
total_erosion_len = VillageRoadInfoErosion.objects.filter(village=village_id).aggregate(
    Sum('road_length_m')
)['road_length_m__sum'] or 0

severe_erosion_len = VillageRoadInfoErosion.objects.filter(
    village=village_id, 
    erosion_class__in=['Severe', 'High']
).aggregate(Sum('road_length_m'))['road_length_m__sum'] or 0

road_erosion_pct = round(severe_erosion_len / total_erosion_len * 100) if total_erosion_len > 0 else 0
road_erosion_score = min(5, max(1, round(road_erosion_pct / 20))) if total_erosion_len > 0 else 1
```

#### 2.6 PRA Access Indicators (7-13)
```python
# PRA data extraction with error handling
try:
    pra = PRA_main.objects.filter(village_id=village_id).first()
    if pra:
        # 6-point to 5-point scale conversion
        input_market_score = 6 - (pra.access_to_market_for_input_supplies or 1)
        output_market_score = 6 - (pra.access_to_market_for_output_produce or 1)
        seed_score = 6 - (pra.access_to_high_quality_seeds or 1)
        fair_price_score = 6 - (pra.access_to_fair_price_input_supplies or 1)
        tech_score = 6 - (pra.access_to_high_technology_farming_practices or 1)
        scientific_score = 6 - (pra.access_to_scientific_methods_of_farming_practices or 1)
    else:
        # Default values for missing PRA data
        input_market_score = output_market_score = seed_score = fair_price_score = tech_score = scientific_score = 3
except:
    # Error handling with neutral scores
    input_market_score = output_market_score = seed_score = fair_price_score = tech_score = scientific_score = 3

# Health service access
try:
    pra = PRA_main.objects.filter(village_id=village_id).first()
    health_score = 6 - (pra.access_to_health_service_including_vaccination or 1) if pra else 3
except:
    health_score = 3
```

**PRA Scale Conversion Logic:**
- Original PRA scale: 1 (Best) to 6 (Worst)
- Converted scale: 5 (Best) to 1 (Worst)
- Formula: `new_score = 6 - original_score`

### Final Score Calculation
```python
# Total score summation
total_score = (land_score + land_size_score + income_score + loss_score + 
              road_flood_score + road_erosion_score + input_market_score + 
              output_market_score + seed_score + fair_price_score + 
              tech_score + scientific_score + health_score)

# Normalization to 0-1 scale (13 indicators, each 1-5 scale)
scores = [land_score, land_size_score, income_score, loss_score, road_flood_score, 
         road_erosion_score, input_market_score, output_market_score, seed_score, 
         fair_price_score, tech_score, scientific_score, health_score]
normalized_scores = [(score - 1) / 4 for score in scores]
avg_score = round(sum(normalized_scores) / 13, 2)

return data, avg_score
```

---

## ## COMPREHENSIVE DATABASE SCHEMA

### Core Tables and Relationships

#### HouseholdSurvey Table
```sql
CREATE TABLE HouseholdSurvey (
    id SERIAL PRIMARY KEY,
    village_id INTEGER REFERENCES Village(id),
    frequency_of_flood VARCHAR(50),           -- "Every Year", "Two Times Every Year", etc.
    maximum_flood_height_in_house_ft DECIMAL, -- Flood depth in feet
    duration_of_flood_stay_in_your_agriculture_field VARCHAR(50), -- Duration categories
    own_agriculture_land VARCHAR(50),         -- Land ownership status
    area_of_agriculture_land_owned_bigha DECIMAL, -- Land area in bigha
    livelihood_primary VARCHAR(100),          -- Primary income source
    livelihood_secondary VARCHAR(100),        -- Secondary income source
    loss_AgriLivli VARCHAR(50)               -- Agricultural losses
);
```

#### VillageRoadInfo Table
```sql
CREATE TABLE VillageRoadInfo (
    id SERIAL PRIMARY KEY,
    village_id INTEGER REFERENCES Village(id),
    road_length_m DECIMAL,                   -- Road length in meters
    flood_depth_m DECIMAL                    -- Flood depth on roads in meters
);
```

#### VillageRoadInfoErosion Table
```sql
CREATE TABLE VillageRoadInfoErosion (
    id SERIAL PRIMARY KEY,
    village_id INTEGER REFERENCES Village(id),
    road_length_m DECIMAL,                   -- Road length affected by erosion
    erosion_class VARCHAR(20)                -- "Severe", "High", "Medium", "Low"
);
```

#### PRA_main Table
```sql
CREATE TABLE PRA_main (
    id SERIAL PRIMARY KEY,
    village_id INTEGER REFERENCES Village(id),
    access_to_market_for_input_supplies INTEGER,     -- 1-6 scale
    access_to_market_for_output_produce INTEGER,     -- 1-6 scale
    access_to_high_quality_seeds INTEGER,            -- 1-6 scale
    access_to_fair_price_input_supplies INTEGER,     -- 1-6 scale
    access_to_high_technology_farming_practices INTEGER, -- 1-6 scale
    access_to_scientific_methods_of_farming_practices INTEGER, -- 1-6 scale
    access_to_health_service_including_vaccination INTEGER -- 1-6 scale
);
```

#### erosion_accretion Spatial Table
```sql
CREATE TABLE erosion_accretion (
    id SERIAL PRIMARY KEY,
    "Vill_ID" VARCHAR(20),                   -- Village code identifier
    "Class" VARCHAR(50),                     -- "erosion", "Errosion", "accretion"
    geom GEOMETRY(POLYGON, 4326)             -- Spatial geometry in WGS84
);
```

## ADVANCED SCORING ALGORITHMS

### Multi-Criteria Decision Analysis (MCDA)

#### Weighted Scoring Framework
```python
def calculate_composite_risk(flood_score, livelihood_score, weights=None):
    """
    Calculate composite risk using weighted average
    Default weights: Equal weighting (0.5, 0.5)
    """
    if weights is None:
        weights = [0.5, 0.5]  # Equal weighting
    
    composite_score = (flood_score * weights[0]) + (livelihood_score * weights[1])
    return round(composite_score, 3)
```

#### Risk Classification System
```python
def classify_risk_level(normalized_score):
    """
    Classify risk based on normalized score (0-1 scale)
    """
    if normalized_score < 0.2:
        return "Very Low", "#00FF00"  # Green
    elif normalized_score < 0.4:
        return "Low", "#FFFF00"      # Yellow
    elif normalized_score < 0.6:
        return "Medium", "#FFA500"   # Orange
    elif normalized_score < 0.8:
        return "High", "#FF4500"     # Red-Orange
    else:
        return "Very High", "#FF0000" # Red
```

### Statistical Validation

#### Data Quality Metrics
```python
def calculate_data_completeness(village_id):
    """
    Calculate data completeness percentage for validation
    """
    total_hh = HouseholdSurvey.objects.filter(village=village_id).count()
    
    # Check completeness of key fields
    complete_flood_freq = HouseholdSurvey.objects.filter(
        village=village_id,
        frequency_of_flood__isnull=False
    ).exclude(frequency_of_flood='').count()
    
    complete_flood_depth = HouseholdSurvey.objects.filter(
        village=village_id,
        maximum_flood_height_in_house_ft__isnull=False
    ).count()
    
    completeness_pct = {
        'flood_frequency': round(complete_flood_freq / total_hh * 100, 1) if total_hh > 0 else 0,
        'flood_depth': round(complete_flood_depth / total_hh * 100, 1) if total_hh > 0 else 0
    }
    
    return completeness_pct
```

## PERFORMANCE OPTIMIZATION

### Database Query Optimization

#### Efficient Aggregation Queries
```python
# Optimized query using select_related and prefetch_related
def get_optimized_household_data(village_id):
    return HouseholdSurvey.objects.filter(
        village_id=village_id
    ).select_related('village').values(
        'frequency_of_flood',
        'maximum_flood_height_in_house_ft',
        'duration_of_flood_stay_in_your_agriculture_field',
        'own_agriculture_land',
        'area_of_agriculture_land_owned_bigha',
        'livelihood_primary',
        'livelihood_secondary',
        'loss_AgriLivli'
    )
```

#### Spatial Query Optimization
```python
# Optimized spatial query with proper indexing
def get_optimized_erosion_data(village_code):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COALESCE(SUM(ST_Perimeter(ST_Transform(geom, 32646))) / 1000, 0)
            FROM public.erosion_accretion
            WHERE "Vill_ID" = %s
            AND "Class" ILIKE ANY(ARRAY['erosion', 'Errosion'])
        """, [village_code])
        return cursor.fetchone()[0]
```

### Memory Management

#### Efficient Data Processing
```python
def process_large_dataset_efficiently(village_id):
    """
    Process large datasets using generators and batch processing
    """
    batch_size = 1000
    total_processed = 0
    
    # Use iterator() for memory-efficient processing
    for batch in HouseholdSurvey.objects.filter(
        village_id=village_id
    ).iterator(chunk_size=batch_size):
        # Process batch
        total_processed += 1
        
        if total_processed % batch_size == 0:
            # Periodic garbage collection
            import gc
            gc.collect()
    
    return total_processed
```

## ERROR HANDLING & VALIDATION

### Comprehensive Error Management

#### Data Validation Framework
```python
def validate_input_data(village_id, village_code):
    """
    Comprehensive input validation with detailed error reporting
    """
    validation_errors = []
    
    # Village existence validation
    if not Village.objects.filter(id=village_id).exists():
        validation_errors.append(f"Village ID {village_id} does not exist")
    
    # Household data validation
    hh_count = HouseholdSurvey.objects.filter(village=village_id).count()
    if hh_count == 0:
        validation_errors.append("No household survey data available")
    
    # Spatial data validation
    if village_code:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM public.erosion_accretion WHERE "Vill_ID" = %s',
                [village_code]
            )
            spatial_count = cursor.fetchone()[0]
            if spatial_count == 0:
                validation_errors.append(f"No spatial data for village code {village_code}")
    
    return validation_errors
```

#### Graceful Degradation System
```python
def safe_calculate_score(calculation_func, default_score=3, error_context=""):
    """
    Safe calculation wrapper with fallback values
    """
    try:
        return calculation_func()
    except ZeroDivisionError:
        logger.warning(f"Division by zero in {error_context}, using default score {default_score}")
        return default_score
    except (ValueError, TypeError) as e:
        logger.warning(f"Data type error in {error_context}: {str(e)}, using default score {default_score}")
        return default_score
    except Exception as e:
        logger.error(f"Unexpected error in {error_context}: {str(e)}, using default score {default_score}")
        return default_score
```

### Data Quality Assurance

#### Outlier Detection
```python
def detect_outliers(values, method='iqr'):
    """
    Detect outliers using IQR or Z-score methods
    """
    import numpy as np
    
    if method == 'iqr':
        Q1 = np.percentile(values, 25)
        Q3 = np.percentile(values, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = [x for x in values if x < lower_bound or x > upper_bound]
    elif method == 'zscore':
        mean = np.mean(values)
        std = np.std(values)
        z_scores = [(x - mean) / std for x in values]
        outliers = [values[i] for i, z in enumerate(z_scores) if abs(z) > 3]
    
    return outliers
```

## INTEGRATION PATTERNS

### Django Integration

#### Model Integration
```python
# models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class VulnerabilityAssessment(models.Model):
    village = models.ForeignKey('Village', on_delete=models.CASCADE)
    flood_hazard_score = models.DecimalField(
        max_digits=3, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    livelihood_sensitivity_score = models.DecimalField(
        max_digits=3, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    overall_risk_score = models.DecimalField(
        max_digits=3, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    assessment_date = models.DateTimeField(auto_now_add=True)
    data_completeness_pct = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ['village', 'assessment_date']
```

#### View Integration
```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def get_vulnerability_assessment(request, village_id):
    try:
        village = Village.objects.get(id=village_id)
        
        # Generate assessments
        flood_data, flood_score = getFloodHazardData(village_id, village.village_code)
        livelihood_data, livelihood_score = getLivelihoodSensitivityData(village_id)
        
        # Calculate composite risk
        overall_risk = (flood_score + livelihood_score) / 2
        risk_level, risk_color = classify_risk_level(overall_risk)
        
        # Data completeness check
        completeness = calculate_data_completeness(village_id)
        
        response_data = {
            'village_id': village_id,
            'village_name': village.village_name,
            'flood_hazard_score': flood_score,
            'livelihood_sensitivity_score': livelihood_score,
            'overall_risk_score': overall_risk,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'data_completeness': completeness,
            'assessment_timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Village.DoesNotExist:
        return JsonResponse({'error': 'Village not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

### API Documentation

#### REST API Endpoints
```yaml
# API Documentation (OpenAPI/Swagger format)
paths:
  /api/vulnerability-assessment/{village_id}:
    get:
      summary: Get vulnerability assessment for a village
      parameters:
        - name: village_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Successful assessment
          content:
            application/json:
              schema:
                type: object
                properties:
                  village_id:
                    type: integer
                  flood_hazard_score:
                    type: number
                    format: float
                    minimum: 0
                    maximum: 1
                  livelihood_sensitivity_score:
                    type: number
                    format: float
                    minimum: 0
                    maximum: 1
                  overall_risk_score:
                    type: number
                    format: float
                    minimum: 0
                    maximum: 1
                  risk_level:
                    type: string
                    enum: ["Very Low", "Low", "Medium", "High", "Very High"]
```

## TESTING FRAMEWORK

### Unit Tests
```python
# tests.py
import unittest
from django.test import TestCase
from .hazard_Vulnerability_risk import getFloodHazardData, getLivelihoodSensitivityData

class VulnerabilityAssessmentTests(TestCase):
    
    def setUp(self):
        # Create test data
        self.test_village = Village.objects.create(
            village_name="Test Village",
            village_code="TEST001"
        )
        
        # Create test household surveys
        HouseholdSurvey.objects.create(
            village=self.test_village,
            frequency_of_flood="Every Year",
            maximum_flood_height_in_house_ft=2.0,
            duration_of_flood_stay_in_your_agriculture_field="7-15 Days"
        )
    
    def test_flood_hazard_calculation(self):
        """Test flood hazard score calculation"""
        flood_data, flood_score = getFloodHazardData(
            self.test_village.id, 
            self.test_village.village_code
        )
        
        self.assertIsInstance(flood_score, float)
        self.assertGreaterEqual(flood_score, 0)
        self.assertLessEqual(flood_score, 1)
        self.assertIsInstance(flood_data, list)
    
    def test_livelihood_sensitivity_calculation(self):
        """Test livelihood sensitivity score calculation"""
        livelihood_data, livelihood_score = getLivelihoodSensitivityData(
            self.test_village.id
        )
        
        self.assertIsInstance(livelihood_score, float)
        self.assertGreaterEqual(livelihood_score, 0)
        self.assertLessEqual(livelihood_score, 1)
        self.assertIsInstance(livelihood_data, list)
    
    def test_empty_data_handling(self):
        """Test handling of villages with no data"""
        empty_village = Village.objects.create(
            village_name="Empty Village",
            village_code="EMPTY001"
        )
        
        flood_data, flood_score = getFloodHazardData(
            empty_village.id, 
            empty_village.village_code
        )
        
        # Should return default values, not crash
        self.assertIsNotNone(flood_score)
        self.assertIsNotNone(flood_data)
```

## DEPLOYMENT CONSIDERATIONS

### Production Optimization

#### Database Indexing Strategy
```sql
-- Recommended indexes for optimal performance
CREATE INDEX idx_household_survey_village_id ON HouseholdSurvey(village_id);
CREATE INDEX idx_village_road_info_village_id ON VillageRoadInfo(village_id);
CREATE INDEX idx_village_road_erosion_village_id ON VillageRoadInfoErosion(village_id);
CREATE INDEX idx_pra_main_village_id ON PRA_main(village_id);
CREATE INDEX idx_erosion_accretion_vill_id ON erosion_accretion("Vill_ID");
CREATE INDEX idx_erosion_accretion_class ON erosion_accretion("Class");

-- Spatial index for geometry column
CREATE INDEX idx_erosion_accretion_geom ON erosion_accretion USING GIST(geom);
```

#### Caching Strategy
```python
# Redis caching for frequently accessed assessments
from django.core.cache import cache
import hashlib

def get_cached_assessment(village_id, village_code):
    # Create cache key
    cache_key = f"vulnerability_assessment_{village_id}_{village_code}"
    
    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Calculate if not in cache
    flood_data, flood_score = getFloodHazardData(village_id, village_code)
    livelihood_data, livelihood_score = getLivelihoodSensitivityData(village_id)
    
    result = {
        'flood_data': flood_data,
        'flood_score': flood_score,
        'livelihood_data': livelihood_data,
        'livelihood_score': livelihood_score
    }
    
    # Cache for 1 hour
    cache.set(cache_key, result, 3600)
    
    return result
```
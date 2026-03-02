# VDMP Report Documentation

## Report entry point

- API endpoint: `/en/api/download_report?village_id=<id>`
- Handler: `assam_crv/vdmp_dashboard/views.py` -> `download_report`
- PDF builder: `assam_crv/vdmp_dashboard/pdf/main.py` -> `generate_pdf`
- Section modules: `assam_crv/vdmp_dashboard/pdf/` (village_summary.py, village_profile.py, hazard_Vulnerability_risk.py, Disaster_preparedness_and_response_plan.py, Mitigation_Intervention_and_Investment_Plan.py)

---

## Client Information

### Client Information
- Data source: static text embedded in code.
- Database tables used: none.
- Query/logic: hardcoded rows for client address, contact, and email.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/client_info.py` -> `draw_client_info_table`.
- Calculation logic: none.

---

## 2 Summary Village Details (chapter 2)

### General Summary
- Data source: `tblVillage` plus PostGIS `public.lulc` for area; LULC derived via helper.
- Database tables used: `tblVillage` (village_profile app), `public.lulc`.
- Query/logic: fetch village with `select_related` for block/circle/district; compute area with `ST_Area` on lulc geom; major landuse via `getLULCData` (class area aggregation).
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `generate_general_summary_table` (uses `get_village_area` and `getLULCData`).
- Calculation logic: area in sq km is sum of lulc geometry areas, formatted to 2 decimals.

### Socio-Economic Summary
- Data source: `HouseholdSurvey` and PostGIS `public.lulc`.
- Database tables used: `HouseholdSurvey` (vdmp_dashboard), `public.lulc`.
- Query/logic: counts households and population; derives dominant house type from `house_type` counts; dominant occupation from mode of `livelihood_primary`; sanitation summary from `sanitation_facility` and `toilet_class`; landuse via `get_major_land_use` (lulc class area aggregation).
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `generate_socio_economic_summary_table` and `get_major_land_use`.
- Calculation logic: percentages computed from counts vs total households.

### Hazard Assessment
- Data source: `PRA_main`.
- Database tables used: `PRA_main` (administrator app).
- Query/logic: fetch single PRA record and read hazard frequency and severity fields.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getHazardAssessment`.
- Calculation logic: none beyond null handling and string formatting.

### Vulnerability Assessment
- Data source: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `Critical_Facility`, `ExposureRiver`.
- Database tables used: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `Critical_Facility`, `shapefiles_exposureriver` (via `ExposureRiver`), plus PRA-derived LVI tables in hazard module.
- Query/logic: counts BPL/PHH from `economic_status`; sums vulnerable population (children, seniors, pregnant, lactating, disabled); counts flood/erosion vulnerable houses; sums road length with flood/erosion filters; counts schools and flood-affected schools; uses river erosion helper for eroding bank length; LVI score via `get_lvi_score` (uses hazard module LVI data).
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getVulnerabilityAssessment`, `get_eroding_river_bank`, `get_lvi_score`.
- Calculation logic: percentages are computed against total households or population; road lengths are converted to km.

### Risk Assessment (excluding content loss in INR Crore)
- Data source: `Risk_Assessment_Result` plus road and agriculture loss tables.
- Database tables used: `Risk_Assessment_Result` (vdmp_progress), `VillageRoadInfo`, `VillageRoadInfoEQ`, `VillageRoadInfoWind`, `villageAgricultureLandFloodInfo`, `villageAgricultureLandEQInfo`, `villageAgricultureLandWindInfo`, `HouseholdSurvey` (for dominant flood year).
- Query/logic: sums loss columns by asset type for flood/eq/wind; converts to crores; picks dominant flood year from `HouseholdSurvey` to label flood column.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getRiskAssessment`.
- Calculation logic: loss sums are divided by 10,000,000 to convert to INR crores.

### Mitigation Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: returns a fixed set of rows with '-' values.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getMitigationIntervention` (called from `village_summary.py`).
- Calculation logic: none.

### Village Contacts (Important contact details)
- Data source: `LineDepartment`.
- Database tables used: `LineDepartment`, `LineDepartment.section_master` (administrator app).
- Query/logic: filter by `official_number='yes'` and village; list name, phone, and section.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getDistrictLevelOfficialsData`.
- Calculation logic: none (row numbering only).

### Emergency Toll Free Contact
- Data source: `LineDepartment` (or fallback static rows).
- Database tables used: `LineDepartment`, `LineDepartment.section_master` (administrator app).
- Query/logic: filter by `official_number='no'` and village; list section and phone; fallback hardcoded sample rows on error.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getEmergencyTollFreeContactData`.
- Calculation logic: none (row numbering only).

---

## 3 Village Profile (chapter 3)

### Location Details
- Data source: `tblVillage`, `PRA_main`, and PostGIS `public.lulc`.
- Database tables used: `tblVillage`, `PRA_main`, `public.lulc`.
- Query/logic: fetch village with block/circle/district names; compute area from lulc table; fallback to PRA fields for elevation and distance to district HQ.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getVillageLocationDetails`.
- Calculation logic: area is sum of `ST_Area(geom)`; numeric values formatted as strings.

### Demographic Profile
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: aggregate male and female totals via `Sum(Cast(...))`; compute total population, households, average family size, and females per 1000 males.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getVillageDemographic`.
- Calculation logic: average family size is rounded; female ratio is `(females/males)*1000`.

### Socio Economic Status
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: normalize `social_status` into buckets; map `economic_status` to AAY/APL/AY/BPL/PHH; count cross-tab totals and percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getSocialEconomicStatusData`.
- Calculation logic: row percentages are based on total households.

### Agriculture Land Holding
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `area_of_agriculture_land_owned_bigha` into size ranges; split by `own_agriculture_land` into leased/owned; compute counts and percentages; count no-land households.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getAgricultureLandHoldingData`.
- Calculation logic: percentages per bucket and total, derived from household counts.

### Annual Household Income
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: clean `approximate_income_earned_every_year_inr`, cast to integer, bucket into income ranges; compute counts and percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getIncomeGroupData`.
- Calculation logic: percent per bucket and overall reported percentage.

### Average Expenditure Breakdown
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: sum numeric values from expenditure fields (agri, festival, repair, tobacco, education, health, food); compute percent share of total.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getAverageExpenditureBreakdownData`.
- Calculation logic: percentage is `category_sum / grand_total` with rounding.

### Household Debt Liability
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: classify `loan_amount` into ranges; compute counts and percentages of households.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getHouseholdDebtLiabilityData`.
- Calculation logic: percent of total households.

### Primary Livelihood Distribution (primary economic activity)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: normalize `livelihood_primary`, count per category, compute percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPrimaryLivelihoodDistributionData`.
- Calculation logic: percentages based on total households.

### Secondary Livelihood Distribution (secondary economic activity)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: same as primary but uses `livelihood_secondary`.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPrimaryLivelihoodDistributionData` with `type='secondary'`.
- Calculation logic: percentages based on total households.

### Crop Cultivation
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts households by `number_of_crops_normally_raised_every_year` and computes percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getCropCultivationData`.
- Calculation logic: percent of households per crop count.

### Livestock Ownership
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `big_cattle` and `small_cattle` categorical values; computes percent of households per category.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getLivestockOwnershipData`.
- Calculation logic: percent of total households.

### Housing Typology
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `house_type` by Kachcha/Semi Pucca/Pucca; compute percent and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getHousingTypologyData`.
- Calculation logic: percent = count/total.

### Digital Access (Digital media owned)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `digital_media_owned` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getDigitalAccessData`.
- Calculation logic: percent of total households.

### Digital Access (Drinking water source)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `drinking_water_source` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getDrinkingWaterSourceData`.
- Calculation logic: percent of total households.

### Digital Access (Adequacy of drinking water)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `adequate_water_supply` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getAdequacyOfDrinkingWaterData`.
- Calculation logic: percent of total households.

### Digital Access (JJM or other tap water connection)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `JJM_or_other_taped_water_connection` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getJJMHouseConnect`.
- Calculation logic: percent of total households.

### Digital Access (Sanitation facilities)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `sanitation_facility` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getSanitationFacilities`.
- Calculation logic: percent of total households.

### Digital Access (Household toilets type)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `type_of_toilet` and `toilet_class` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getHouseholdToiletsType`.
- Calculation logic: percent of total households.

### Digital Access (De-sludge material)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `sludge_be_disposed_type` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getDe_sludgeMaterial`.
- Calculation logic: percent of total households.

### Digital Access (Electricity connection)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `house_has_electric_connection` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getElectricityconnection`.
- Calculation logic: percent of total households.

### Digital Access (Electricity source)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `source_of_electricity` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getElectricitySource`.
- Calculation logic: percent of total households.

### Public Assets
- Data source: `Commercial`.
- Database tables used: `Commercial`.
- Query/logic: counts facilities by `type_of_occupancy` and counts presence of electricity, water, sanitation, road access, and building quality.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPublicAssetsData`.
- Calculation logic: per-facility type counts only; no percentages.

### Road Length by Typology
- Data source: PostGIS `public.road_network` or GeoServer WFS fallback.
- Database tables used: `public.road_network` (PostGIS) or GeoServer layer `assam:road_network` via WFS.
- Query/logic: group by road surface type and sum length; convert meters to km; compute percent of total length.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getRoadLengthByTypologyData`.
- Calculation logic: `length_km = length_m/1000`; percent of total length.

### Power Infrastructure
- Data source: `ElectricPole` and `Transformer`.
- Database tables used: `ElectricPole`, `Transformer`.
- Query/logic: count poles and transformers by village.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPowerInfrastructureData_Total`.
- Calculation logic: simple counts.

### Facility Access
- Data source: `PRA_main`.
- Database tables used: `PRA_main` (administrator app).
- Query/logic: read nearest facility distance fields and format in km.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getFacilityAccessData`.
- Calculation logic: formats numeric distances with 0 or 1 decimal place.

### Land Use Classification
- Data source: PostGIS `public.lulc` or GeoServer WFS fallback.
- Database tables used: `public.lulc` or GeoServer layer `assam:lulc` via WFS.
- Query/logic: sum LULC class areas; normalize class names; compute percent share of total area.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getLULCData`.
- Calculation logic: percent = class_area/total_area.

---

## 4 Hazard, Vulnerability and Risk Assessment (chapter 4)

### Hazard Presence
- Data source: `PRA_main`.
- Database tables used: `PRA_main` (administrator app).
- Query/logic: read hazard frequency/severity fields for flood, erosion, strong wind, earthquake.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHazardPresenceData`.
- Calculation logic: none (null-safe formatting).

### Earthquake MMI
- Data source: static table.
- Database tables used: none.
- Query/logic: hardcoded MMI row.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEarthquakeMMITableData`.
- Calculation logic: none.

### Flood Hazard Characteristics
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: compute max flood depth, mode values of flood-related fields, and dominant year from survey fields.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHazardCharacteristics`.
- Calculation logic: uses `max` and `mode` across survey values with null-safe filtering.

### Flood Frequency at House
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: count households by keyword match in `house_affected_by_flood` using predefined frequency categories.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodFrequencyAtHouseData`.
- Calculation logic: percent = category_count/total_households.

### Flood Frequency in Agriculture Field
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: count households by keyword match in `your_agriculture_affected_by_flood` using frequency categories; track max category.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodFrequencyInAgricultureFieldData`.
- Calculation logic: percent = category_count/total_households.

### Flood Duration in Agriculture Field
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: count households by keyword match in `duration_of_flood_stay_in_your_agriculture_field` using duration categories.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodDurationInAgricultureFieldData`.
- Calculation logic: percent = category_count/total_households.

### Hazard Calendar
- Data source: `VdmDistrictMapData.hazard_calendar` image if present, otherwise static table.
- Database tables used: `VdmDistrictMapData` (vdmp_dashboard), or none for fallback table.
- Query/logic: if hazard calendar image is stored, it is rendered; otherwise table rows are hardcoded.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHazardCalender` (table fallback) and `draw_hazard_Vulnerability_risk`.
- Calculation logic: none (static labels).

### Erosion Characteristics
- Data source: PostGIS `public.erosion_accretion` table.
- Database tables used: `public.erosion_accretion`.
- Query/logic: raw SQL to sum erosion/accretion area and boundary length by class for the village.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getErosionCharacteristics`.
- Calculation logic: area in sq m and length in km from geometry calculations.

### Vulnerable Population
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: sums children, seniors, pregnant, lactating, disabled, and total population; computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getVulnerablePopulationTableData`.
- Calculation logic: percent of total population.

### Housing Flood Vulnerability
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result` (vdmp_progress).
- Query/logic: group by `house_type_name`; classify flood hazard depth into severe/high/moderate/low buckets.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHousingFloodVulnerabilityData`.
- Calculation logic: depth thresholds (>1.0, >0.5, >0.3, >0 m).

### Housing Erosion Vulnerability
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result` (vdmp_progress).
- Query/logic: group by `house_type_name`; count erosion classes (Severe/High/Medium/Low).
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHousingErosionVulnerabilityData`.
- Calculation logic: count by erosion class.

### House Typology
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts households by `house_type` and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHouseTypeData`.
- Calculation logic: percent of total households.

### Building Quality
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `building_quality` values into Good/Bad/Moderate categories; computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getBuildingQualityData`.
- Calculation logic: percent of total households.

### Plinth Height
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `plinth_or_stilt_height_ft` values into ranges and compute percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getPlinthHeightData`.
- Calculation logic: percent of total households.

### Toilet Quality
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `toilet_class` values (pucca/semi pucca/kachcha) and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getToiletStructuralQualityData`.
- Calculation logic: percent of total households.

### House Repair Expense
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `amount_towards_flood_recovery_expenditure` into ranges and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHouseRepairExpenseData`.
- Calculation logic: percent of total households.

### Household Flood Loss
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `economic_loss_to_your_house_due_to_flood` into ranges and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHouseholdFloodLossData`.
- Calculation logic: percent of total households.

### Agriculture Flood Loss
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `loss_AgriLivli` values into ranges and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getAgricultureFloodLossData`.
- Calculation logic: percent of total households.

### Road Flood Vulnerability
- Data source: `VillageRoadInfo`.
- Database tables used: `VillageRoadInfo`.
- Query/logic: sum `road_length_m` by flood class (Severe/High/Moderate/Low), convert to km and percent of total.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getRoadFloodVulnerabilityData`.
- Calculation logic: percent of total road length.

### Road Erosion Vulnerability
- Data source: `VillageRoadInfoErosion` and `VillageRoadInfo`.
- Database tables used: `VillageRoadInfoErosion`, `VillageRoadInfo`.
- Query/logic: sum `road_length_m` by erosion class from erosion table; compute total road length from `VillageRoadInfo` for percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getRoadErosionVulnerabilityData`.
- Calculation logic: percent of total road length.

### Educational Facilities
- Data source: `Critical_Facility`.
- Database tables used: `Critical_Facility`.
- Query/logic: filter by `occupancy_type` containing school; counts by flood class and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEducationalFacilitiesData`.
- Calculation logic: count and percent by flood class.

### Health Facilities
- Data source: `Critical_Facility`.
- Database tables used: `Critical_Facility`.
- Query/logic: filter health facility types (hospital, PHC, CHC); count by flood class and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHealthFacilitiesData`.
- Calculation logic: count and percent by flood class.

### Other Assets
- Data source: `Critical_Facility`, `ElectricPole`, `Transformer`.
- Database tables used: `Critical_Facility`, `ElectricPole`, `Transformer`.
- Query/logic: counts of non-education/non-health facilities plus power assets, split by flood class.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getOtherAssetsData`.
- Calculation logic: count and percent by flood class.

### Power Infrastructure
- Data source: `ElectricPole`, `Transformer`.
- Database tables used: `ElectricPole`, `Transformer`.
- Query/logic: count assets by flood class and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getPowerInfrastructureData`.
- Calculation logic: count and percent by flood class.

### Livelihood Exposure
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: compute exposure indicators using survey fields (economic loss, flood depth, flood frequency, etc.); produce a score row.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getLivelihoodExposureData`.
- Calculation logic: indicator scoring and averaging for exposure index.

### Livelihood Sensitivity
- Data source: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `PRA_main`.
- Database tables used: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `PRA_main`.
- Query/logic: combines agriculture, road, and PRA vulnerability indicators to compute sensitivity scores.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getLivelihoodSensitivityData`.
- Calculation logic: indicator scoring and averaging for sensitivity index.

### Livelihood Adaptive Capacity
- Data source: `HouseholdSurvey`, `PRA_main`.
- Database tables used: `HouseholdSurvey`, `PRA_main`.
- Query/logic: evaluates adaptive capacity indicators from survey and PRA fields to compute index.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getLivelihoodAdaptiveCapacityData`.
- Calculation logic: indicator scoring and averaging for adaptive capacity index.

### Environmental Characteristics
- Data source: `PRA_main` and erosion helper.
- Database tables used: `PRA_main`, `public.erosion_accretion` (via `getErosionCharacteristics`).
- Query/logic: uses PRA fields for siltation, water logging, encroachment, drains; erosion length from erosion table.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEnvironmentalCharacteristicsData`.
- Calculation logic: erosion length in km.

### Flood Loss Buildings
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result`.
- Query/logic: sum `replacement_cost_inr` and `flood_loss` by asset_type; compute loss percent per exposure.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodLossBuildingsTableData`.
- Calculation logic: values converted to INR crores; percent = loss/exposure.

### Flood Loss Roads Agriculture
- Data source: `VillageRoadInfo`, `villageAgricultureLandFloodInfo`.
- Database tables used: `VillageRoadInfo`, `villageAgricultureLandFloodInfo`.
- Query/logic: sum exposure and loss; format values in crore or lakh based on magnitude.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodLossRoadsAgriTableData`.
- Calculation logic: choose crore vs lakh based on exposure value; percent = loss/exposure.

### Average Loss Roads Agriculture
- Data source: `VillageRoadInfo`, `villageAgricultureLandFloodInfo`.
- Database tables used: `VillageRoadInfo`, `villageAgricultureLandFloodInfo`.
- Query/logic: average loss per km and per sq m for roads and agriculture.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getAverageLossRoadsAgriTableData`.
- Calculation logic: average = total_loss / total_length or total_area.

### Earthquake Loss Buildings
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result`.
- Query/logic: sum `replacement_cost_inr` and `eq_loss` by asset_type; compute loss percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEarthquakeLossBuildingsTableData`.
- Calculation logic: values in INR crores; percent = loss/exposure.

### Cyclone Loss Buildings
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result`.
- Query/logic: sum `replacement_cost_inr` and `wind_loss` by asset_type; compute loss percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getCycloneLossBuildingsTableData`.
- Calculation logic: values in INR crores; percent = loss/exposure.

### Strong Wind Agriculture Loss
- Data source: `villageAgricultureLandWindInfo`.
- Database tables used: `villageAgricultureLandWindInfo`.
- Query/logic: sum exposure and wind loss; compute loss percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getStrongWindAgricultureTableData`.
- Calculation logic: percent = loss/exposure.

---

## 5 Disaster Preparedness and Response Plan (chapter 5)

### Early Warning Systems
- Data source: static rows.
- Database tables used: none.
- Query/logic: hardcoded early warning sources and lead times.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> in `draw_disaster_preparedness_and_response_plan`.
- Calculation logic: none.

### Disaster Mitigation Plan
- Data source: static rows.
- Database tables used: none.
- Query/logic: hardcoded mitigation tasks and responsibilities.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> in `draw_disaster_preparedness_and_response_plan`.
- Calculation logic: none.

### VDMC Members
- Data source: `TaskForce`.
- Database tables used: `TaskForce` (task_force app).
- Query/logic: filter `team_type='VLCDMC'` and list member details.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `getVLCDMCMemberList`.
- Calculation logic: designation derived from `position_responsibility`.

### Identified Safe Shelter
- Data source: `PRA_shelter`.
- Database tables used: `PRA_shelter` (administrator app).
- Query/logic: list shelter properties and contacts by village.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `getSafeShelterData`.
- Calculation logic: none.

### Search and Rescue Team
- Data source: `TaskForce`.
- Database tables used: `TaskForce`.
- Query/logic: filter by `team_type='Search & rescue'` and list member details.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `getTeamMemberList`.
- Calculation logic: none.

### Relief Management Team
- Data source: `TaskForce`.
- Database tables used: `TaskForce`.
- Query/logic: filter by `team_type='Relief management team'` and list member details.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `getTeamMemberList`.
- Calculation logic: none.

### Shelter Management Team
- Data source: `TaskForce`.
- Database tables used: `TaskForce`.
- Query/logic: filter by `team_type='Shelter Management team'` and list member details.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `getTeamMemberList`.
- Calculation logic: none.

### First Aid Team
- Data source: `TaskForce`.
- Database tables used: `TaskForce`.
- Query/logic: filter by `team_type='First Aid team'` and list member details.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `getTeamMemberList`.
- Calculation logic: none.

### Safe Shelter
- Data source: `PRA_shelter`.
- Database tables used: `PRA_shelter` (administrator app).
- Query/logic: list shelters with rooms, capacity, contacts, and facilities.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/Disaster_preparedness_and_response_plan.py` -> `get_pra_shelter_data`.
- Calculation logic: none.

---

## 6 Mitigation Intervention and Investment Plan (chapter 6)

All tables in this chapter are currently populated with placeholders from `dummy_data.py` (all values are '-') and do not query the database.

### Developmental Issues and Needs
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getDevelopmentIssuesTable`.
- Calculation logic: none.

### Residential Vulnerability
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getResidentialVulnerabilityTable`.
- Calculation logic: none.

### Housing Cost
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getResilientHousingCostTable`.
- Calculation logic: none.

### Road Typology
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getRoadTypologyTable`.
- Calculation logic: none.

### Road Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getRoadInterventionTable`.
- Calculation logic: none.

### River Bank Protection
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getRiverBankProtectionTable`.
- Calculation logic: none.

### River Bank Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getRiverBankInterventionTable`.
- Calculation logic: none.

### Educational Facilities
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getEducationalFacilitiesTable`.
- Calculation logic: none.

### Educational Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getEducationalInterventionTable`.
- Calculation logic: none.

### WASH Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getWASHInterventionTable`.
- Calculation logic: none.

### Electric Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getElectricInterventionTable`.
- Calculation logic: none.

### Livelihood Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed row set.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getLivelihoodInterventionTable`.
- Calculation logic: none.

---

## 7 PRA Map and Field Photos (chapter 7)

- No report tables. Images are pulled from `FieldImage` records by category.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/PRA_map_and_Field_Photos.py` -> `draw_PRA_map_and_field_photos`.

## Column Mapping Details

This section lists how each report table column is populated. If a table is static, the columns are hardcoded in the PDF module.

### Client Information
- Columns: `Field`, `Value`.
- Column mapping: both columns are hardcoded strings in `draw_client_info_table`.

### General Summary
- Columns: `Field`, `Value`.
- Column mapping:
  - Field: hardcoded labels in `generate_general_summary_table`.
  - Value: `tblVillage.name`, `tblVillage.gram_panchayat.name`, `tblVillage.gram_panchayat.circle.name`, `tblVillage.gram_panchayat.circle.district.name`, and area from `public.lulc` via `ST_Area` sum; major landuse via `getLULCData`.

### Socio-Economic Summary
- Columns: `Field`, `Value`.
- Column mapping:
  - Total population: sum of `HouseholdSurvey.number_of_males_including_children` + `HouseholdSurvey.number_of_females_including_children`.
  - Total households: `HouseholdSurvey` count.
  - Dominant house type: counts of `HouseholdSurvey.house_type` values.
  - Major landuse: top `public.lulc.Class_name` by area.
  - Dominant occupational category: mode of `HouseholdSurvey.livelihood_primary`.
  - Sanitation facilities: distribution from `HouseholdSurvey.sanitation_facility` and `HouseholdSurvey.toilet_class`.

### Hazard Assessment
- Columns: `Hazard`, `Frequency`, `Severity`.
- Column mapping: `PRA_main` fields `flood_frequency`, `flood_severity`, `erosion_hazard_frequency`, `erosion_hazard_severity`, `strong_wind_hazard_frequency`, `strong_wind_hazard_severity`, `earthquake_hazard_frequency`, `earthquake_hazard_severity`.

### Vulnerability Assessment
- Columns: `Indicator`, `Value`.
- Column mapping:
  - Economic status: counts from `HouseholdSurvey.economic_status` (BPL/PHH).
  - Vulnerable population: sums of `children_below_6_years`, `senior_citizens`, `pregnant_women`, `lactating_women`, `persons_with_disability_or_chronic_disease` vs total population.
  - Eroding river bank: length from `ExposureRiver` or erosion helpers.
  - Flood/erosion vulnerable houses: `HouseholdSurvey.flood_depth_m` and `HouseholdSurvey.house_vulnerable_to_erosion`.
  - Flood/erosion vulnerable road: sums of `VillageRoadInfo.road_length_m` and `VillageRoadInfoErosion.road_length_m` with class filters.
  - School: counts in `Critical_Facility` with `occupancy_type` like school and flood depth filter.
  - Livelihood vulnerability index: computed from LVI tables in `hazard_Vulnerability_risk.py`.

### Risk Assessment (excluding content loss)
- Columns: `Sector`, `Flood`, `Earthquake 475 RP`, `Strong wind 100 RP`.
- Column mapping:
  - Residential/commercial/critical: sums of `Risk_Assessment_Result.flood_loss`, `eq_loss`, `wind_loss` for each `asset_type`.
  - Road: sums of `VillageRoadInfo.flood_loss`.
  - Agriculture: sums of `villageAgricultureLandFloodInfo.flood_loss`.
  - Flood header year: dominant `HouseholdSurvey.year_in_which_max_flood_experience_in_your_agriculture_land`.

### Mitigation Intervention
- Columns: `Indicator`, `Value`.
- Column mapping: all values hardcoded as '-' in `dummy_data.getMitigationIntervention`.

### Village Contacts (Important contact details)
- Columns: `S. No.`, `Name/designation`, `Phone Number`, `Position/Responsibility`.
- Column mapping: `LineDepartment.contact_name`, `LineDepartment.phone_number`, `LineDepartment.section_master.section`.

### Emergency Toll Free Contact
- Columns: `S. No.`, `Important Contact`, `Contact Number`.
- Column mapping: `LineDepartment.section_master.section`, `LineDepartment.phone_number`.

---

## 3 Village Profile column mappings

### Location Details
- Columns: `Field`, `Value`.
- Column mapping: `tblVillage` hierarchy fields; distance and elevation from `PRA_main`; total area from `public.lulc` geometry sum.

### Demographic Profile
- Columns: `S. No.`, `Household Characteristic`, `Total`.
- Column mapping: totals from `HouseholdSurvey` male/female fields; derived totals and ratios.

### Socio Economic Status
- Columns: `S. No.`, `Social/Economic Status Household`, `AAY`, `APL`, `AY`, `BPL`, `PHH`, `Total`, `%`.
- Column mapping: normalized `HouseholdSurvey.social_status` and `HouseholdSurvey.economic_status` counts; totals and percent of households.

### Agriculture Land Holding
- Columns: `S. No.`, `Agricultural land ownership (in bigha)`, `< 0.5`, `0.5-1.5`, `1.5-2.5`, `>2.5`, `Total`.
- Column mapping: buckets from `HouseholdSurvey.area_of_agriculture_land_owned_bigha` and `own_agriculture_land`.

### Annual Household Income
- Columns: `S. No.`, `Income Group (INR)`, `No. of Household`, `%`.
- Column mapping: buckets from cleaned `HouseholdSurvey.approximate_income_earned_every_year_inr`.

### Average Expenditure Breakdown
- Columns: `S. No.`, `Expenditure Category`, `%`.
- Column mapping: percent share of sums from `HouseholdSurvey.amount_spent_for_agriculture_livestock`, `expense_on_festival_marriage_and_other_social_occassions`, `expense_on_house_repair`, `expense_on_tobacco_liquor`, `expense_on_education`, `expense_on_health`, `expense_on_food`.

### Household Debt Liability
- Columns: `S. No.`, `Loan Amount (INR)`, `Number of households`, `%`.
- Column mapping: buckets from `HouseholdSurvey.loan_amount`.

### Primary Livelihood Distribution
- Columns: `Livelihood`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.livelihood_primary`.

### Secondary Livelihood Distribution
- Columns: `Livelihood`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.livelihood_secondary`.

### Crop Cultivation
- Columns: `Number of Crops Cultivated Every Year`, `Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.number_of_crops_normally_raised_every_year`.

### Livestock Ownership
- Columns: `Count`, `HH with Big Cattle`, `%`, `HH with Small Cattle`, `%`.
- Column mapping: categorical counts from `HouseholdSurvey.big_cattle` and `HouseholdSurvey.small_cattle`.

### Housing Typology
- Columns: `Typology`, `Kachcha`, `Semi Pucca`, `Pucca`, `Total`.
- Column mapping: counts of `HouseholdSurvey.house_type`.

### Digital Access (Digital media owned)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.digital_media_owned`.

### Digital Access (Drinking water source)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.drinking_water_source`.

### Digital Access (Adequacy of drinking water)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.adequate_water_supply`.

### Digital Access (JJM or other tap water connection)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.JJM_or_other_taped_water_connection`.

### Digital Access (Sanitation facilities)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.sanitation_facility`.

### Digital Access (Household toilets type)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.type_of_toilet` and `toilet_class`.

### Digital Access (De-sludge material)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.sludge_be_disposed_type`.

### Digital Access (Electricity connection)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.house_has_electric_connection`.

### Digital Access (Electricity source)
- Columns: `Category`, `No. of Household`, `%`.
- Column mapping: counts of `HouseholdSurvey.source_of_electricity`.

### Public Assets
- Columns: `Type`, `Number`, `Electricity`, `Drinking Water`, `Sanitation`, `Good Road Access`, `Building Condition (Good)`.
- Column mapping: `Commercial.type_of_occupancy` grouped; columns are counts of `house_has_electric_connection`, `drinking_water_source`, `toilet_facility`, `access_road_during_flood`, `building_quality` for each type.

### Road Length by Typology
- Columns: `Surface type`, `Length (km)`, `% to Total road length`.
- Column mapping: PostGIS `public.road_network` `rsur_type` and `length` sums (or GeoServer WFS fallback).

### Power Infrastructure
- Columns: `Asset`, `Number`.
- Column mapping: counts of `ElectricPole` and `Transformer` records.

### Facility Access
- Columns: `S. No.`, `Asset Type`, `Distance from Village`.
- Column mapping: `PRA_main` distance fields such as `nearest_higher_secondary_km`, `nearest_college_km`, `nearest_post_office_km`, etc.

### Land Use Classification
- Columns: `Landuse`, `Area (sqm)`, `%`.
- Column mapping: PostGIS `public.lulc.Class_name` grouped with `Area_SqM` sums; percent of total area.

---

## 4 Hazard, Vulnerability and Risk Assessment column mappings

### Hazard Presence
- Columns: `S. No.`, `Hazard`, `Frequency`, `Severity`, `Vulnerable Area/Group`.
- Column mapping: PRA fields; vulnerable area/group is fixed text in code.

### Earthquake MMI
- Columns: `PGA (g)`, `MMI`, `Category`, `Description`.
- Column mapping: static values in code.

### Flood Hazard Characteristics
- Columns: `S. No.`, `Flood characteristics`, `Details`.
- Column mapping: max or mode values from `HouseholdSurvey` flood-related fields.

### Flood Frequency at House
- Columns: `Flood frequency`, `Number of HHs reported`, `%`.
- Column mapping: keyword match in `HouseholdSurvey.house_affected_by_flood`.

### Flood Frequency in Agriculture Field
- Columns: `Flood frequency`, `Number of HHs reported`, `%`.
- Column mapping: keyword match in `HouseholdSurvey.your_agriculture_affected_by_flood`.

### Flood Duration in Agriculture Field
- Columns: `Flood duration`, `Number of HHs reported`, `%`.
- Column mapping: keyword match in `HouseholdSurvey.duration_of_flood_stay_in_your_agriculture_field`.

### Hazard Calendar
- Columns: months for each hazard row.
- Column mapping: static table rows unless a hazard calendar image exists in `VdmDistrictMapData.hazard_calendar`.

### Erosion Characteristics
- Columns: `Erosion/Accretion`, `Area (sq m)`, `Vulnerable stretch (km)`.
- Column mapping: SQL aggregates from `public.erosion_accretion` by `Class` for `Vill_ID`.

### Vulnerable Population
- Columns: `Category`, `Population`, `%`.
- Column mapping: sums from `HouseholdSurvey` population fields; percent of total population.

### Housing Flood Vulnerability
- Columns: `House Type`, `Number of HH`, `>1.0 m`, `High (0.5-1.0 m)`, `Moderate (0.3-0.5 m)`, `Low (<0.3 m)`.
- Column mapping: grouped `Risk_Assessment_Result.house_type_name` and `flood_hazard` thresholds.

### Housing Erosion Vulnerability
- Columns: `House Type`, `Number of HH`, `Severe`, `High`, `Moderate`, `Low`.
- Column mapping: grouped `Risk_Assessment_Result.house_type_name` and `erosion_class`.

### House Typology
- Columns: `Typology`, `Kachcha`, `Semi Pucca`, `Pucca`, `Total`.
- Column mapping: counts from `HouseholdSurvey.house_type`.

### Building Quality
- Columns: `Building quality`, `Number of HH`, `%`.
- Column mapping: counts from `HouseholdSurvey.building_quality` normalized to Good/Bad/Moderate.

### Plinth Height
- Columns: `Plinth height`, `Number of HH`, `%`.
- Column mapping: buckets from `HouseholdSurvey.plinth_or_stilt_height_ft`.

### Toilet Quality
- Columns: `Toilet structural quality`, `Number of HH`, `%`.
- Column mapping: counts from `HouseholdSurvey.toilet_class`.

### House Repair Expense
- Columns: `Expense range`, `Number of HH`, `%`.
- Column mapping: buckets from `HouseholdSurvey.amount_towards_flood_recovery_expenditure`.

### Household Flood Loss
- Columns: `Loss range`, `Number of HH`, `%`.
- Column mapping: buckets from `HouseholdSurvey.economic_loss_to_your_house_due_to_flood`.

### Agriculture Flood Loss
- Columns: `Loss range`, `Number of HH`, `%`.
- Column mapping: buckets from `HouseholdSurvey.loss_AgriLivli`.

### Road Flood Vulnerability
- Columns: `Flood class`, `Road length (km)`, `%`.
- Column mapping: sums from `VillageRoadInfo.road_length_m` grouped by `flood_class`.

### Road Erosion Vulnerability
- Columns: `Erosion class`, `Road length (km)`, `%`.
- Column mapping: sums from `VillageRoadInfoErosion.road_length_m` grouped by `erosion_class`.

### Educational Facilities
- Columns: `Facility type`, `Total`, `High`, `Moderate`, `Low`, `%`.
- Column mapping: `Critical_Facility` records filtered by school types and `flood_class`.

### Health Facilities
- Columns: `Facility type`, `Total`, `High`, `Moderate`, `Low`, `%`.
- Column mapping: `Critical_Facility` records filtered by health facility types and `flood_class`.

### Other Assets
- Columns: `Asset type`, `Total`, `High`, `Moderate`, `Low`, `%`.
- Column mapping: `Critical_Facility` non-education/non-health plus `ElectricPole` and `Transformer` counts by `flood_class`.

### Power Infrastructure
- Columns: `Asset type`, `Total`, `High`, `Moderate`, `Low`, `%`.
- Column mapping: `ElectricPole` and `Transformer` counts by `flood_class`.

### Livelihood Exposure, Sensitivity, Adaptive Capacity
- Columns: `Indicator`, `Description`, `Value`, `Score`.
- Column mapping: computed indicators from `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, and `PRA_main` fields; scores are derived in the respective LVI functions.

### Environmental Characteristics
- Columns: `Environmental characteristics`, `Details`.
- Column mapping: PRA fields and erosion length from `public.erosion_accretion`.

### Flood Loss Buildings
- Columns: `Exposure Category`, `Total Exposure Value`, `Loss`, `Loss %`.
- Column mapping: sums of `Risk_Assessment_Result.replacement_cost_inr` and `flood_loss` by `asset_type`.

### Flood Loss Roads Agriculture
- Columns: `Exposure Category`, `Total Exposure Value`, `Loss`, `Loss %`.
- Column mapping: sums of `VillageRoadInfo.replacement_cost_inr` and `flood_loss`; sums of `villageAgricultureLandFloodInfo.total_replacement_cost_inr` and `flood_loss`.

### Average Loss Roads Agriculture
- Columns: `Exposure Category`, `Average loss`.
- Column mapping: average loss computed from total loss divided by road length or agriculture area.

### Earthquake Loss Buildings
- Columns: `Exposure Category`, `Total Exposure Value`, `Loss`, `Loss %`.
- Column mapping: sums of `Risk_Assessment_Result.replacement_cost_inr` and `eq_loss` by `asset_type`.

### Cyclone Loss Buildings
- Columns: `Exposure Category`, `Total Exposure Value`, `Loss`, `Loss %`.
- Column mapping: sums of `Risk_Assessment_Result.replacement_cost_inr` and `wind_loss` by `asset_type`.

### Strong Wind Agriculture Loss
- Columns: `Exposure Category`, `Total Exposure Value`, `Loss`, `Loss %`.
- Column mapping: sums from `villageAgricultureLandWindInfo.total_replacement_cost_inr` and `wind_loss`.

---

## 5 Disaster Preparedness and Response Plan column mappings

All chapter 5 tables are static except team and shelter tables.

### Early Warning Systems
- Columns: `S. No.`, `Nature of early warning`, `Source`, `Lead time`.
- Column mapping: static rows.

### Disaster Mitigation Plan
- Columns: `S. No.`, `Work needs to done before the onset of the rainy season`, `Responsibility`.
- Column mapping: static rows.

### VDMC Members
- Columns: `S. No.`, `Designation`, `Name`, `Name of Father`, `Gender`, `Contact No`.
- Column mapping: `TaskForce` fields `fullname`, `father_name`, `gender`, `mobile_number`; designation derived from `position_responsibility`.

### Identified Safe Shelter
- Columns: `Type of Shelter`, `Rooms`, `Capacity`, `Contact Persons and Phone No.`, `Remarks`.
- Column mapping: `PRA_shelter` fields `name_of_shelter`, `number_of_rooms`, `capacity`, `contact_person`, `phone_number`.

### Search and Rescue Team, Relief Management Team, Shelter Management Team, First Aid Team
- Columns: `S. No.`, `Name`, `Father's Name`, `Gender`, `Phone number`, `Position/Responsibility`.
- Column mapping: `TaskForce` fields `fullname`, `father_name`, `gender`, `mobile_number`, `position_responsibility` filtered by `team_type`.

### Safe Shelter
- Columns: `Shelter`, `Single/Multi stories/Room`, `Capacity`, `Contact Persons and Phone No.`, `Remarks`.
- Column mapping: `PRA_shelter` fields `name_of_shelter`, `number_of_rooms`, `capacity`, `contact_person`, `phone_number`, `toilet_facility_available`, `drinking_water_facility_available`, `alternate_power_source`.

---

## 6 Mitigation Intervention and Investment Plan column mappings

All chapter 6 tables are static placeholder rows in `dummy_data.py` (all columns are hardcoded).

---

## 7 PRA Map and Field Photos

No tables. Images are fetched from `FieldImage` by `category` for the given village.


## Appendix: Field-by-field column mapping

Below, each table lists columns and the exact field or expression used per row. For static tables, columns are hardcoded in the PDF module.

### Client Information
- Column 1 (Field): hardcoded labels (`Client Address`, `Contact details`, `Email id`).
- Column 2 (Value): hardcoded strings (ASDMA address, CEO, email).

---

## 2 Summary Village Details (field-by-field)

### General Summary
- Column 1: hardcoded labels in `generate_general_summary_table`.
- Column 2:
  - Date of baseline data collection: hardcoded `Feb 2025`.
  - Revenue village: `tblVillage.name`.
  - Geographic area: `get_village_area` -> `public.lulc` sum of `ST_Area(ST_Transform(geom, 32646)) / 1,000,000`.
  - Block: `tblVillage.gram_panchayat.name`.
  - Revenue circle: `tblVillage.gram_panchayat.circle.name`.
  - District: `tblVillage.gram_panchayat.circle.district.name`.

### Socio-Economic Summary
- Column 1: hardcoded labels in `generate_socio_economic_summary_table`.
- Column 2:
  - Total population: sum of `HouseholdSurvey.number_of_males_including_children` + `number_of_females_including_children`.
  - Total households: `HouseholdSurvey` count.
  - Dominant house type: counts from `HouseholdSurvey.house_type` and percent of total.
  - Major landuse: `public.lulc` max area class and percent (via `get_major_land_use`).
  - Dominant occupational category: mode of `HouseholdSurvey.livelihood_primary` and percent of total households.
  - Sanitation facilities: distribution from `HouseholdSurvey.sanitation_facility` and `toilet_class`.

### Hazard Assessment
- Columns:
  - Hazard: hardcoded `Flood hazard`, `Erosion hazard`, `Strong Wind hazard`, `Earthquake hazard`.
  - Frequency: `PRA_main.flood_frequency`, `erosion_hazard_frequency`, `strong_wind_hazard_frequency`, `earthquake_hazard_frequency`.
  - Severity: `PRA_main.flood_severity`, `erosion_hazard_severity`, `strong_wind_hazard_severity`, `earthquake_hazard_severity`.

### Vulnerability Assessment
- Columns:
  - Indicator: hardcoded labels.
  - Value:
    - Economic status: BPL and PHH percentages from `HouseholdSurvey.economic_status`.
    - Vulnerable population: sums of `children_below_6_years`, `senior_citizens`, `pregnant_women`, `lactating_women`, `persons_with_disability_or_chronic_disease` as percent of total population.
    - Eroding river bank: length from `ExposureRiver` helper or erosion calculation.
    - Flood vulnerable houses: count of `HouseholdSurvey.flood_depth_m >= 0.5`.
    - Erosion vulnerable houses: count of `HouseholdSurvey.house_vulnerable_to_erosion = 'yes'`.
    - Flood vulnerable road: sum of `VillageRoadInfo.road_length_m` where `flood_depth_m > 0.5`, converted to km.
    - Erosion vulnerable road: sum of `VillageRoadInfoErosion.road_length_m` where `erosion_class in ('High','Severe')`, converted to km.
    - School: `Critical_Facility` school count and flood-affected count.
    - Livelihood vulnerability index: computed from `get_lvi_score` (averages exposure, sensitivity, adaptive capacity indices).

### Risk Assessment (excluding content loss)
- Columns:
  - Sector: hardcoded labels.
  - Flood: sums of loss in `Risk_Assessment_Result.flood_loss` by `asset_type`, or road/agri loss tables; displayed in INR.
  - Earthquake 475 RP: sums of `Risk_Assessment_Result.eq_loss`.
  - Strong wind 100 RP: sums of `Risk_Assessment_Result.wind_loss`.
  - Flood column header year: dominant `HouseholdSurvey.year_in_which_max_flood_experience_in_your_agriculture_land`.

### Mitigation Intervention
- Column 1: hardcoded labels in `dummy_data.getMitigationIntervention`.
- Column 2: hardcoded '-' values.

### Village Contacts (Important contact details)
- Columns:
  - S. No.: row index.
  - Name/designation: `LineDepartment.contact_name`.
  - Phone Number: `LineDepartment.phone_number`.
  - Position/Responsibility: `LineDepartment.section_master.section`.

### Emergency Toll Free Contact
- Columns:
  - S. No.: row index.
  - Important Contact: `LineDepartment.section_master.section`.
  - Contact Number: `LineDepartment.phone_number`.

---

## 3 Village Profile (field-by-field)

### Location Details
- Column 1: hardcoded labels.
- Column 2:
  - Revenue Village: `tblVillage.name`.
  - Block: `tblVillage.gram_panchayat.name`.
  - Revenue Circle: `tblVillage.gram_panchayat.circle.name`.
  - District: `tblVillage.gram_panchayat.circle.district.name`.
  - Distance from district headquarter (km): `PRA_main.distance_from_district_headquarter_km`.
  - Total area (sq km): `public.lulc` sum of `ST_Area`.
  - Average elevation (above MSL): `PRA_main.average_elevation_msl`.

### Demographic Profile
- Columns:
  - S. No.: row index.
  - Household Characteristic: hardcoded label.
  - Total:
    - No of Males: sum of `HouseholdSurvey.number_of_males_including_children`.
    - No of Females: sum of `HouseholdSurvey.number_of_females_including_children`.
    - Total Population: male + female totals.
    - Number of Households: `HouseholdSurvey` count.
    - Absentee House: hardcoded `None`.
    - Average Family Size: total population / total households.
    - Number of females per 1,000 males: `(females/males)*1000`.

### Socio Economic Status
- Columns:
  - S. No.: row index.
  - Social/Economic Status Household: normalized `HouseholdSurvey.social_status`.
  - AAY/APL/AY/BPL/PHH: counts from `HouseholdSurvey.economic_status` mapping.
  - Total: row sum of the above.
  - %: row total / total households.

### Agriculture Land Holding
- Columns:
  - S. No.: row index.
  - Agricultural land ownership (in bigha): fixed row labels.
  - Buckets `<0.5`, `0.5-1.5`, `1.5-2.5`, `>2.5`: bucket counts from `HouseholdSurvey.area_of_agriculture_land_owned_bigha`, split by `own_agriculture_land`.
  - Total: row sum.

### Annual Household Income
- Columns:
  - S. No.: row index.
  - Income Group (INR): fixed labels.
  - No. of Household: bucket counts from cleaned `HouseholdSurvey.approximate_income_earned_every_year_inr`.
  - %: bucket count / total households.

### Average Expenditure Breakdown
- Columns:
  - S. No.: row index.
  - Expenditure Category: fixed labels.
  - %: category sum / total sum; sums computed from `HouseholdSurvey` expense fields.

### Household Debt Liability
- Columns:
  - S. No.: row index.
  - Loan Amount (INR): fixed labels.
  - Number of households: bucket counts from `HouseholdSurvey.loan_amount`.
  - %: bucket count / total households.

### Primary Livelihood Distribution
- Columns:
  - Livelihood: normalized `HouseholdSurvey.livelihood_primary`.
  - No. of Household: count per category.
  - %: count / total households.

### Secondary Livelihood Distribution
- Columns:
  - Livelihood: normalized `HouseholdSurvey.livelihood_secondary`.
  - No. of Household: count per category.
  - %: count / total households.

### Crop Cultivation
- Columns:
  - Number of Crops Cultivated Every Year: fixed labels.
  - Household: count by `HouseholdSurvey.number_of_crops_normally_raised_every_year`.
  - %: count / total households.

### Livestock Ownership
- Columns:
  - Count: fixed labels (`0`, `<3`, `3-6`, `>6`).
  - HH with Big Cattle: counts from `HouseholdSurvey.big_cattle`.
  - %: big cattle count / total households.
  - HH with Small Cattle: counts from `HouseholdSurvey.small_cattle`.
  - %: small cattle count / total households.

### Housing Typology
- Columns:
  - Typology: fixed labels.
  - Kachcha/Semi Pucca/Pucca: counts from `HouseholdSurvey.house_type`.
  - Total: sum of above.

### Digital Access (Digital media owned)
- Columns:
  - Category: distinct `HouseholdSurvey.digital_media_owned`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (Drinking water source)
- Columns:
  - Category: distinct `HouseholdSurvey.drinking_water_source`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (Adequacy of drinking water)
- Columns:
  - Category: distinct `HouseholdSurvey.adequate_water_supply`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (JJM or other tap water connection)
- Columns:
  - Category: distinct `HouseholdSurvey.JJM_or_other_taped_water_connection`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (Sanitation facilities)
- Columns:
  - Category: distinct `HouseholdSurvey.sanitation_facility`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (Household toilets type)
- Columns:
  - Category: `HouseholdSurvey.type_of_toilet` and `HouseholdSurvey.toilet_class` categories.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (De-sludge material)
- Columns:
  - Category: distinct `HouseholdSurvey.sludge_be_disposed_type`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (Electricity connection)
- Columns:
  - Category: distinct `HouseholdSurvey.house_has_electric_connection`.
  - No. of Household: count per category.
  - %: count / total households.

### Digital Access (Electricity source)
- Columns:
  - Category: distinct `HouseholdSurvey.source_of_electricity`.
  - No. of Household: count per category.
  - %: count / total households.

### Public Assets
- Columns:
  - Type: fixed list (Anganwadi, LP School, Middle School, Religious Place).
  - Number: count of `Commercial` with `type_of_occupancy` per type.
  - Electricity: count where `Commercial.house_has_electric_connection = 'Yes'`.
  - Drinking Water: count where `Commercial.drinking_water_source` set.
  - Sanitation: count where `Commercial.toilet_facility` set.
  - Good Road Access: count where `Commercial.access_road_during_flood = 'Good Road'`.
  - Building Condition (Good): count where `Commercial.building_quality` in `Good`.

### Road Length by Typology
- Columns:
  - Surface Type: `public.road_network.RSur_Type` or `rsur_type`.
  - Length (km): sum of `public.road_network.Length` or `length` divided by 1000.
  - % to Total Road Length: length_km / total_length_km.

### Power Infrastructure
- Columns:
  - Asset: fixed labels (Electric post and network, Transformer).
  - Number: counts of `ElectricPole` and `Transformer` by village.

### Facility Access
- Columns:
  - S. No.: row index.
  - Asset Type: fixed labels.
  - Distance from Village: PRA fields like `nearest_higher_secondary_km`, `nearest_college_km`, `nearest_post_office_km`, `nearest_police_station_km`, `nearest_bank_atm_km`, `nearest_phc_km`, `nearest_chc_km`, `nearest_hospital_km`, `nearest_ambulance_km`.

### Land Use Classification
- Columns:
  - Landuse: `public.lulc.Class_name` normalized.
  - Area (sqm): sum of `public.lulc.Area_SqM` per class.
  - %: class_area / total_area.

---

## 4 Hazard, Vulnerability and Risk Assessment (field-by-field)

### Hazard Presence
- Columns:
  - S. No.: row index.
  - Hazard: fixed labels.
  - Frequency: `PRA_main` hazard frequency fields.
  - Severity: `PRA_main` hazard severity fields.
  - Vulnerable Area/Group: fixed text per row.

### Earthquake MMI
- Columns: all values are hardcoded in `getEarthquakeMMITableData`.

### Flood Hazard Characteristics
- Columns:
  - S. No.: row index.
  - Flood characteristics: fixed labels.
  - Details: max or mode values from `HouseholdSurvey.maximum_flood_height_in_house_ft`, `maximum_flood_height_experience_in_your_agriculture_ft`, `duration_of_flood_stay_in_your_agriculture_field`, `your_agriculture_affected_by_flood`, `year_in_which_maximum_flood_experience_in_your_house`.

### Flood Frequency at House
- Columns:
  - Flood frequency: category labels.
  - Number of HHs reported: count where `HouseholdSurvey.house_affected_by_flood` matches keywords.
  - %: count / total households.

### Flood Frequency in Agriculture Field
- Columns:
  - Flood frequency: category labels.
  - Number of HHs reported: count where `HouseholdSurvey.your_agriculture_affected_by_flood` matches keywords.
  - %: count / total households.

### Flood Duration in Agriculture Field
- Columns:
  - Flood duration: category labels.
  - Number of HHs reported: count where `HouseholdSurvey.duration_of_flood_stay_in_your_agriculture_field` matches keywords.
  - %: count / total households.

### Hazard Calendar
- Columns: months and categories are hardcoded unless `VdmDistrictMapData.hazard_calendar` image is used.

### Erosion Characteristics
- Columns:
  - Erosion/Accretion: `public.erosion_accretion.Class`.
  - Area (sq m): sum of `ST_Area(ST_Transform(geom,32646))`.
  - Vulnerable stretch (km): sum of `ST_Length(ST_Boundary(geom)) / 1000`.

### Vulnerable Population
- Columns:
  - Category: fixed labels.
  - Population: sums of `HouseholdSurvey` population fields.
  - %: category sum / total population.

### Housing Flood Vulnerability
- Columns:
  - House Type: `Risk_Assessment_Result.house_type_name`.
  - Number of HH: count by type.
  - >1.0, High, Moderate, Low: counts based on `Risk_Assessment_Result.flood_hazard` thresholds.

### Housing Erosion Vulnerability
- Columns:
  - House Type: `Risk_Assessment_Result.house_type_name`.
  - Number of HH: count by type.
  - Severe/High/Moderate/Low: counts by `Risk_Assessment_Result.erosion_class`.

### House Typology
- Columns:
  - Kachcha/Semi Pucca/Pucca: counts from `HouseholdSurvey.house_type`.
  - % row: percent of total.

### Building Quality
- Columns:
  - Building quality: Good/Bad/Moderate from `HouseholdSurvey.building_quality`.
  - Number of HH: counts.
  - %: count / total households.

### Plinth Height
- Columns:
  - Plinth height bucket: ranges from `HouseholdSurvey.plinth_or_stilt_height_ft`.
  - Number of HH: bucket counts.
  - %: count / total households.

### Toilet Quality
- Columns:
  - Toilet class: values from `HouseholdSurvey.toilet_class`.
  - Number of HH: counts.
  - %: count / total households.

### House Repair Expense
- Columns:
  - Expense range: buckets from `HouseholdSurvey.amount_towards_flood_recovery_expenditure`.
  - Number of HH: counts.
  - %: count / total households.

### Household Flood Loss
- Columns:
  - Loss range: buckets from `HouseholdSurvey.economic_loss_to_your_house_due_to_flood`.
  - Number of HH: counts.
  - %: count / total households.

### Agriculture Flood Loss
- Columns:
  - Loss range: buckets from `HouseholdSurvey.loss_AgriLivli`.
  - Number of HH: counts.
  - %: count / total households.

### Road Flood Vulnerability
- Columns:
  - Flood class: `VillageRoadInfo.flood_class`.
  - Road length (km): sum of `VillageRoadInfo.road_length_m` / 1000.
  - %: length / total length.

### Road Erosion Vulnerability
- Columns:
  - Erosion class: `VillageRoadInfoErosion.erosion_class`.
  - Road length (km): sum of `VillageRoadInfoErosion.road_length_m` / 1000.
  - %: length / total length from `VillageRoadInfo`.

### Educational Facilities
- Columns:
  - Facility type: fixed labels.
  - Total: count of `Critical_Facility` school types.
  - High/Moderate/Low: counts by `Critical_Facility.flood_class`.
  - %: count / total.

### Health Facilities
- Columns:
  - Facility type: fixed labels.
  - Total: count of `Critical_Facility` health types.
  - High/Moderate/Low: counts by `Critical_Facility.flood_class`.
  - %: count / total.

### Other Assets
- Columns:
  - Asset type: fixed labels.
  - Total/High/Moderate/Low: counts from `Critical_Facility`, `ElectricPole`, `Transformer` grouped by `flood_class`.
  - %: count / total.

### Power Infrastructure
- Columns:
  - Asset type: fixed labels.
  - Total/High/Moderate/Low: counts from `ElectricPole` and `Transformer` by `flood_class`.
  - %: count / total.

### Livelihood Exposure/Sensitivity/Adaptive Capacity
- Columns:
  - Indicator: fixed labels.
  - Description: fixed labels.
  - Value: computed from survey/road/PRA fields.
  - Score: derived indicator scoring in respective functions.

### Environmental Characteristics
- Columns:
  - Environmental characteristics: fixed labels.
  - Details: `PRA_main` fields plus erosion length.

### Flood Loss Buildings
- Columns:
  - Exposure Category: fixed labels.
  - Total Exposure Value (INR Crore): sum of `Risk_Assessment_Result.replacement_cost_inr` / 10000000.
  - Loss (INR Crore): sum of `Risk_Assessment_Result.flood_loss` / 10000000.
  - Loss %: loss / exposure.

### Flood Loss Roads Agriculture
- Columns:
  - Exposure Category: fixed labels.
  - Total Exposure Value: sum of `VillageRoadInfo.replacement_cost_inr` and `villageAgricultureLandFloodInfo.total_replacement_cost_inr` (crore or lakh).
  - Loss: sum of `VillageRoadInfo.flood_loss` and `villageAgricultureLandFloodInfo.flood_loss`.
  - Loss %: loss / exposure.

### Average Loss Roads Agriculture
- Columns:
  - Exposure Category: fixed labels.
  - Average loss: `total_loss / total_length_or_area` from road/agri tables.

### Earthquake Loss Buildings
- Columns:
  - Exposure Category: fixed labels.
  - Total Exposure Value (INR Crore): sum of `Risk_Assessment_Result.replacement_cost_inr` / 10000000.
  - Loss (INR Crore): sum of `Risk_Assessment_Result.eq_loss` / 10000000.
  - Loss %: loss / exposure.

### Cyclone Loss Buildings
- Columns:
  - Exposure Category: fixed labels.
  - Total Exposure Value (INR Crore): sum of `Risk_Assessment_Result.replacement_cost_inr` / 10000000.
  - Loss (INR Crore): sum of `Risk_Assessment_Result.wind_loss` / 10000000.
  - Loss %: loss / exposure.

### Strong Wind Agriculture Loss
- Columns:
  - Exposure Category: fixed label.
  - Total Exposure Value (INR): sum of `villageAgricultureLandWindInfo.total_replacement_cost_inr`.
  - Loss (INR): sum of `villageAgricultureLandWindInfo.wind_loss`.
  - Loss %: loss / exposure.

---

## 5 Disaster Preparedness and Response Plan (field-by-field)

### Early Warning Systems
- Columns: all hardcoded rows in `draw_disaster_preparedness_and_response_plan`.

### Disaster Mitigation Plan
- Columns: all hardcoded rows in `draw_disaster_preparedness_and_response_plan`.

### VDMC Members
- Columns:
  - S. No.: row index.
  - Designation: `TaskForce.position_responsibility` mapped to Chairperson/Member.
  - Name: `TaskForce.fullname`.
  - Name of Father: `TaskForce.father_name`.
  - Gender: `TaskForce.gender`.
  - Contact No: `TaskForce.mobile_number`.

### Identified Safe Shelter
- Columns:
  - Type of Shelter: `PRA_shelter.name_of_shelter`.
  - Rooms: `PRA_shelter.number_of_rooms`.
  - Capacity: `PRA_shelter.capacity`.
  - Contact Persons and Phone No.: `PRA_shelter.contact_person` + `phone_number`.
  - Remarks: hardcoded `N/A`.

### Search and Rescue Team / Relief Management Team / Shelter Management Team / First Aid Team
- Columns:
  - S. No.: row index.
  - Name: `TaskForce.fullname`.
  - Father's Name: `TaskForce.father_name`.
  - Gender: `TaskForce.gender`.
  - Phone number: `TaskForce.mobile_number`.
  - Position/Responsibility: `TaskForce.position_responsibility`.

### Safe Shelter
- Columns:
  - Shelter: `PRA_shelter.name_of_shelter`.
  - Single/Multi stories/Room: `PRA_shelter.number_of_rooms`.
  - Capacity: `PRA_shelter.capacity`.
  - Contact Persons and Phone No.: `PRA_shelter.contact_person` + `phone_number`.
  - Remarks: `PRA_shelter.toilet_facility_available`, `drinking_water_facility_available`, `alternate_power_source` joined.

---

## 6 Mitigation Intervention and Investment Plan (field-by-field)

All chapter 6 tables are hardcoded placeholder rows in `dummy_data.py`.

---

## 7 PRA Map and Field Photos

No tables. Images are loaded from `FieldImage` where `FieldImage.category` matches the section name.


## Appendix: ORM/SQL snippets per table

Below, each table includes a minimal ORM or SQL snippet that mirrors how the data is fetched in code. Static tables are noted as static.

### Client Information
- Static table: no ORM/SQL; values are hardcoded.

---

## 2 Summary Village Details (snippets)

### General Summary
```python
village = tblVillage.objects.select_related(
    'gram_panchayat',
    'gram_panchayat__circle',
    'gram_panchayat__circle__district'
).get(id=village_id)
```
```sql
SELECT COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000.0, 0)
FROM public.lulc
WHERE "Vill_ID" = %s;
```

### Socio-Economic Summary
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
```
```sql
SELECT "Class_name", SUM("Area_SqM") AS total_area
FROM public.lulc
WHERE "Vill_ID" = %s
GROUP BY "Class_name"
ORDER BY total_area DESC
LIMIT 1;
```

### Hazard Assessment
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```

### Vulnerability Assessment
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
roads_flood = VillageRoadInfo.objects.filter(village_id=village_id, flood_depth_m__gt=0.5)
roads_erosion = VillageRoadInfoErosion.objects.filter(village_id=village_id, erosion_class__in=['High','Severe'])
```

### Risk Assessment (excluding content loss)
```python
risk = Risk_Assessment_Result.objects.filter(village_id=village_id)
road_loss = VillageRoadInfo.objects.filter(village_id=village_id).aggregate(total=Sum('flood_loss'))
```

### Mitigation Intervention
- Static table: no ORM/SQL.

### Village Contacts (Important contact details)
```python
officials = LineDepartment.objects.filter(
    village_id=village_id,
    official_number__iexact='yes'
).select_related('section_master')
```

### Emergency Toll Free Contact
```python
officials = LineDepartment.objects.filter(
    village_id=village_id,
    official_number__iexact='no'
).select_related('section_master')
```

---

## 3 Village Profile (snippets)

### Location Details
```python
village = tblVillage.objects.select_related('gram_panchayat__circle__district').get(id=village_id)
```
```sql
SELECT COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000, 0)
FROM public.lulc
WHERE "Vill_ID" = %s;
```

### Demographic Profile
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    total_males=Sum(Cast('number_of_males_including_children', IntegerField())),
    total_females=Sum(Cast('number_of_females_including_children', IntegerField())),
)
```

### Socio Economic Status
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# iterate and map social_status/economic_status to buckets
```

### Agriculture Land Holding
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# bucket by area_of_agriculture_land_owned_bigha and own_agriculture_land
```

### Annual Household Income
```python
households = HouseholdSurvey.objects.filter(village_id=village_id).annotate(
    income_clean=Replace(Replace('approximate_income_earned_every_year_inr', Value(','), Value('')),
                         Value(' '), Value('')),
    income_amt=Case(When(income_clean__regex=r'^\d+$', then=Cast('income_clean', IntegerField())),
                    default=None, output_field=IntegerField())
)
```

### Average Expenditure Breakdown
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# sum amount_spent_for_agriculture_livestock, expense_on_festival_marriage..., etc.
```

### Household Debt Liability
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# bucket loan_amount into ranges
```

### Primary Livelihood Distribution
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .exclude(livelihood_primary__isnull=True)
    .values('livelihood_primary')
    .annotate(count=Count('livelihood_primary'))
```

### Secondary Livelihood Distribution
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .exclude(livelihood_secondary__isnull=True)
    .values('livelihood_secondary')
    .annotate(count=Count('livelihood_secondary'))
```

### Crop Cultivation
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('number_of_crops_normally_raised_every_year')
    .annotate(count=Count('id'))
```

### Livestock Ownership
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('big_cattle', 'small_cattle')
```

### Housing Typology
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    kachcha=Count('id', filter=Q(house_type__iexact='Kachcha')),
    semi_pucca=Count('id', filter=Q(house_type__iexact='Semi pucca')),
    pucca=Count('id', filter=Q(house_type__iexact='Pucca')),
)
```

### Digital Access (Digital media owned)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('digital_media_owned').annotate(count=Count('id'))
```

### Digital Access (Drinking water source)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('drinking_water_source').annotate(count=Count('id'))
```

### Digital Access (Adequacy of drinking water)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('adequate_water_supply').annotate(count=Count('id'))
```

### Digital Access (JJM or other tap water connection)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('JJM_or_other_taped_water_connection').annotate(count=Count('id'))
```

### Digital Access (Sanitation facilities)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('sanitation_facility').annotate(count=Count('id'))
```

### Digital Access (Household toilets type)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('type_of_toilet').annotate(count=Count('id'))
```

### Digital Access (De-sludge material)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('sludge_be_disposed_type').annotate(count=Count('id'))
```

### Digital Access (Electricity connection)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('house_has_electric_connection').annotate(count=Count('id'))
```

### Digital Access (Electricity source)
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('source_of_electricity').annotate(count=Count('id'))
```

### Public Assets
```python
Commercial.objects.filter(village_id=village_id, type_of_occupancy='Anganwadi')
```

### Road Length by Typology
```sql
SELECT "RSur_Type", SUM("Length") AS total_length
FROM public.road_network
WHERE "Vill_ID" = %s
GROUP BY "RSur_Type";
```

### Power Infrastructure
```python
ElectricPole.objects.filter(village_id=village_id).count()
Transformer.objects.filter(village_id=village_id).count()
```

### Facility Access
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```

### Land Use Classification
```sql
SELECT "Class_name", SUM("Area_SqM") AS total_area
FROM public.lulc
WHERE "Vill_ID" = %s
GROUP BY "Class_name";
```

---

## 4 Hazard, Vulnerability and Risk Assessment (snippets)

### Hazard Presence
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```

### Earthquake MMI
- Static table: no ORM/SQL.

### Flood Hazard Characteristics
```python
qs = HouseholdSurvey.objects.filter(village_id=village_id)
```

### Flood Frequency at House
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .filter(house_affected_by_flood__icontains='every')
```

### Flood Frequency in Agriculture Field
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .filter(your_agriculture_affected_by_flood__icontains='every')
```

### Flood Duration in Agriculture Field
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .filter(duration_of_flood_stay_in_your_agriculture_field__icontains='3-7')
```

### Hazard Calendar
- Static table or `VdmDistrictMapData.hazard_calendar` image.

### Erosion Characteristics
```sql
SELECT "Class",
       COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))), 0) AS area_sqm,
       COALESCE(SUM(ST_Length(ST_Transform(ST_Boundary(geom), 32646))) / 1000, 0) AS length_km
FROM public.erosion_accretion
WHERE "Vill_ID" = %s
GROUP BY "Class";
```

### Vulnerable Population
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    children=Sum(Cast('children_below_6_years', FloatField())),
    seniors=Sum(Cast('senior_citizens', FloatField())),
    pregnant=Sum(Cast('pregnant_women', FloatField())),
    lactating=Sum(Cast('lactating_women', FloatField())),
    disabled=Sum(Cast('persons_with_disability_or_chronic_disease', FloatField())),
)
```

### Housing Flood Vulnerability
```python
Risk_Assessment_Result.objects.filter(village_id=village_id, asset_type='household')
```

### Housing Erosion Vulnerability
```python
Risk_Assessment_Result.objects.filter(village_id=village_id, asset_type='household')
```

### House Typology
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('house_type')
    .annotate(count=Count('id'))
```

### Building Quality
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('building_quality', flat=True)
```

### Plinth Height
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('plinth_or_stilt_height_ft', flat=True)
```

### Toilet Quality
```python
HouseholdSurvey.objects.filter(village_id=village_id).values('toilet_class').annotate(count=Count('id'))
```

### House Repair Expense
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('amount_towards_flood_recovery_expenditure', flat=True)
```

### Household Flood Loss
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('economic_loss_to_your_house_due_to_flood', flat=True)
```

### Agriculture Flood Loss
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('loss_AgriLivli', flat=True)
```

### Road Flood Vulnerability
```python
VillageRoadInfo.objects.filter(village_id=village_id).values('flood_class').annotate(total=Sum('road_length_m'))
```

### Road Erosion Vulnerability
```python
VillageRoadInfoErosion.objects.filter(village_id=village_id).values('erosion_class').annotate(total=Sum('road_length_m'))
```

### Educational Facilities
```python
Critical_Facility.objects.filter(village_id=village_id, occupancy_type__icontains='school')
```

### Health Facilities
```python
Critical_Facility.objects.filter(village_id=village_id, occupancy_type__icontains='hospital')
```

### Other Assets
```python
Critical_Facility.objects.filter(village_id=village_id).exclude(occupancy_type__icontains='school')
```

### Power Infrastructure
```python
ElectricPole.objects.filter(village_id=village_id)
Transformer.objects.filter(village_id=village_id)
```

### Livelihood Exposure/Sensitivity/Adaptive Capacity
```python
HouseholdSurvey.objects.filter(village_id=village_id)
```

### Environmental Characteristics
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```

### Flood Loss Buildings
```python
Risk_Assessment_Result.objects.filter(village_id=village_id).values('asset_type').annotate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('flood_loss')
)
```

### Flood Loss Roads Agriculture
```python
VillageRoadInfo.objects.filter(village_id=village_id).aggregate(total_exposure=Sum('replacement_cost_inr'), total_loss=Sum('flood_loss'))
```

### Average Loss Roads Agriculture
```python
VillageRoadInfo.objects.filter(village_id=village_id).aggregate(total_loss=Sum('flood_loss'), total_len=Sum('road_length_m'))
```

### Earthquake Loss Buildings
```python
Risk_Assessment_Result.objects.filter(village_id=village_id).values('asset_type').annotate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('eq_loss')
)
```

### Cyclone Loss Buildings
```python
Risk_Assessment_Result.objects.filter(village_id=village_id).values('asset_type').annotate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('wind_loss')
)
```

### Strong Wind Agriculture Loss
```python
villageAgricultureLandWindInfo.objects.filter(village_id=village_id).aggregate(
    total_exposure=Sum('total_replacement_cost_inr'),
    total_loss=Sum('wind_loss')
)
```

---

## 5 Disaster Preparedness and Response Plan (snippets)

### Early Warning Systems
- Static table: no ORM/SQL.

### Disaster Mitigation Plan
- Static table: no ORM/SQL.

### VDMC Members
```python
TaskForce.objects.filter(village_id=village_id, team_type='VLCDMC')
```

### Identified Safe Shelter
```python
PRA_shelter.objects.filter(village_id=village_id)
```

### Search and Rescue Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='Search & rescue')
```

### Relief Management Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='Relief management team')
```

### Shelter Management Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='Shelter Management team')
```

### First Aid Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='First Aid team')
```

### Safe Shelter
```python
PRA_shelter.objects.filter(village_id=village_id)
```

---

## 6 Mitigation Intervention and Investment Plan (snippets)

All chapter 6 tables are static placeholders in `dummy_data.py` (no ORM/SQL).

---

## 7 PRA Map and Field Photos

No tables. Images are loaded from `FieldImage` by `category`.


## Appendix: Full ORM/SQL snippets as in code

This appendix provides the exact query shapes used in code (or the closest full snippet), including helper queries and fallbacks.

---

## 2 Summary Village Details (full snippets)

### General Summary
```python
village = tblVillage.objects.select_related(
    'gram_panchayat',
    'gram_panchayat__circle',
    'gram_panchayat__circle__district'
).get(id=village_id)
```
```python
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'lulc'
        )
    """)
    table_exists = cursor.fetchone()[0]
    if table_exists:
        cursor.execute("""
            SELECT COALESCE(
                SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000.0,
                0
            ) AS area_sqkm
            FROM public.lulc
            WHERE "Vill_ID" = %s
        """, [village_code])
        row = cursor.fetchone()
```
```python
lulc_data = getLULCData(village_id, 'assam', 'lulc', True)
```

### Socio-Economic Summary
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
```
```python
households_n = households.annotate(
    house_type_n=Lower(Trim('house_type')),
    toilet_class_n=Lower(Trim('toilet_class')),
    sanitation_type_n=Lower(Trim('sanitation_facility')),
    livelihood_n=Lower(Trim('livelihood_primary')),
)
```
```python
own_households = households_n.filter(sanitation_type_n='own')
pucca_toilet = own_households.filter(toilet_class_n='pucca').count()
semi_pucca_toilet = own_households.filter(toilet_class_n='semi pucca').count()
kachcha_toilet = own_households.filter(toilet_class_n='kachcha').count()
```
```python
kachcha = households_n.filter(house_type_n='kachcha').count()
semi_pucca = households_n.filter(house_type_n='semi pucca').count()
pucca = households_n.filter(house_type_n='pucca').count()
```
```python
livelihood_qs = (
    households_n
    .exclude(livelihood_n__isnull=True)
    .exclude(livelihood_n='')
    .values('livelihood_n')
    .annotate(count=Count('livelihood_n'))
    .order_by('-count')
)
```
```python
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT "Class_name", SUM("Area_SqM") as total_area
        FROM public.lulc
        WHERE "Vill_ID" = %s
        GROUP BY "Class_name"
        ORDER BY total_area DESC
        LIMIT 1
    """, [village_code])
    row = cursor.fetchone()
```

### Hazard Assessment
```python
pra_data = PRA_main.objects.filter(village_id=village_id).first()
```

### Vulnerability Assessment
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
```
```python
bpl_count = 0
phh_count = 0
for h in households:
    economic = (h.economic_status or "").lower()
    if economic == 'bpl' or 'below poverty line' in economic:
        bpl_count += 1
    elif economic == 'phh' or 'priority household' in economic:
        phh_count += 1
```
```python
flood_vulnerable_houses = households.filter(flood_depth_m__gte=0.5).count()
```
```python
erosion_vulnerable_houses = households.filter(
    house_vulnerable_to_erosion__iexact='yes'
).count()
```
```python
flood_road_length_m = VillageRoadInfo.objects.filter(
    village_id=village_id,
    flood_depth_m__gt=0.5
).aggregate(total=Sum('road_length_m'))['total'] or 0
```
```python
erosion_road_length_m = VillageRoadInfoErosion.objects.filter(
    village_id=village_id
).filter(
    Q(erosion_class__iexact='Severe') |
    Q(erosion_class__iexact='High')
).aggregate(total=Sum('road_length_m'))['total'] or 0
```
```python
schools_qs = Critical_Facility.objects.filter(
    village_id=village_id,
    occupancy_type__icontains='school'
)
```
```python
lvi_score = get_lvi_score(village_id)
```

### Risk Assessment (excluding content loss)
```python
risk_data = Risk_Assessment_Result.objects.filter(village_id=village_id)
```
```python
dominant_year_obj = (
    HouseholdSurvey.objects
    .filter(
        village_id=village_id,
        year_in_which_max_flood_experience_in_your_agriculture_land__isnull=False
    )
    .exclude(year_in_which_max_flood_experience_in_your_agriculture_land='')
    .values('year_in_which_max_flood_experience_in_your_agriculture_land')
    .annotate(count=Count('id'))
    .order_by('-count')
    .first()
)
```
```python
household_flood = (
    risk_data.filter(asset_type='household')
    .aggregate(Sum('flood_loss'))['flood_loss__sum'] or 0
) / 10000000
```
```python
road_risk_flood = (
    VillageRoadInfo.objects.filter(village_id=village_id)
    .aggregate(total=Sum('flood_loss'))['total'] or 0
) / 10000000
```
```python
agriculture_flood = (
    villageAgricultureLandFloodInfo.objects.filter(village_id=village_id)
    .aggregate(total=Sum('flood_loss'))['total'] or 0
) / 10000000
```

---

## 3 Village Profile (full snippets)

### Location Details
```python
village = tblVillage.objects.select_related(
    'gram_panchayat__circle__district'
).get(id=village_id)
```
```python
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'lulc'
        )
    """)
    if cursor.fetchone()[0]:
        cursor.execute("""
            SELECT COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000,0)
            FROM public.lulc
            WHERE "Vill_ID" = %s
        """, [village_code])
        row = cursor.fetchone()
```
```python
pra_data = PRA_main.objects.filter(village_id=village_id).first()
```

### Demographic Profile
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    total_males=Coalesce(
        Sum(Cast(Cast('number_of_males_including_children', FloatField()), IntegerField())),
        0
    ),
    total_females=Coalesce(
        Sum(Cast(Cast('number_of_females_including_children', FloatField()), IntegerField())),
        0
    ),
)
```

### Socio Economic Status
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for hh in households:
    social_key = normalize_social_status(hh.social_status)
    economic_key = map_economic_status(hh.economic_status)
```

### Agriculture Land Holding
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# bucket area_of_agriculture_land_owned_bigha and own_agriculture_land
```

### Annual Household Income
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)

households = households.annotate(
    income_clean=Replace(
        Replace('approximate_income_earned_every_year_inr', Value(','), Value('')),
        Value(' '), Value('')
    )
).annotate(
    income_amt=Case(
        When(income_clean__regex=r'^\d+$', then=Cast('income_clean', IntegerField())),
        default=None,
        output_field=IntegerField()
    )
)
```

### Average Expenditure Breakdown
```python
households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
```
```python
agri_sum = sum(safe_decimal(h.amount_spent_for_agriculture_livestock) for h in households)
festival_sum = sum(safe_decimal(h.expense_on_festival_marriage_and_other_social_occassions) for h in households)
repair_sum = sum(safe_decimal(h.expense_on_house_repair) for h in households)
tobacco_sum = sum(safe_decimal(h.expense_on_tobacco_liquor) for h in households)
education_sum = sum(safe_decimal(h.expense_on_education) for h in households)
health_sum = sum(safe_decimal(h.expense_on_health) for h in households)
food_sum = sum(safe_decimal(h.expense_on_food) for h in households)
```

### Household Debt Liability
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# bucket loan_amount values
```

### Primary/Secondary Livelihood Distribution
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .exclude(livelihood_primary__isnull=True)
    .values('livelihood_primary')
    .annotate(count=Count('livelihood_primary'))
    .order_by('-count')
```
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .exclude(livelihood_secondary__isnull=True)
    .values('livelihood_secondary')
    .annotate(count=Count('livelihood_secondary'))
    .order_by('-count')
```

### Crop Cultivation
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('number_of_crops_normally_raised_every_year')
    .annotate(count=Count('id'))
```

### Livestock Ownership
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
big_0 = households.filter(big_cattle='No Big Cattle').count()
small_0 = households.filter(small_cattle='No Small Cattle').count()
```

### Housing Typology
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    kachcha=Count('id', filter=Q(house_type__iexact='Kachcha')),
    semi_pucca=Count('id', filter=Q(house_type__iexact='Semi pucca')),
    pucca=Count('id', filter=Q(house_type__iexact='Pucca'))
)
```

### Digital Access (various)
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('digital_media_owned')
    .annotate(count=Count('id'))
```
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('drinking_water_source')
    .annotate(count=Count('id'))
```

### Public Assets
```python
facilities = Commercial.objects.filter(village=village_id)
```

### Road Length by Typology
```sql
SELECT "RSur_Type", SUM("Length") AS total_length
FROM public.road_network
WHERE "Vill_ID" = %s
GROUP BY "RSur_Type"
ORDER BY total_length DESC;
```
```sql
SELECT rsur_type, SUM(length) AS total_length
FROM public.road_network
WHERE vill_id = %s
GROUP BY rsur_type
ORDER BY total_length DESC;
```

### Power Infrastructure
```python
ElectricPole.objects.filter(village_id=village_id).count()
Transformer.objects.filter(village_id=village_id).count()
```

### Facility Access
```python
pra_data = PRA_main.objects.filter(village_id=village_id).first()
```

### Land Use Classification
```sql
SELECT "Class_name", SUM("Area_SqM") as total_area
FROM public.lulc
WHERE "Vill_ID" = %s
GROUP BY "Class_name";
```

---

## 4 Hazard, Vulnerability and Risk Assessment (full snippets)

### Hazard Presence
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```

### Flood Hazard Characteristics
```python
qs = HouseholdSurvey.objects.filter(village_id=village_id)
max_house_flood = qs.exclude(maximum_flood_height_in_house_ft__isnull=True)
```

### Flood Frequency at House
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for label, keywords in FLOOD_FREQUENCY_CATEGORIES:
    q = Q()
    for k in keywords:
        q |= Q(house_affected_by_flood__icontains=k)
    count = households.filter(q).count()
```

### Flood Frequency in Agriculture Field
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for label, keywords in FLOOD_FREQUENCY_CATEGORIES:
    q = Q()
    for k in keywords:
        q |= Q(your_agriculture_affected_by_flood__icontains=k)
    count = households.filter(q).count()
```

### Flood Duration in Agriculture Field
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for label, keywords in FLOOD_DURATION_CATEGORIES:
    q = Q()
    for k in keywords:
        q |= Q(duration_of_flood_stay_in_your_agriculture_field__icontains=k)
    count = households.filter(q).count()
```

### Erosion Characteristics
```sql
SELECT "Class",
       COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))), 0) AS area_sqm,
       COALESCE(SUM(ST_Length(ST_Transform(ST_Boundary(geom), 32646))) / 1000, 0) AS length_km
FROM public.erosion_accretion
WHERE "Vill_ID" = %s
GROUP BY "Class";
```

### Vulnerable Population
```python
qs = HouseholdSurvey.objects.filter(village=village_id)
qs.aggregate(
    children=Sum(Cast('children_below_6_years', FloatField())),
    seniors=Sum(Cast('senior_citizens', FloatField())),
    pregnant=Sum(Cast('pregnant_women', FloatField())),
    lactating=Sum(Cast('lactating_women', FloatField())),
    disabled=Sum(Cast('persons_with_disability_or_chronic_disease', FloatField())),
    males=Sum(Cast('number_of_males_including_children', FloatField())),
    females=Sum(Cast('number_of_females_including_children', FloatField())),
)
```

### Housing Flood/Erosion Vulnerability
```python
Risk_Assessment_Result.objects.filter(village=village_id, asset_type='household')
```

### House Typology
```python
HouseholdSurvey.objects.filter(village=village_id).aggregate(
    kachcha=Count('id', filter=Q(house_type__iexact='Kachcha')),
    semi_pucca=Count('id', filter=Q(house_type__iexact='Semi pucca')),
    pucca=Count('id', filter=Q(house_type__iexact='Pucca')),
)
```

### Road Flood/Erosion Vulnerability
```python
VillageRoadInfo.objects.filter(village_id=village_id).values('flood_class').annotate(total=Sum('road_length_m'))
```
```python
VillageRoadInfoErosion.objects.filter(village_id=village_id).values('erosion_class').annotate(total=Sum('road_length_m'))
```

### Educational Facilities
```python
Critical_Facility.objects.filter(village_id=village_id, occupancy_type__icontains='school')
```

### Power Infrastructure
```python
ElectricPole.objects.filter(village_id=village_id)
Transformer.objects.filter(village_id=village_id)
```

### Flood Loss Buildings
```python
Risk_Assessment_Result.objects.filter(village=village_id).values('asset_type').annotate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('flood_loss')
)
```

### Flood Loss Roads Agriculture
```python
VillageRoadInfo.objects.filter(village=village_id).aggregate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('flood_loss')
)
```
```python
villageAgricultureLandFloodInfo.objects.filter(village=village_id).aggregate(
    total_exposure=Sum('total_replacement_cost_inr'),
    total_loss=Sum('flood_loss')
)
```

### Earthquake/Cyclone Loss Buildings
```python
Risk_Assessment_Result.objects.filter(village=village_id).values('asset_type').annotate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('eq_loss')
)
```
```python
Risk_Assessment_Result.objects.filter(village=village_id).values('asset_type').annotate(
    total_exposure=Sum('replacement_cost_inr'),
    total_loss=Sum('wind_loss')
)
```

---

## 5 Disaster Preparedness and Response Plan (full snippets)

### VDMC Members
```python
TaskForce.objects.filter(village_id=village_id, team_type='VLCDMC')
```

### Identified Safe Shelter / Safe Shelter
```python
PRA_shelter.objects.filter(village_id=village_id)
```

### Search and Rescue Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='Search & rescue')
```

### Relief Management Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='Relief management team')
```

### Shelter Management Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='Shelter Management team')
```

### First Aid Team
```python
TaskForce.objects.filter(village_id=village_id, team_type='First Aid team')
```

---

## 6 Mitigation Intervention and Investment Plan (full snippets)

All chapter 6 tables are static placeholders in `dummy_data.py` (no ORM/SQL).

---

## 7 PRA Map and Field Photos

No tables. Images loaded from `FieldImage` by `category`.

### General Summary
- Data source: `tblVillage` and PostGIS `public.lulc`.
- Database tables used: `tblVillage`, `public.lulc`.
- Query/logic: fetch village hierarchy; calculate area using `ST_Area`; major landuse via `getLULCData`.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `generate_general_summary_table`.
- Column mapping:
  - Column 1: hardcoded labels.
  - Column 2:
    - Date of baseline data collection: hardcoded `Feb 2025`.
    - Revenue village: `tblVillage.name`.
    - Geographic area: sum of `ST_Area` in `public.lulc` for `Vill_ID`.
    - Block: `tblVillage.gram_panchayat.name`.
    - Revenue circle: `tblVillage.gram_panchayat.circle.name`.
    - District: `tblVillage.gram_panchayat.circle.district.name`.
- ORM/SQL snippet:
```python
village = tblVillage.objects.select_related(
    'gram_panchayat',
    'gram_panchayat__circle',
    'gram_panchayat__circle__district'
).get(id=village_id)
```
```sql
SELECT COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000.0, 0)
FROM public.lulc
WHERE "Vill_ID" = %s;
```

### Socio-Economic Summary
- Data source: `HouseholdSurvey` and PostGIS `public.lulc`.
- Database tables used: `HouseholdSurvey`, `public.lulc`.
- Query/logic: counts households and population; dominant house type and occupation from survey; sanitation summary from survey; major landuse from `public.lulc`.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `generate_socio_economic_summary_table`.
- Column mapping:
  - Column 1: hardcoded labels.
  - Column 2:
    - Total population: sum of `number_of_males_including_children` + `number_of_females_including_children`.
    - Total households: `HouseholdSurvey` count.
    - Dominant house type: counts of `house_type` with percent.
    - Major landuse: max `public.lulc.Class_name` by area.
    - Dominant occupational category: mode of `livelihood_primary` with percent.
    - Sanitation facilities: `sanitation_facility` and `toilet_class` distribution.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
```
```python
livelihood_qs = (
    households.annotate(livelihood_n=Lower(Trim('livelihood_primary')))
    .exclude(livelihood_n__isnull=True)
    .exclude(livelihood_n='')
    .values('livelihood_n')
    .annotate(count=Count('livelihood_n'))
    .order_by('-count')
)
```
```sql
SELECT "Class_name", SUM("Area_SqM") AS total_area
FROM public.lulc
WHERE "Vill_ID" = %s
GROUP BY "Class_name"
ORDER BY total_area DESC
LIMIT 1;
```

### Hazard Assessment
- Data source: `PRA_main`.
- Database tables used: `PRA_main`.
- Query/logic: read hazard frequency and severity fields.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getHazardAssessment`.
- Column mapping:
  - Hazard: fixed labels.
  - Frequency/Severity: PRA fields `flood_frequency`, `flood_severity`, `erosion_hazard_frequency`, `erosion_hazard_severity`, `strong_wind_hazard_frequency`, `strong_wind_hazard_severity`, `earthquake_hazard_frequency`, `earthquake_hazard_severity`.
- ORM/SQL snippet:
```python
pra_data = PRA_main.objects.filter(village_id=village_id).first()
```

### Vulnerability Assessment
- Data source: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `Critical_Facility`, `ExposureRiver`.
- Database tables used: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `Critical_Facility`, `shapefiles_exposureriver`.
- Query/logic: compute economic status, vulnerable population, vulnerable houses/roads, schools under risk; LVI score from hazard module.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getVulnerabilityAssessment`.
- Column mapping:
  - Economic status: counts from `HouseholdSurvey.economic_status`.
  - Vulnerable population: sums of `children_below_6_years`, `senior_citizens`, `pregnant_women`, `lactating_women`, `persons_with_disability_or_chronic_disease`.
  - Flood vulnerable houses: `HouseholdSurvey.flood_depth_m >= 0.5`.
  - Erosion vulnerable houses: `HouseholdSurvey.house_vulnerable_to_erosion = 'yes'`.
  - Flood vulnerable road: sum of `VillageRoadInfo.road_length_m` where `flood_depth_m > 0.5`.
  - Erosion vulnerable road: sum of `VillageRoadInfoErosion.road_length_m` where `erosion_class in ('High','Severe')`.
  - School: counts of `Critical_Facility` school types, plus flood depth filter.
  - Livelihood vulnerability index: `get_lvi_score` from hazard module.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
```
```python
flood_road_length_m = VillageRoadInfo.objects.filter(
    village_id=village_id,
    flood_depth_m__gt=0.5
).aggregate(total=Sum('road_length_m'))['total'] or 0
```
```python
erosion_road_length_m = VillageRoadInfoErosion.objects.filter(
    village_id=village_id
).filter(
    Q(erosion_class__iexact='Severe') |
    Q(erosion_class__iexact='High')
).aggregate(total=Sum('road_length_m'))['total'] or 0
```

### Risk Assessment (excluding content loss in INR Crore)
- Data source: `Risk_Assessment_Result` plus road/agriculture loss tables.
- Database tables used: `Risk_Assessment_Result`, `VillageRoadInfo`, `VillageRoadInfoEQ`, `VillageRoadInfoWind`, `villageAgricultureLandFloodInfo`, `villageAgricultureLandEQInfo`, `villageAgricultureLandWindInfo`, `HouseholdSurvey`.
- Query/logic: sum loss columns by asset type; convert to INR crores; dominant flood year from survey.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getRiskAssessment`.
- Column mapping:
  - Sector: fixed labels.
  - Flood/Earthquake/Strong wind: sums of loss fields by `asset_type` or road/agri loss tables.
- ORM/SQL snippet:
```python
risk_data = Risk_Assessment_Result.objects.filter(village_id=village_id)
```
```python
household_flood = (
    risk_data.filter(asset_type='household')
    .aggregate(Sum('flood_loss'))['flood_loss__sum'] or 0
) / 10000000
```

### Mitigation Intervention
- Data source: static placeholder rows.
- Database tables used: none.
- Query/logic: fixed rows with '-' values.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/dummy_data.py` -> `getMitigationIntervention`.
- Column mapping: all columns hardcoded.
- ORM/SQL snippet: none (static table).

### Village Contacts (Important contact details)
- Data source: `LineDepartment`.
- Database tables used: `LineDepartment`.
- Query/logic: filter by `official_number='yes'`.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getDistrictLevelOfficialsData`.
- Column mapping:
  - Name/designation: `LineDepartment.contact_name`.
  - Phone Number: `LineDepartment.phone_number`.
  - Position/Responsibility: `LineDepartment.section_master.section`.
- ORM/SQL snippet:
```python
officials = LineDepartment.objects.filter(
    village_id=village_id,
    official_number__iexact='yes'
).select_related('section_master')
```

### Emergency Toll Free Contact
- Data source: `LineDepartment` (fallback to static rows on error).
- Database tables used: `LineDepartment`.
- Query/logic: filter by `official_number='no'`.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_summary.py` -> `getEmergencyTollFreeContactData`.
- Column mapping:
  - Important Contact: `LineDepartment.section_master.section`.
  - Contact Number: `LineDepartment.phone_number`.
- ORM/SQL snippet:
```python
officials = LineDepartment.objects.filter(
    village_id=village_id,
    official_number__iexact='no'
).select_related('section_master')
```

---

## Chapter 3 - Village Profile

### Location Details
- Data source: `tblVillage`, `PRA_main`, and PostGIS `public.lulc`.
- Database tables used: `tblVillage`, `PRA_main`, `public.lulc`.
- Query/logic: fetch village with block/circle/district names; compute area from lulc table; fallback to PRA fields for elevation and distance to district HQ.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getVillageLocationDetails`.
- Column mapping:
  - Revenue Village: `tblVillage.name`.
  - Block: `tblVillage.gram_panchayat.name`.
  - Revenue Circle: `tblVillage.gram_panchayat.circle.name`.
  - District: `tblVillage.gram_panchayat.circle.district.name`.
  - Distance from district headquarter (km): `PRA_main.distance_from_district_headquarter_km`.
  - Total area (sq km): `public.lulc` sum of `ST_Area`.
  - Average elevation (above MSL): `PRA_main.average_elevation_msl`.
- ORM/SQL snippet:
```python
village = tblVillage.objects.select_related(
    'gram_panchayat__circle__district'
).get(id=village_id)
```
```sql
SELECT COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))) / 1000000, 0)
FROM public.lulc
WHERE "Vill_ID" = %s;
```

### Demographic Profile
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: aggregate male and female totals; compute total population, households, average family size, and females per 1000 males.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getVillageDemographic`.
- Column mapping:
  - No of Males: sum of `number_of_males_including_children`.
  - No of Females: sum of `number_of_females_including_children`.
  - Total Population: male + female.
  - Number of Households: count.
  - Average Family Size: total population / total households.
  - Number of females per 1,000 males: `(females/males)*1000`.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    total_males=Coalesce(
        Sum(Cast(Cast('number_of_males_including_children', FloatField()), IntegerField())),
        0
    ),
    total_females=Coalesce(
        Sum(Cast(Cast('number_of_females_including_children', FloatField()), IntegerField())),
        0
    ),
)
```

### Socio Economic Status
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: normalize `social_status`, map `economic_status` to AAY/APL/AY/BPL/PHH, and count cross-tab totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getSocialEconomicStatusData`.
- Column mapping:
  - Social/Economic Status Household: normalized `social_status`.
  - AAY/APL/AY/BPL/PHH: counts from mapped `economic_status`.
  - Total/%: row total and percent of total households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for hh in households:
    social_key = normalize_social_status(hh.social_status)
    economic_key = map_economic_status(hh.economic_status)
```

### Agriculture Land Holding
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `area_of_agriculture_land_owned_bigha` into size ranges; split by `own_agriculture_land` into leased/owned; compute counts and percentages; count no-land households.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getAgricultureLandHoldingData`.
- Column mapping: bucket counts and totals from `area_of_agriculture_land_owned_bigha` with `own_agriculture_land`.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# bucket area_of_agriculture_land_owned_bigha and own_agriculture_land
```

### Annual Household Income
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: clean `approximate_income_earned_every_year_inr`, cast to integer, bucket into income ranges; compute counts and percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getIncomeGroupData`.
- Column mapping: income bucket counts and percent of households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)

households = households.annotate(
    income_clean=Replace(
        Replace('approximate_income_earned_every_year_inr', Value(','), Value('')),
        Value(' '), Value('')
    )
).annotate(
    income_amt=Case(
        When(income_clean__regex=r'^\d+$', then=Cast('income_clean', IntegerField())),
        default=None,
        output_field=IntegerField()
    )
)
```

### Average Expenditure Breakdown
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: sum numeric values from expenditure fields and compute percent share of total.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getAverageExpenditureBreakdownData`.
- Column mapping: percent share for each expense field.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
```
```python
agri_sum = sum(safe_decimal(h.amount_spent_for_agriculture_livestock) for h in households)
festival_sum = sum(safe_decimal(h.expense_on_festival_marriage_and_other_social_occassions) for h in households)
repair_sum = sum(safe_decimal(h.expense_on_house_repair) for h in households)
tobacco_sum = sum(safe_decimal(h.expense_on_tobacco_liquor) for h in households)
education_sum = sum(safe_decimal(h.expense_on_education) for h in households)
health_sum = sum(safe_decimal(h.expense_on_health) for h in households)
food_sum = sum(safe_decimal(h.expense_on_food) for h in households)
```

### Household Debt Liability
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: classify `loan_amount` into ranges; compute counts and percentages of households.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getHouseholdDebtLiabilityData`.
- Column mapping: bucket counts and percent of households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
# bucket loan_amount values
```

### Primary Livelihood Distribution (primary economic activity)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: normalize `livelihood_primary`, count per category, compute percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPrimaryLivelihoodDistributionData`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .exclude(livelihood_primary__isnull=True)
    .values('livelihood_primary')
    .annotate(count=Count('livelihood_primary'))
    .order_by('-count')
```

### Secondary Livelihood Distribution (secondary economic activity)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: normalize `livelihood_secondary`, count per category, compute percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPrimaryLivelihoodDistributionData` (type `secondary`).
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .exclude(livelihood_secondary__isnull=True)
    .values('livelihood_secondary')
    .annotate(count=Count('livelihood_secondary'))
    .order_by('-count')
```

### Crop Cultivation
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts households by `number_of_crops_normally_raised_every_year` and computes percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getCropCultivationData`.
- Column mapping: crop count category, household count, percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('number_of_crops_normally_raised_every_year')
    .annotate(count=Count('id'))
```

### Livestock Ownership
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `big_cattle` and `small_cattle` categorical values; computes percent of households per category.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getLivestockOwnershipData`.
- Column mapping: category counts from `big_cattle` and `small_cattle` and percent of households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
big_0 = households.filter(big_cattle='No Big Cattle').count()
small_0 = households.filter(small_cattle='No Small Cattle').count()
```

### Housing Typology
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `house_type` by Kachcha/Semi Pucca/Pucca; compute percent and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getHousingTypologyData`.
- Column mapping: counts of `house_type` categories and percent of total.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id).aggregate(
    kachcha=Count('id', filter=Q(house_type__iexact='Kachcha')),
    semi_pucca=Count('id', filter=Q(house_type__iexact='Semi pucca')),
    pucca=Count('id', filter=Q(house_type__iexact='Pucca'))
)
```

### Digital Access (Digital media owned)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `digital_media_owned` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getDigitalAccessData`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('digital_media_owned')
    .annotate(count=Count('id'))
```

### Digital Access (Drinking water source)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `drinking_water_source` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getDrinkingWaterSourceData`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('drinking_water_source')
    .annotate(count=Count('id'))
```

### Digital Access (Adequacy of drinking water)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `adequate_water_supply` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getAdequacyOfDrinkingWaterData`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('adequate_water_supply')
    .annotate(count=Count('id'))
```

### Digital Access (JJM or other tap water connection)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `JJM_or_other_taped_water_connection` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getJJMHouseConnect`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('JJM_or_other_taped_water_connection')
    .annotate(count=Count('id'))
```

### Digital Access (Sanitation facilities)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `sanitation_facility` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getSanitationFacilities`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('sanitation_facility')
    .annotate(count=Count('id'))
```

### Digital Access (Household toilets type)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `type_of_toilet` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getHouseholdToiletsType`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('type_of_toilet')
    .annotate(count=Count('id'))
```

### Digital Access (De-sludge material)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `sludge_be_disposed_type` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getDe_sludgeMaterial`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('sludge_be_disposed_type')
    .annotate(count=Count('id'))
```

### Digital Access (Electricity connection)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `house_has_electric_connection` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getElectricityconnection`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('house_has_electric_connection')
    .annotate(count=Count('id'))
```

### Digital Access (Electricity source)
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `source_of_electricity` values and computes percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getElectricitySource`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
    .values('source_of_electricity')
    .annotate(count=Count('id'))
```

### Public Assets
- Data source: `Commercial`.
- Database tables used: `Commercial`.
- Query/logic: counts facilities by `type_of_occupancy` and counts presence of electricity, water, sanitation, road access, and building quality.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPublicAssetsData`.
- Column mapping: per facility type counts and counts of attribute presence.
- ORM/SQL snippet:
```python
facilities = Commercial.objects.filter(village=village_id)
```

### Road Length by Typology
- Data source: PostGIS `public.road_network` (GeoServer WFS fallback exists).
- Database tables used: `public.road_network`.
- Query/logic: group by road surface type and sum length; convert meters to km; compute percent of total length.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getRoadLengthByTypologyData`.
- Column mapping: surface type, length in km, percent of total.
- ORM/SQL snippet:
```sql
SELECT "RSur_Type", SUM("Length") AS total_length
FROM public.road_network
WHERE "Vill_ID" = %s
GROUP BY "RSur_Type"
ORDER BY total_length DESC;
```

### Power Infrastructure
- Data source: `ElectricPole` and `Transformer`.
- Database tables used: `ElectricPole`, `Transformer`.
- Query/logic: count poles and transformers by village.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getPowerInfrastructureData_Total`.
- Column mapping: counts for poles and transformers.
- ORM/SQL snippet:
```python
ElectricPole.objects.filter(village_id=village_id).count()
Transformer.objects.filter(village_id=village_id).count()
```

### Facility Access
- Data source: `PRA_main`.
- Database tables used: `PRA_main`.
- Query/logic: read nearest facility distance fields and format in km.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getFacilityAccessData`.
- Column mapping: PRA fields such as `nearest_higher_secondary_km`, `nearest_college_km`, `nearest_post_office_km`, `nearest_police_station_km`, `nearest_bank_atm_km`, `nearest_phc_km`, `nearest_chc_km`, `nearest_hospital_km`, `nearest_ambulance_km`.
- ORM/SQL snippet:
```python
pra_data = PRA_main.objects.filter(village_id=village_id).first()
```

### Land Use Classification
- Data source: PostGIS `public.lulc` (GeoServer WFS fallback exists).
- Database tables used: `public.lulc`.
- Query/logic: sum LULC class areas; normalize class names; compute percent share of total area.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/village_profile.py` -> `getLULCData`.
- Column mapping: class name, area, percent of total.
- ORM/SQL snippet:
```sql
SELECT "Class_name", SUM("Area_SqM") as total_area
FROM public.lulc
WHERE "Vill_ID" = %s
GROUP BY "Class_name";
```

---

## Chapter 4 - Hazard, Vulnerability and Risk Assessment

### Hazard Presence
- Data source: `PRA_main`.
- Database tables used: `PRA_main`.
- Query/logic: read hazard frequency/severity fields for flood, erosion, strong wind, earthquake.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHazardPresenceData`.
- Column mapping: frequency and severity from PRA fields; hazard labels are fixed.
- ORM/SQL snippet:
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```

### Earthquake MMI
- Data source: static table.
- Database tables used: none.
- Query/logic: hardcoded MMI row.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEarthquakeMMITableData`.
- Column mapping: all columns hardcoded.
- ORM/SQL snippet: none (static table).

### Flood Hazard Characteristics
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: compute max flood depth, mode values of flood-related fields, and dominant year from survey fields.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHazardCharacteristics`.
- Column mapping: details pulled from `maximum_flood_height_in_house_ft`, `maximum_flood_height_experience_in_your_agriculture_ft`, `duration_of_flood_stay_in_your_agriculture_field`, `your_agriculture_affected_by_flood`, `year_in_which_maximum_flood_experience_in_your_house`.
- ORM/SQL snippet:
```python
qs = HouseholdSurvey.objects.filter(village_id=village_id)
```

### Flood Frequency at House
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: count households by keyword match in `house_affected_by_flood` using predefined categories.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodFrequencyAtHouseData`.
- Column mapping: category labels, count, percent of total households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for label, keywords in FLOOD_FREQUENCY_CATEGORIES:
    q = Q()
    for k in keywords:
        q |= Q(house_affected_by_flood__icontains=k)
    count = households.filter(q).count()
```

### Flood Frequency in Agriculture Field
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: count households by keyword match in `your_agriculture_affected_by_flood` using predefined categories.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodFrequencyInAgricultureFieldData`.
- Column mapping: category labels, count, percent of total households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for label, keywords in FLOOD_FREQUENCY_CATEGORIES:
    q = Q()
    for k in keywords:
        q |= Q(your_agriculture_affected_by_flood__icontains=k)
    count = households.filter(q).count()
```

### Flood Duration in Agriculture Field
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: count households by keyword match in `duration_of_flood_stay_in_your_agriculture_field` using predefined categories.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getFloodDurationInAgricultureFieldData`.
- Column mapping: category labels, count, percent of total households.
- ORM/SQL snippet:
```python
households = HouseholdSurvey.objects.filter(village_id=village_id)
for label, keywords in FLOOD_DURATION_CATEGORIES:
    q = Q()
    for k in keywords:
        q |= Q(duration_of_flood_stay_in_your_agriculture_field__icontains=k)
    count = households.filter(q).count()
```

### Hazard Calendar
- Data source: `VdmDistrictMapData.hazard_calendar` image if present, otherwise static table.
- Database tables used: `VdmDistrictMapData`.
- Query/logic: render hazard calendar image if exists; else use hardcoded table.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `draw_hazard_Vulnerability_risk` and `getHazardCalender`.
- Column mapping: static month labels and hazard rows (fallback table).
- ORM/SQL snippet:
```python
img_field = VdmDistrictMapData.objects.filter(district_id=district_id).values('hazard_calendar').first()
```

### Erosion Characteristics
- Data source: PostGIS `public.erosion_accretion`.
- Database tables used: `public.erosion_accretion`.
- Query/logic: sum erosion/accretion area and boundary length by class for village.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getErosionCharacteristics`.
- Column mapping: class, area in sq m, vulnerable stretch in km.
- ORM/SQL snippet:
```sql
SELECT "Class",
       COALESCE(SUM(ST_Area(ST_Transform(geom, 32646))), 0) AS area_sqm,
       COALESCE(SUM(ST_Length(ST_Transform(ST_Boundary(geom), 32646))) / 1000, 0) AS length_km
FROM public.erosion_accretion
WHERE "Vill_ID" = %s
GROUP BY "Class";
```

### Vulnerable Population
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: sum vulnerable categories and total population; compute percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getVulnerablePopulationTableData`.
- Column mapping: category counts from survey fields.
- ORM/SQL snippet:
```python
qs = HouseholdSurvey.objects.filter(village=village_id)
qs.aggregate(
    children=Sum(Cast('children_below_6_years', FloatField())),
    seniors=Sum(Cast('senior_citizens', FloatField())),
    pregnant=Sum(Cast('pregnant_women', FloatField())),
    lactating=Sum(Cast('lactating_women', FloatField())),
    disabled=Sum(Cast('persons_with_disability_or_chronic_disease', FloatField())),
    males=Sum(Cast('number_of_males_including_children', FloatField())),
    females=Sum(Cast('number_of_females_including_children', FloatField())),
)
```

### Housing Flood Vulnerability
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result`.
- Query/logic: group by `house_type_name`; classify `flood_hazard` depth into severity buckets.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHousingFloodVulnerabilityData`.
- Column mapping: house type counts and flood depth buckets.
- ORM/SQL snippet:
```python
Risk_Assessment_Result.objects.filter(village=village_id, asset_type='household')
```

### Housing Erosion Vulnerability
- Data source: `Risk_Assessment_Result`.
- Database tables used: `Risk_Assessment_Result`.
- Query/logic: group by `house_type_name`; count erosion classes.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHousingErosionVulnerabilityData`.
- Column mapping: house type counts and erosion class buckets.
- ORM/SQL snippet:
```python
Risk_Assessment_Result.objects.filter(village=village_id, asset_type='household')
```

### House Typology
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `house_type` by Kachcha/Semi Pucca/Pucca; compute percent and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHouseTypeData`.
- Column mapping: counts of `house_type` categories and percent of total.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village=village_id).aggregate(
    kachcha=Count('id', filter=Q(house_type__iexact='Kachcha')),
    semi_pucca=Count('id', filter=Q(house_type__iexact='Semi pucca')),
    pucca=Count('id', filter=Q(house_type__iexact='Pucca')),
)
```

### Building Quality
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `building_quality` values into Good/Bad/Moderate categories; compute percentages.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getBuildingQualityData`.
- Column mapping: category counts and percent of households.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village=village_id).values_list('building_quality', flat=True)
```

### Plinth Height
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `plinth_or_stilt_height_ft` values into ranges and compute percentage.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getPlinthHeightData`.
- Column mapping: height buckets, counts, percent.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village=village_id).values_list('plinth_or_stilt_height_ft', flat=True)
```

### Toilet Quality
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: counts `toilet_class` values (pucca/semi pucca/kachcha) and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getToiletStructuralQualityData`.
- Column mapping: toilet class counts and percent.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village=village_id).values('toilet_class').annotate(count=Count('id'))
```

### House Repair Expense
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `amount_towards_flood_recovery_expenditure` into ranges and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHouseRepairExpenseData`.
- Column mapping: expense ranges, counts, percent.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('amount_towards_flood_recovery_expenditure', flat=True)
```

### Household Flood Loss
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `economic_loss_to_your_house_due_to_flood` into ranges and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHouseholdFloodLossData`.
- Column mapping: loss ranges, counts, percent.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('economic_loss_to_your_house_due_to_flood', flat=True)
```

### Agriculture Flood Loss
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: bucket `loss_AgriLivli` values into ranges and percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getAgricultureFloodLossData`.
- Column mapping: loss ranges, counts, percent.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id).values_list('loss_AgriLivli', flat=True)
```

### Road Flood Vulnerability
- Data source: `VillageRoadInfo`.
- Database tables used: `VillageRoadInfo`.
- Query/logic: sum `road_length_m` by `flood_class` and compute percent.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getRoadFloodVulnerabilityData`.
- Column mapping: flood class, length in km, percent.
- ORM/SQL snippet:
```python
VillageRoadInfo.objects.filter(village_id=village_id).values('flood_class').annotate(total=Sum('road_length_m'))
```

### Road Erosion Vulnerability
- Data source: `VillageRoadInfoErosion` and `VillageRoadInfo`.
- Database tables used: `VillageRoadInfoErosion`, `VillageRoadInfo`.
- Query/logic: sum `road_length_m` by `erosion_class`; percent of total road length from `VillageRoadInfo`.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getRoadErosionVulnerabilityData`.
- Column mapping: erosion class, length in km, percent.
- ORM/SQL snippet:
```python
VillageRoadInfoErosion.objects.filter(village_id=village_id).values('erosion_class').annotate(total=Sum('road_length_m'))
```

### Educational Facilities
- Data source: `Critical_Facility`.
- Database tables used: `Critical_Facility`.
- Query/logic: filter by `occupancy_type` containing school; count by flood class and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEducationalFacilitiesData`.
- Column mapping: facility counts and flood class distribution.
- ORM/SQL snippet:
```python
Critical_Facility.objects.filter(village_id=village_id, occupancy_type__icontains='school')
```

### Health Facilities
- Data source: `Critical_Facility`.
- Database tables used: `Critical_Facility`.
- Query/logic: filter health facility types; count by flood class and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getHealthFacilitiesData`.
- Column mapping: facility counts and flood class distribution.
- ORM/SQL snippet:
```python
Critical_Facility.objects.filter(village_id=village_id, occupancy_type__icontains='hospital')
```

### Other Assets
- Data source: `Critical_Facility`, `ElectricPole`, `Transformer`.
- Database tables used: `Critical_Facility`, `ElectricPole`, `Transformer`.
- Query/logic: counts of non-education/non-health facilities plus power assets, split by flood class.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getOtherAssetsData`.
- Column mapping: asset counts and flood class distribution.
- ORM/SQL snippet:
```python
Critical_Facility.objects.filter(village_id=village_id).exclude(occupancy_type__icontains='school')
```

### Power Infrastructure
- Data source: `ElectricPole`, `Transformer`.
- Database tables used: `ElectricPole`, `Transformer`.
- Query/logic: count assets by flood class and totals.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getPowerInfrastructureData`.
- Column mapping: counts by flood class.
- ORM/SQL snippet:
```python
ElectricPole.objects.filter(village_id=village_id)
Transformer.objects.filter(village_id=village_id)
```

### Livelihood Exposure
- Data source: `HouseholdSurvey`.
- Database tables used: `HouseholdSurvey`.
- Query/logic: compute exposure indicators from survey fields; compute index score.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getLivelihoodExposureData`.
- Column mapping: indicator values and computed scores.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
```

### Livelihood Sensitivity
- Data source: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `PRA_main`.
- Database tables used: `HouseholdSurvey`, `VillageRoadInfo`, `VillageRoadInfoErosion`, `PRA_main`.
- Query/logic: combine agriculture, road, and PRA indicators to compute sensitivity score.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getLivelihoodSensitivityData`.
- Column mapping: indicator values and computed scores.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
```

### Livelihood Adaptive Capacity
- Data source: `HouseholdSurvey`, `PRA_main`.
- Database tables used: `HouseholdSurvey`, `PRA_main`.
- Query/logic: evaluate adaptive capacity indicators from survey and PRA fields.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getLivelihoodAdaptiveCapacityData`.
- Column mapping: indicator values and computed scores.
- ORM/SQL snippet:
```python
HouseholdSurvey.objects.filter(village_id=village_id)
```

### Environmental Characteristics
- Data source: `PRA_main` and erosion helper.
- Database tables used: `PRA_main`, `public.erosion_accretion`.
- Query/logic: uses PRA fields for siltation, water logging, encroachment, drains; erosion length from erosion table.
- Python file and function: `assam_crv/vdmp_dashboard/pdf/hazard_Vulnerability_risk.py` -> `getEnvironmentalCharacteristicsData`.
- Column mapping: PRA fields and erosion length.
- ORM/SQL snippet:
```python
pra = PRA_main.objects.filter(village_id=village_id).first()
```


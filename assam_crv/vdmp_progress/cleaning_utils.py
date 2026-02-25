import pandas as pd
import re
import logging
from sklearn.neighbors import NearestNeighbors
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from vdmp_dashboard.models import HouseholdSurvey
from layers.models import village_flood_raster_Files, district_wind_raster_file, district_eq_raster_file
from village_profile.models import tblVillage
import math
import psycopg2
from village_profile.models import tblVillage
from osgeo import gdal, ogr, osr
import tempfile
import os
import geopandas as gpd
from sqlalchemy import create_engine
from django.conf import settings
from urllib.parse import quote_plus

def extract_flood_depth_from_raster(df, village_id):
    """
    SAFE flood depth extraction from raster (EPSG:4326)
    - Uses inverse geotransform
    - Checks raster extent
    - Returns None for failed extractions
    """

    print("---- Extracting flood depth from raster ----")

    raster_file = village_flood_raster_Files.objects.filter(
        village_id=village_id
    ).first()

    if not raster_file or not raster_file.raster_file:
        print("⚠️ No raster file found for village")
        return df

    raster_path = os.path.join(settings.MEDIA_ROOT, raster_file.raster_file.name)
    ds = gdal.Open(raster_path)

    if not ds:
        print("⚠️ Failed to open raster file")
        return df

    band = ds.GetRasterBand(1)
    gt = ds.GetGeoTransform()
    nodata = band.GetNoDataValue()

    inv_gt = gdal.InvGeoTransform(gt)
    if inv_gt is None:
        print("⚠️ Invalid geotransform")
        return df

    # Raster extent (lon/lat)
    minx = gt[0]
    maxy = gt[3]
    maxx = minx + gt[1] * ds.RasterXSize
    miny = maxy + gt[5] * ds.RasterYSize

    flood_values = []
    skipped_count = 0

    for idx, row in df.iterrows():
        try:
            lat = safe_float(row["latitude"])
            lon = safe_float(row["longitude"])

            if lat is None or lon is None:
                flood_values.append(None)
                skipped_count += 1
                continue

            # EXTENT CHECK
            if not (minx <= lon <= maxx and miny <= lat <= maxy):
                flood_values.append(None)
                skipped_count += 1
                continue

            px, py = gdal.ApplyGeoTransform(inv_gt, lon, lat)
            px, py = int(px), int(py)

            if (
                px < 0 or py < 0 or
                px >= ds.RasterXSize or
                py >= ds.RasterYSize
            ):
                flood_values.append(None)
                skipped_count += 1
                continue

            val = band.ReadAsArray(px, py, 1, 1)[0, 0]

            if val is None or (isinstance(val, float) and math.isnan(val)):
                flood_values.append(None)
                skipped_count += 1
            elif nodata is not None and val == nodata:
                flood_values.append(None)
                skipped_count += 1
            else:
                flood_values.append(round(float(val), 3))

        except Exception:
            flood_values.append(None)
            skipped_count += 1

    df["flood_depth_m"] = flood_values
    
    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count}/{len(df)} records (missing/invalid coordinates or no raster value)")

    df["flood_class"] = df["flood_depth_m"].apply(_classify_flood)

    return df


def safe_float(x):
    try:
        if x is None:
            return None
        x = str(x).strip()
        if x == "" or x.lower() in {"na", "null", "none"}:
            return None
        return float(x)
    except Exception:
        return None


def extract_erosion_buffer_values(df):
    """
    Loop-based point-in-polygon check against river buffer GeoJSON.
    Silent fail if extents do not overlap.
    """

    import geopandas as gpd
    from shapely.geometry import Point
    import os

    geojson_path = os.path.join(
        settings.MEDIA_ROOT,
        "pipeline_data",
        "river_buff_shp_file",
        "new_river_buff.geojson"
    )

    if not os.path.exists(geojson_path):
        return df

    # --------------------------------------------------
    # 1. Sanitize coordinates
    # --------------------------------------------------
    df["latitude_f"] = df["latitude"].apply(safe_float)
    df["longitude_f"] = df["longitude"].apply(safe_float)
    df["erosion_buffer_m"] = None
    df["erosion_value"] = None

    valid_df = df[
        df["latitude_f"].notna() & df["longitude_f"].notna()
    ].copy()

    if valid_df.empty:
        return df

    # --------------------------------------------------
    # 2. Create points GeoDataFrame (EPSG:4326 → meters)
    # --------------------------------------------------
    points_4326 = gpd.GeoDataFrame(
        valid_df,
        geometry=gpd.points_from_xy(
            valid_df["longitude_f"],
            valid_df["latitude_f"]
        ),
        crs="EPSG:4326"
    )

    points_m = points_4326.to_crs("EPSG:32646")  # Assam UTM

    # --------------------------------------------------
    # 3. Load buffers and project to meters
    # --------------------------------------------------
    buff_4326 = gpd.read_file(geojson_path)
    buff_m = buff_4326.to_crs("EPSG:32646")

    # --------------------------------------------------
    # 4. EXTENT CHECK (silent skip if mismatch)
    # --------------------------------------------------
    p_minx, p_miny, p_maxx, p_maxy = points_4326.total_bounds
    b_minx, b_miny, b_maxx, b_maxy = buff_4326.total_bounds

    if (
        p_maxx < b_minx or p_minx > b_maxx or
        p_maxy < b_miny or p_miny > b_maxy
    ):
        return df  # 👈 silently skip

    # --------------------------------------------------
    # 5. Loop over points
    # --------------------------------------------------
    for idx, pt_row in points_m.iterrows():

        pt = pt_row.geometry
        matched_buffers = []

        for _, buff in buff_m.iterrows():
            if pt.intersects(buff.geometry):
                matched_buffers.append(buff["BUFF_DIST"])

        if matched_buffers:
            value = str(int(min(matched_buffers)))  # smallest buffer wins
            df.at[idx, "erosion_buffer_m"] = value
            df.at[idx, "erosion_value"] = value

    return df


def _get_db_config(db_name=None, db_user=None, db_password=None, db_host=None, db_port=None):
    db_settings = settings.DATABASES.get("default", {})
    return {
        "dbname": db_name or db_settings.get("NAME"),
        "user": db_user or db_settings.get("USER"),
        "password": db_password or db_settings.get("PASSWORD"),
        "host": db_host or db_settings.get("HOST"),
        "port": db_port or db_settings.get("PORT"),
    }


def extract_erosion_buffer_values_postgis(
    df,
    buffer_table="public.riverbuffer",
    db_name=None,
    db_user=None,
    db_password=None,
    db_host=None,
    db_port=None,
):
    """
    SAFE erosion extraction using PostGIS
    - Skips invalid coordinates
    - NEVER crashes on bad data
    """

    import psycopg2
    import math

    df["latitude_f"] = df["latitude"].apply(safe_float)
    df["longitude_f"] = df["longitude"].apply(safe_float)
    df["erosion_buffer_m"] = None
    df["erosion_value"] = None

    db_config = _get_db_config(
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        db_host=db_host,
        db_port=db_port,
    )
    conn = psycopg2.connect(**db_config)

    sql = f"""
        SELECT MIN("BUFF_DIST")
        FROM {buffer_table}
        WHERE ST_Intersects(
            ST_Transform(
                ST_SetSRID(
                    ST_MakePoint(%s, %s),
                    4326
                ),
                32646
            ),
            ST_Transform(
                ST_SetSRID(geom, 4326),
                32646
            )
        );
    """


    with conn.cursor() as cur:
        processed_count = 0
        skipped_count = 0
        
        for idx, row in df.iterrows():

            lat = row["latitude_f"]
            lon = row["longitude_f"]

            # 🔒 HARD SAFETY CHECK - Skip None, NaN, and out-of-range values
            if lat is None or lon is None:
                skipped_count += 1
                df.at[idx, "erosion_value"] = None
                continue
            
            # Check for NaN (NaN != NaN is True)
            if isinstance(lat, float) and math.isnan(lat):
                skipped_count += 1
                df.at[idx, "erosion_value"] = None
                continue
            if isinstance(lon, float) and math.isnan(lon):
                skipped_count += 1
                df.at[idx, "erosion_value"] = None
                continue
            
            # Check valid coordinate ranges
            if lat < -90 or lat > 90 or lon < -180 or lon > 180:
                skipped_count += 1
                df.at[idx, "erosion_value"] = None
                continue

            try:
                cur.execute(sql, (lon, lat))
                result = cur.fetchone()[0]
                
                if result is not None:
                    val = str(int(result))
                    df.at[idx, "erosion_buffer_m"] = val
                    df.at[idx, "erosion_value"] = val
                
                processed_count += 1
                    
            except Exception as e:
                # Rollback and continue - doesn't re-run previous queries
                conn.rollback()
                skipped_count += 1
                continue
        
        if skipped_count > 0:
            print(f"⚠️ Skipped {skipped_count}/{len(df)} records (invalid coordinates or no erosion buffer)")

    conn.close()
    return df


def process_road_data_pipeline(
    village_id,
    village_code,
    district_code,
    district_name,
    village_name,
    district_id,
    db_name=None,
    db_user=None,
    db_password=None,
    db_host=None,
    db_port=None,
):
   
  

    print(f"🛣️ Processing roads for village: {village_name}")

    village_obj = tblVillage.objects.get(id=village_id)

    db_config = _get_db_config(
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        db_host=db_host,
        db_port=db_port,
    )
    conn = psycopg2.connect(**db_config)

 

    # Flood / EQ / Wind (combined in one function)
    print("🌊 Processing flood, earthquake, and wind hazards...")
    _process_road_flood_data(
        conn,
        village_obj,
        village_code,
        district_code,
        district_name,
        village_name,
        district_id
    )

    # # ✅ Erosion (vector only)
    print("🌊 Processing erosion hazard...")
    _process_road_erosion_data(
        conn,
        village_obj,
        village_code,
        district_code,
        district_name,
        village_name,
    )

    conn.close()
    print("✅ Road processing completed")


# ------------------------------- agriculture ----------------

def load_village_agriculture_lulc(village_code):
    engine = get_sqlalchemy_engine()

    sql = """
    SELECT
        id,
        "Vill_ID",
        "Class_name",
        "Area_SqM",
        geom
    FROM public.lulc
    WHERE "Vill_ID" = %s
      AND "Class_name" IN ('Agriculture Land', 'Fallow Land')
      AND geom IS NOT NULL;
    """

    return gpd.read_postgis(
        sql=sql,
        con=engine,
        params=(village_code,),
        geom_col="geom",
        crs="EPSG:4326"
    )


import numpy as np
from osgeo import gdal, ogr, osr
import geopandas as gpd
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_zonal_stats_gdal(raster_path, polygon_geom):
    """
    Get zonal statistics (mean, max, min) for a polygon using GDAL
    Returns: dict with mean, max, min values and valid pixel count
    """
    src_ds = gdal.Open(raster_path)
    if not src_ds:
        return {'mean': 0.0, 'max': 0.0, 'min': 0.0, 'valid_pixels': 0}
    
    band = src_ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gt = src_ds.GetGeoTransform()
    
    # Get polygon bounds and convert to pixel coordinates
    minx, miny, maxx, maxy = polygon_geom.bounds
    px1 = max(0, int((minx - gt[0]) / gt[1]))
    py1 = max(0, int((maxy - gt[3]) / gt[5]))
    px2 = min(src_ds.RasterXSize, int((maxx - gt[0]) / gt[1]))
    py2 = min(src_ds.RasterYSize, int((miny - gt[3]) / gt[5]))
    
    # Read raster subset
    width = px2 - px1
    height = py2 - py1
    
    if width <= 0 or height <= 0:
        return {'mean': 0.0, 'max': 0.0, 'min': 0.0, 'valid_pixels': 0}
    
    data = band.ReadAsArray(px1, py1, width, height)
    
    # Create subset geotransform
    sub_gt = (
        gt[0] + px1 * gt[1],
        gt[1], gt[2],
        gt[3] + py1 * gt[5],
        gt[4], gt[5]
    )
    
    # Create memory mask raster
    mem_drv = gdal.GetDriverByName('MEM')
    mask_ds = mem_drv.Create('', width, height, 1, gdal.GDT_Byte)
    mask_ds.SetGeoTransform(sub_gt)
    mask_ds.SetProjection(src_ds.GetProjection())
    
    # Create memory vector layer
    mem_vector_drv = ogr.GetDriverByName('MEM')
    mem_vector_ds = mem_vector_drv.CreateDataSource('')
    srs = osr.SpatialReference()
    srs.ImportFromWkt(src_ds.GetProjection())
    mem_layer = mem_vector_ds.CreateLayer('polygon', srs, ogr.wkbPolygon)
    
    # Rasterize polygon
    feature_defn = mem_layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)
    feature.SetGeometry(ogr.CreateGeometryFromWkt(polygon_geom.wkt))
    mem_layer.CreateFeature(feature)
    
    gdal.RasterizeLayer(mask_ds, [1], mem_layer, burn_values=[1])
    mask = mask_ds.GetRasterBand(1).ReadAsArray()
    
    # Clean up
    feature = None
    mem_layer = None
    mem_vector_ds = None
    
    # Extract masked data
    masked_data = data[mask == 1]
    masked_data = masked_data[~np.isnan(masked_data)]
    
    if nodata is not None and not np.isnan(nodata):
        masked_data = masked_data[masked_data != nodata]
    
    if masked_data.size == 0:
        return {'mean': 0.0, 'max': 0.0, 'min': 0.0, 'valid_pixels': 0}
    
    return {
        'mean': round(float(np.mean(masked_data)), 4),
        'max': round(float(np.max(masked_data)), 4),
        'min': round(float(np.min(masked_data)), 4),
        'valid_pixels': int(masked_data.size)
    }


def get_raster_fallback_stats(raster_path, village_code, stat_type='max',eq=False):
    """
    Get fallback statistics from clipped raster when polygon-level data is insufficient
    Returns median or max value from the entire clipped raster
    """
    try:
        village_gdf = load_village_boundary(village_code)
        clipped_raster = clip_raster_to_village(raster_path, village_gdf)
        
        ds = None
        if eq:
            ds = gdal.Open(raster_path)
        else:
            ds = gdal.Open(clipped_raster)
        if not ds:
            return 0.0
            
        # Check geotransform validity
        gt = ds.GetGeoTransform()
        if gt is None or gt[1] == 0 or gt[5] == 0:
            print("⚠️ Invalid geotransform, using original raster")
            ds = gdal.Open(raster_path)
            if not ds:
                return 0.0
            
        band = ds.GetRasterBand(1)
        data = band.ReadAsArray()
        nodata = band.GetNoDataValue()
        
        # Remove nodata values
        valid_data = data[~np.isnan(data)]
        if nodata is not None:
            valid_data = valid_data[valid_data != nodata]
        
        if valid_data.size == 0:
            return 0.0
            
        if stat_type == 'median':
            return round(float(np.median(valid_data)), 4)
        elif stat_type == 'max':
            return round(float(np.max(valid_data)), 4)
        else:
            return round(float(np.mean(valid_data)), 4)
            
    except Exception as e:
        print(f"⚠️ Fallback stats failed: {e}")
        return 0.0


def get_agriculture_unit_cost(land_type="Agriculture Land"):
    """
    Get unit cost per sqm from AgricultureLandCostMaping model
    """
    from vdmp_dashboard.models import AgricultureLandCostMaping
    
    cost_mapping = AgricultureLandCostMaping.objects.filter(
        land_type__icontains=land_type
    ).first()

    # print(f"🔍 Fetching unit cost for {land_type}: {cost_mapping}")
    
    if cost_mapping:
        return float(cost_mapping.unit_cost_per_sqm)
    
    return 0.0


def get_agriculture_flood_mdr(flood_depth_m, crop_type):
    """
    Get MDR value for agriculture flood:
    - default crop_type
    - round depth
    - nearest lower match
    - cap at max MDR
    """
    from vdmp_dashboard.models import agricultureLandFloodMDRMapping

    # Default crop type
    crop_type = crop_type or "Agriculture Land"

    # No flood → no damage
    if flood_depth_m is None or flood_depth_m <= 0:
        return 0.0

    # Round flood depth
    flood_depth = round(float(flood_depth_m), 2)

    base_qs = agricultureLandFloodMDRMapping.objects.filter(
        crop_type=crop_type
    )

    if not base_qs.exists():
        return 0.0

    # Nearest LOWER depth
    record = (
        base_qs
        .filter(flood_depth_m__lte=flood_depth)
        .order_by("-flood_depth_m")
        .first()
    )

    # Cap at max MDR if depth exceeds table
    if not record:
        record = base_qs.order_by("-flood_depth_m").first()

    return float(record.mdr) if record else 0.0



def get_agriculture_wind_mdr(wind_hazard, crop_type):
    """
    Get MDR value for agriculture wind:
    - default crop_type
    - round hazard
    - nearest lower match
    - cap at max MDR
    """
    from vdmp_dashboard.models import agricultureLandWindMDRMapping

    # Default crop type
    crop_type = crop_type or "Agriculture Land"

    # No wind → no damage
    if wind_hazard is None or wind_hazard <= 0:
        return 0.0

    # Round wind hazard
    wind_hazard = round(float(wind_hazard), 2)

    base_qs = agricultureLandWindMDRMapping.objects.filter(
        crop_type=crop_type
    )

    if not base_qs.exists():
        return 0.0

    # Nearest LOWER hazard
    record = (
        base_qs
        .filter(wind_hazard__lte=wind_hazard)
        .order_by("-wind_hazard")
        .first()
    )

    # Cap at max MDR if hazard exceeds table
    if not record:
        record = base_qs.order_by("-wind_hazard").first()

    return float(record.mdr) if record else 0.0


def get_agriculture_eq_mdr(eq_hazard, crop_type):
    """
    Get MDR value for agriculture earthquake based on EQ hazard and crop type
    """
    from vdmp_dashboard.models import agricultureLandEQMDRMapping
    
    mdr_record = agricultureLandEQMDRMapping.objects.filter(
        eq_hazard__lte=eq_hazard,
        crop_type=crop_type
    ).order_by('-eq_hazard').first()
    
    return float(mdr_record.mdr) if mdr_record else 0.0



# ============================================================================
# WIND HAZARD PROCESSING
# ============================================================================

def sample_raster_at_point(ds, point_geom):
    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gt = ds.GetGeoTransform()

    inv_gt = gdal.InvGeoTransform(gt)
    if not inv_gt:
        return None

    px, py = gdal.ApplyGeoTransform(inv_gt, point_geom.x, point_geom.y)
    px, py = int(px), int(py)

    if (
        px < 0 or py < 0 or
        px >= ds.RasterXSize or py >= ds.RasterYSize
    ):
        return None

    val = band.ReadAsArray(px, py, 1, 1)[0, 0]

    if val is None or (nodata is not None and val == nodata):
        return None

    return round(float(val), 4)




def process_agriculture_wind_pipeline(
    village_obj,
    village_code,
    district_name,
    district_code,
    village_name,
):
    """
    Process wind hazard for agriculture land
    """
    print(f"💨 Processing Agriculture Wind Hazard for {village_name} ({village_code})")

    from vdmp_dashboard.models import villageAgricultureLandWindInfo
    from django.db import transaction

    vill_obj = tblVillage.objects.get(id=int(village_obj))
    
    # Delete old data first
    with transaction.atomic():
        deleted_count, _ = villageAgricultureLandWindInfo.objects.filter(village=vill_obj).delete()
        print(f"🧹 Deleted {deleted_count} old wind records for {village_name}")
    
    # Wind raster path
    raster_path = os.path.join(settings.MEDIA_ROOT, "pipeline_data", "wind_raster", "Wind.tif")
    ds = gdal.Open(raster_path)
    # Load agriculture polygons
    lulc_gdf = load_village_agriculture_lulc(village_code)
    if lulc_gdf.empty:
        print("⚠️ No agriculture polygons found")
        return

    print(f"📌 Processing {len(lulc_gdf)} agriculture polygons...")

    records = []
    stats_summary = {'with_hazard': 0, 'no_coverage': 0}
    fallback_value = None

    # Process each polygon
    for idx, row in lulc_gdf.iterrows():
        stats = get_zonal_stats_gdal(raster_path, row["geom"])
        
        wind_hazard = stats['mean']  # Use mean wind hazard
        area_sqm = float(row["Area_SqM"])
        
        # Track statistics
        if stats['valid_pixels'] > 0:
            wind_hazard = max(stats['mean'], stats['max'])
            stats_summary['with_hazard'] += 1

        else:
            # 🔑 CENTROID FALLBACK
            centroid = row["geom"].centroid
            # print(f"⚠️ No valid pixels for polygon {idx}, using centroid fallback at {centroid.y}, {centroid.x}")
            centroid_value = sample_raster_at_point(ds, centroid)
            # print(f"   Centroid value: {centroid_value}")

            if centroid_value is not None:
                wind_hazard = centroid_value
                stats_summary['with_hazard'] += 1
            else:
                wind_hazard = 0.0
                stats_summary['no_coverage'] += 1

       

        # Calculate costs and get MDR from database
        unit_cost = Decimal(str(get_agriculture_unit_cost("Agriculture Land")))
        replacement_cost = Decimal(str(area_sqm)) * unit_cost
        crop_type = row.get("Class_name", "Agriculture Land")
        mdr = Decimal(str(get_agriculture_wind_mdr(wind_hazard, crop_type)))
        loss = replacement_cost * mdr

        records.append(
            villageAgricultureLandWindInfo(
                village=vill_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_name,
                village_code=village_code,
                total_area_sqm=area_sqm,
                wind_hazard=Decimal(str(wind_hazard)),
                wind_hazard_mdr=mdr,
                unit_cost_per_sqm=unit_cost,
                total_replacement_cost_inr=replacement_cost,
                wind_loss=loss,
            )
        )

    # 🔥 FALLBACK: If no coverage, use clipped raster median
    if stats_summary['with_hazard'] == 0 and stats_summary['no_coverage'] > 0:
        print("🔄 No wind data coverage, applying fallback using clipped raster...")
        fallback_value = get_raster_fallback_stats(raster_path, village_code, 'max')
        
        if fallback_value > 0:
            # Update records with fallback value
            updated_records = []
            for i, record in enumerate(records):
                if record.wind_hazard == 0:
                    # Get crop_type from original lulc_gdf data
                    crop_type = lulc_gdf.iloc[i].get("Class_name", "Agriculture Land")
                    
                    record.wind_hazard = Decimal(str(fallback_value))
                    mdr = Decimal(str(get_agriculture_wind_mdr(fallback_value, crop_type)))
                    record.wind_hazard_mdr = mdr
                    record.wind_loss = record.total_replacement_cost_inr * mdr
                    
                    stats_summary['with_hazard'] += 1
                    stats_summary['no_coverage'] -= 1
                updated_records.append(record)
            records = updated_records
            print(f"✅ Applied fallback value {fallback_value} to {stats_summary['with_hazard']} polygons")

    # Save records
    if records:
        villageAgricultureLandWindInfo.objects.bulk_create(records, batch_size=500)
        
        print(f"\n📊 Wind Hazard Summary:")
        print(f"   ✅ Saved {len(records)} records")
        print(f"   💨 Polygons with wind data: {stats_summary['with_hazard']}")
        print(f"   ⚠️  No coverage: {stats_summary['no_coverage']}")
        if fallback_value:
            print(f"   🔄 Fallback value used: {fallback_value}")
    else:
        print("⚠️ No records to save")


# ============================================================================
# EARTHQUAKE HAZARD PROCESSING
# ============================================================================

def process_agriculture_earthquake_pipeline(
    village_obj,
    village_code,
    district_name,
    district_code,
    village_name,
):
    """
    Process earthquake hazard (PGA) for agriculture land
    """
    print(f"🌍 Processing Agriculture Earthquake Hazard for {village_name} ({village_code})")

    from vdmp_dashboard.models import villageAgricultureLandEQInfo

    vill_obj = tblVillage.objects.get(id=int(village_obj))
    
    # Earthquake raster path
    raster_path = "c:\\assamcrv\\assam_crv\\static\\risk_assessment_raster\\eq.tif"
    
    # Load agriculture polygons
    lulc_gdf = load_village_agriculture_lulc(village_code)
    if lulc_gdf.empty:
        print("⚠️ No agriculture polygons found")
        return

    print(f"📌 Processing {len(lulc_gdf)} agriculture polygons...")

    records = []
    stats_summary = {'with_hazard': 0, 'no_coverage': 0}
    fallback_value = None

    # Process each polygon
    for idx, row in lulc_gdf.iterrows():
        stats = get_zonal_stats_gdal(raster_path, row["geom"])
        
        eq_hazard = stats['mean']  # Use mean PGA value
        area_sqm = float(row["Area_SqM"])
        
        # Track statistics
        if stats['valid_pixels'] > 0:
            stats_summary['with_hazard'] += 1
        else:
            stats_summary['no_coverage'] += 1
            eq_hazard = 0.0

        # Calculate costs and get MDR from database
        unit_cost = Decimal(str(get_agriculture_unit_cost("Agriculture Land")))
        replacement_cost = Decimal(str(area_sqm)) * unit_cost
        crop_type = row.get("Class_name", "Agriculture Land")
        mdr = Decimal(str(get_agriculture_eq_mdr(eq_hazard, crop_type)))
        loss = replacement_cost * mdr

        records.append(
            villageAgricultureLandEQInfo(
                village=vill_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_name,
                village_code=village_code,
                total_area_sqm=area_sqm,
                eq_hazard=Decimal(str(eq_hazard)),
                eq_hazard_mdr=mdr,
                unit_cost_per_sqm=unit_cost,
                total_replacement_cost_inr=replacement_cost,
                eq_loss=loss,
            )
        )

    # 🔥 FALLBACK: If no coverage, use clipped raster max
    if stats_summary['with_hazard'] == 0 and stats_summary['no_coverage'] > 0:
        print("🔄 No earthquake data coverage, applying fallback using clipped raster...")
        fallback_value = get_raster_fallback_stats(raster_path, village_code, 'max', eq=True)
        
        if fallback_value > 0:
            # Update records with fallback value
            updated_records = []
            for i, record in enumerate(records):
                if record.eq_hazard == 0:
                    # Get crop_type from original lulc_gdf data
                    crop_type = lulc_gdf.iloc[i].get("Class_name", "Agriculture Land")
                    
                    record.eq_hazard = Decimal(str(fallback_value))
                    mdr = Decimal(str(get_agriculture_eq_mdr(fallback_value, crop_type)))
                    record.eq_hazard_mdr = mdr
                    record.eq_loss = record.total_replacement_cost_inr * mdr
                    
                    stats_summary['with_hazard'] += 1
                    stats_summary['no_coverage'] -= 1
                updated_records.append(record)
            records = updated_records
            print(f"✅ Applied fallback value {fallback_value} to {stats_summary['with_hazard']} polygons")

    # Save records
    if records:
        villageAgricultureLandEQInfo.objects.bulk_create(records, batch_size=500)
        
        print(f"\n📊 Earthquake Hazard Summary:")
        print(f"   ✅ Saved {len(records)} records")
        print(f"   🌍 Polygons with EQ data: {stats_summary['with_hazard']}")
        print(f"   ⚠️  No coverage: {stats_summary['no_coverage']}")
        if fallback_value:
            print(f"   🔄 Fallback value used: {fallback_value}")
    else:
        print("⚠️ No records to save")


import os
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone

def process_arrgicultural_data_pipeline(
    village_obj,
    village_code,
    district_name,
    district_code,
    village_name,
):
    """
    Agriculture Flood Hazard Pipeline

    Steps:
    1. Delete old records
    2. Load flood raster
    3. Load agriculture polygons
    4. Perform zonal statistics
    5. Calculate replacement cost & loss
    6. Apply fallback if needed
    7. Bulk insert fresh records
    """

    print(f"\n🌾 Processing Agriculture Flood Data for {village_name} ({village_code})")

    from layers.models import village_flood_raster_Files
    from vdmp_dashboard.models import villageAgricultureLandFloodInfo
    from administrator.models import tblVillage

    vill_obj = tblVillage.objects.get(id=int(village_obj))

    with transaction.atomic():

        # --------------------------------------------------
        # STEP 1: DELETE OLD DATA (ENSURE FRESH CALCULATION)
        # --------------------------------------------------
        deleted_count, _ = villageAgricultureLandFloodInfo.objects.filter(
            village=vill_obj
        ).delete()

        print(f"🧹 Deleted {deleted_count} old agriculture flood records")

        # --------------------------------------------------
        # STEP 2: LOAD FLOOD RASTER
        # --------------------------------------------------
        flood_raster = village_flood_raster_Files.objects.filter(
            village_id=vill_obj
        ).first()

        if not flood_raster:
            print("❌ Flood raster not found")
            return

        raster_path = os.path.join(
            settings.MEDIA_ROOT,
            flood_raster.raster_file.name
        )

        # --------------------------------------------------
        # STEP 3: LOAD AGRICULTURE POLYGONS
        # --------------------------------------------------
        lulc_gdf = load_village_agriculture_lulc(village_code)

        if lulc_gdf.empty:
            print("⚠️ No agriculture polygons found")
            return

        print(f"📌 Processing {len(lulc_gdf)} polygons...")

        records = []
        stats_summary = {'flooded': 0, 'no_flood': 0, 'no_coverage': 0}
        fallback_value = None

        # --------------------------------------------------
        # STEP 4: PROCESS EACH POLYGON
        # --------------------------------------------------
        for idx, row in lulc_gdf.iterrows():

            stats = get_zonal_stats_gdal(raster_path, row["geom"])

            flood_depth = float(stats.get("max", 0) or 0)
            valid_pixels = stats.get("valid_pixels", 0)

            flood_class = _classify_flood(flood_depth)

            # Convert sq meters → sq km (IMPORTANT)
            area_sqm = float(row["Area_SqM"])
            # area_sqkm = area_sqm / 1_000_000

            if valid_pixels == 0:
                stats_summary['no_coverage'] += 1
            elif flood_depth > 0:
                stats_summary['flooded'] += 1
            else:
                stats_summary['no_flood'] += 1

            unit_cost = Decimal(str(get_agriculture_unit_cost("Agriculture Land")))
            replacement_cost = Decimal(str(area_sqm)) * unit_cost

            crop_type = row.get("Class_name") or "Agriculture Land"

            mdr = Decimal(str(get_agriculture_flood_mdr(flood_depth, crop_type)))
            loss = replacement_cost * mdr

            records.append(
                villageAgricultureLandFloodInfo(
                    village=vill_obj,
                    district_name=district_name,
                    district_code=district_code,
                    village_name=village_name,
                    village_code=village_code,
                    total_area_sqm=area_sqm,
                    flood_depth_m=flood_depth,
                    flood_class=flood_class,
                    unit_cost_per_sqm=unit_cost,
                    total_replacement_cost_inr=replacement_cost,
                    flood_hazard_mdr=mdr,
                    flood_loss=loss,
                    
                )
            )

        # --------------------------------------------------
        # STEP 5: FALLBACK LOGIC
        # --------------------------------------------------
        """
        If:
            - No flooded polygons detected
            - Some polygons had no raster coverage
        Then:
            Use village-level raster median depth
            to avoid under-estimating risk.
        """

        if stats_summary['flooded'] == 0 and stats_summary['no_coverage'] > 0:

            print("🔄 Applying fallback using raster median...")

            fallback_value = get_raster_fallback_stats(
                raster_path,
                village_code,
                'median'
            )

            if fallback_value and fallback_value > 0:

                for i, record in enumerate(records):

                    if record.flood_depth_m == 0.0:

                        crop_type = (
                            lulc_gdf.iloc[i].get("Class_name")
                            or "Agriculture Land"
                        )

                        record.flood_depth_m = fallback_value
                        record.flood_class = _classify_flood(fallback_value)

                        mdr = Decimal(
                            str(get_agriculture_flood_mdr(fallback_value, crop_type))
                        )

                        record.flood_hazard_mdr = mdr
                        record.flood_loss = (
                            record.total_replacement_cost_inr * mdr
                        )

                        stats_summary['flooded'] += 1
                        stats_summary['no_coverage'] -= 1

                print(f"✅ Fallback applied ({fallback_value}m)")

        # --------------------------------------------------
        # STEP 6: BULK INSERT NEW RECORDS
        # --------------------------------------------------
        if records:
            villageAgricultureLandFloodInfo.objects.bulk_create(
                records,
                batch_size=500
            )

            print("\n📊 Flood Summary:")
            print(f"   Total records: {len(records)}")
            print(f"   Flooded: {stats_summary['flooded']}")
            print(f"   Safe: {stats_summary['no_flood']}")
            print(f"   No coverage: {stats_summary['no_coverage']}")
        else:
            print("⚠️ No records generated")

# ============================================================================
# EROSION PROCESSING
# ============================================================================

def get_erosion_buffer_for_polygon(polygon_wkt, 
                                   buffer_table="public.riverbuffer",
                                   db_config=None):
    """
    Get minimum erosion buffer distance for a polygon using PostGIS intersection
    Returns: buffer distance (50, 100, 150) or None
    """
    if db_config is None:
        db_config = _get_db_config()
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # PostGIS query to find intersecting buffers
        sql = f"""
            SELECT MIN("BUFF_DIST") AS min_buffer
            FROM {buffer_table}
            WHERE ST_Intersects(
                ST_Transform(
                    ST_SetSRID(ST_GeomFromText(%s), 4326),
                    32646
                ),
                ST_Transform(
                    ST_SetSRID(geom, 4326),
                    32646
                )
            );
        """

        
        cur.execute(sql, (polygon_wkt,))
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if result and result[0] is not None:
            return int(result[0])
        return None
        
    except Exception as e:
        print(f"⚠️ Erosion buffer query failed: {e}")
        return None


def process_agriculture_erosion_pipeline(
    village_obj,
    village_code,
    district_name,
    district_code,
    village_name,
    db_config=None
):
    """
    Process erosion risk for agriculture land using river buffer intersection
    """
    print(f"🌊 Processing Agriculture Erosion Risk for {village_name} ({village_code})")

    from vdmp_dashboard.models import villageAgricultureLandErosionInfo
    from django.db import transaction

    vill_obj = tblVillage.objects.get(id=int(village_obj))
    
    # Delete old data first
    with transaction.atomic():
        deleted_count, _ = villageAgricultureLandErosionInfo.objects.filter(village=vill_obj).delete()
        print(f"🧹 Deleted {deleted_count} old erosion records for {village_name}")
    
    # Load agriculture polygons
    lulc_gdf = load_village_agriculture_lulc(village_code)
    if lulc_gdf.empty:
        print("⚠️ No agriculture polygons found")
        return

    print(f"📌 Processing {len(lulc_gdf)} agriculture polygons...")

    records = []
    stats_summary = {
        'high_risk': 0,
        'medium_risk': 0,
        'low_risk': 0,
        'no_risk': 0
    }

    # Process each polygon
    for idx, row in lulc_gdf.iterrows():
        area_sqm = float(row["Area_SqM"])
        polygon_wkt = row["geom"].wkt
        
        # Get erosion buffer distance
        buffer_distance = get_erosion_buffer_for_polygon(
            polygon_wkt, 
            buffer_table="public.riverbuffer",
            db_config=db_config
        )
        
        # Classify erosion risk
        erosion_class = _classify_erosion_buffer(buffer_distance)
        
        # Track statistics
        if buffer_distance is None:
            stats_summary['no_risk'] += 1
        elif buffer_distance <= 50:
            stats_summary['high_risk'] += 1
        elif buffer_distance <= 100:
            stats_summary['medium_risk'] += 1
        elif buffer_distance <= 150:
            stats_summary['low_risk'] += 1

        records.append(
            villageAgricultureLandErosionInfo(
                village=vill_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_name,
                village_code=village_code,
                total_area_sqm=area_sqm,
                erosion_class=erosion_class,
                unit_cost_per_sqm=Decimal(0.0),
                total_replacement_cost_inr=Decimal(0.0),
                # unit_cost_per_sqm=Decimal(str(get_agriculture_unit_cost("Agriculture Land"))),
                # total_replacement_cost_inr=Decimal(str(area_sqm)) * Decimal(str(get_agriculture_unit_cost("Agriculture Land"))),
            )
        )

    # Save records
    if records:
        villageAgricultureLandErosionInfo.objects.bulk_create(records, batch_size=500)
        
        print(f"\n📊 Erosion Risk Summary:")
        print(f"   ✅ Saved {len(records)} records")
        print(f"   🔴 High risk (0-50m): {stats_summary['high_risk']}")
        print(f"   🟡 Medium risk (50-100m): {stats_summary['medium_risk']}")
        print(f"   🟢 Low risk (100-150m): {stats_summary['low_risk']}")
        print(f"   ✅ No risk: {stats_summary['no_risk']}")
    else:
        print("⚠️ No records to save")


# ============================================================================
# MASTER FUNCTION TO RUN ALL HAZARDS
# ============================================================================

def process_all_agriculture_hazards(
    village_obj,
    village_code,
    district_name,
    district_code,
    village_name,
    db_config=None
):
    """
    Master Agriculture Hazard Assessment

    Each pipeline:
        - Deletes old data
        - Recalculates fresh values
        - Stores new values in DB
    """

    print(f"\n{'='*60}")
    print("🌾 AGRICULTURE HAZARD ASSESSMENT")
    print(f"Village: {village_name} ({village_code})")
    print(f"{'='*60}\n")

    # --------------------------------------------------
    # 1️⃣ FLOOD
    # --------------------------------------------------
    print("1️⃣ FLOOD HAZARD")
    process_arrgicultural_data_pipeline(
        village_obj,
        village_code,
        district_name,
        district_code,
        village_name
    )

    # --------------------------------------------------
    # 2️⃣ WIND
    # --------------------------------------------------
    print("\n2️⃣ WIND HAZARD")
    process_agriculture_wind_pipeline(
        village_obj,
        village_code,
        district_name,
        district_code,
        village_name
    )

    # --------------------------------------------------
    # 3️⃣ EROSION
    # --------------------------------------------------
    print("\n3️⃣ EROSION RISK")
    process_agriculture_erosion_pipeline(
        village_obj,
        village_code,
        district_name,
        district_code,
        village_name,
        db_config
    )

    print(f"\n{'='*60}")
    print("✅ ALL AGRICULTURE HAZARD ASSESSMENTS COMPLETED!")
    print(f"{'='*60}\n")

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

# Run for a single village
# process_all_agriculture_hazards(
#     village_obj=550,
#     village_code="280_6",
#     district_name="Bongaigaon",
#     district_code="280",
#     village_name="Ag Mandia"
# )

# Or run individually
# process_agriculture_wind_pipeline(550, "280_6", "Bongaigaon", "280", "Ag Mandia")
# process_agriculture_earthquake_pipeline(550, "280_6", "Bongaigaon", "280", "Ag Mandia")
# process_agriculture_erosion_pipeline(550, "280_6", "Bongaigaon", "280", "Ag Mandia")


def get_mdr_value(hazard_value, hazard_type, road_type_id):
    from vdmp_progress.models import (
        flood_MDR_table,
        EQ_MDR_table,
        wind_MDR_table,
        house_type,
    )

    ht = house_type.objects.filter(
        house_type_id=road_type_id
    ).first()
    if not ht:
        return 0.0

    if hazard_type == "flood":
        rec = flood_MDR_table.objects.filter(
            house_type=ht,
            flood_depth_m__lte=hazard_value
        ).order_by("-flood_depth_m").first()

    elif hazard_type == "eq":
        rec = EQ_MDR_table.objects.filter(
            house_type=ht,
            PGA_g__lte=hazard_value
        ).order_by("-PGA_g").first()

    elif hazard_type == "wind":
        rec = wind_MDR_table.objects.filter(
            house_type=ht,
            wind_speed_kmph__lte=hazard_value
        ).order_by("-wind_speed_kmph").first()
    else:
        return 0.0

    return float(rec.MDR_value) if rec else 0.0

# -------------------------------

from osgeo import gdal
from shapely.geometry import box
import geopandas as gpd
import numpy as np
import os


def load_village_boundary(village_code):
    engine = get_sqlalchemy_engine()

    sql = """
    SELECT geom
    FROM public.village_boundary
    WHERE TRIM("Vill_ID") = %s;
    """

    gdf = gpd.read_postgis(
        sql,
        engine,
        params=(village_code,),
        geom_col="geom",
        crs="EPSG:4326"
    )

    if gdf.empty:
        raise RuntimeError(f"Village boundary not found for Vill_ID={village_code}")

    return gdf




def clip_raster_to_village(raster_path, village_gdf):
    """
    Clip raster to village boundary.
    Returns path to clipped raster (temporary file).
    """
    tmp_dir = tempfile.mkdtemp()
    clipped_raster = os.path.join(tmp_dir, "clipped.tif")

    village_geojson = os.path.join(tmp_dir, "village.geojson")
    village_gdf.to_file(village_geojson, driver="GeoJSON")

    gdal.Warp(
        clipped_raster,
        raster_path,
        cutlineDSName=village_geojson,
        cropToCutline=True,
        dstNodata=0,                         # 🔴 IMPORTANT
        dstSRS="EPSG:4326",
        resampleAlg=gdal.GRA_NearestNeighbour,  # 🔴 IMPORTANT
        outputType=gdal.GDT_Float32             # 🔴 IMPORTANT
    )

    # -------- VALIDATION --------
    ds = gdal.Open(clipped_raster)
    if ds is None:
        raise RuntimeError("Clipped raster not created")

    if ds.RasterXSize == 0 or ds.RasterYSize == 0:
        raise RuntimeError("Clipped raster is empty (no overlap)")

    gt = ds.GetGeoTransform()
    if gt is None:
        raise RuntimeError("Clipped raster has no geotransform")

    if gt[2] != 0 or gt[4] != 0:
        raise RuntimeError("Clipped raster is rotated (unsupported)")

    return clipped_raster



def raster_to_grid_gdf(
    raster_path,
    village_code,
    export_geojson=False,
    geojson_name="flood_grid_debug.geojson",
    eq=False
):
    """
    Convert raster pixels into vector grid polygons.
    Each polygon represents ONE raster pixel.

    Optionally exports the grid as GeoJSON
    to assam_crv/media for visual verification.
    """

    village_gdf = load_village_boundary(village_code)

    # --------------------------------------------------
    # 1. Open raster
    # --------------------------------------------------

    ds=None
    if eq:
        clipped_raster_path = clip_raster_to_village(
        raster_path,
        village_gdf
        )
        ds = gdal.Open(clipped_raster_path)
    else:
        clipped_raster_path = clip_raster_to_village(
            raster_path,
            village_gdf
        )
        ds = gdal.Open(clipped_raster_path)
    if not ds:
        raise RuntimeError("Cannot open raster")
    
    if ds is None:
        raise RuntimeError("Cannot open clipped raster")

    # ---- EXTRA SAFETY ----
    if ds.RasterXSize == 0 or ds.RasterYSize == 0:
        raise RuntimeError("Clipped raster has zero size")

    gt = ds.GetGeoTransform()
    if gt is None:
        raise RuntimeError("Clipped raster has no geotransform")

  

  

    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()

    gt = ds.GetGeoTransform()
    nodata = band.GetNoDataValue()
    crs = ds.GetProjection()

    rows, cols = arr.shape

    polygons = []
    values = []

    # --------------------------------------------------
    # 2. Loop through each pixel
    # --------------------------------------------------
    for row in range(rows):
        for col in range(cols):

            val = arr[row, col]

            # Skip NoData pixels
            if nodata is not None and val == nodata:
                val = 0.0   # treat as no hazard


            # Pixel bounds (lon/lat)
            x_min = gt[0] + col * gt[1]
            x_max = x_min + gt[1]
            y_max = gt[3] + row * gt[5]
            y_min = y_max + gt[5]

            polygons.append(
                box(x_min, y_min, x_max, y_max)
            )
            values.append(float(val))

    # --------------------------------------------------
    # 3. Create GeoDataFrame
    # --------------------------------------------------
    grid_gdf = gpd.GeoDataFrame(
        {"flood_depth_m": values},
        geometry=polygons,
        crs=crs
    )

    # Unique ID per pixel
    grid_gdf["grid_id"] = grid_gdf.index

    # --------------------------------------------------
    # 4. OPTIONAL: Export to GeoJSON for verification
    # --------------------------------------------------
    if export_geojson:
        media_dir = settings.MEDIA_ROOT
        os.makedirs(media_dir, exist_ok=True)

        geojson_path = os.path.join(media_dir, geojson_name)

        # GeoJSON driver
        grid_gdf.to_file(
            geojson_path,
            driver="GeoJSON"
        )

        print(f"✅ Grid GeoJSON exported to: {geojson_path}")

    return grid_gdf

# -------------------------------
# Load village roads (PostGIS)


def get_district_from_village(village_obj):
    """
    Safely derive district info from village object.
    """
    try:
        district = village_obj.gram_panchayat.circle.district
        return district.name, district.code
    except Exception:
        return None, None

def get_sqlalchemy_engine():
    """
    Create SQLAlchemy engine using Django DB settings.
    Keeps DB config in ONE place (env → settings.py).
    Properly escapes special characters in credentials.
    """

    db = settings.DATABASES["default"]

    engine_url = (
        f"postgresql+psycopg2://"
        f"{quote_plus(db['USER'])}:{quote_plus(db['PASSWORD'])}@"
        f"{db['HOST']}:{db['PORT']}/"
        f"{db['NAME']}"
    )

    return create_engine(engine_url)


import geopandas as gpd
from sqlalchemy.exc import ProgrammingError

def load_village_roads(village_code):
    """
    Load all road geometries and related attributes
    for a given village from PostGIS.

    Geometry CRS: EPSG:4326
    Length calculation will be done later in EPSG:32646
    """

    engine = get_sqlalchemy_engine()

    # First attempt: lowercase column names (recommended standard)
    sql_lower = """
        SELECT
            id,
            geom,
            rd_surface,
            rsur_type,
            ast_typo AS asset_type,
            rsurtypeid AS rsurtypeid,
            width,
            length,
            unitrpcost AS unit_cost
        FROM public.road_network
        WHERE TRIM(vill_id) = TRIM(%s)
        AND geom IS NOT NULL;
    """

    # Second attempt: quoted mixed-case column names
    sql_upper = """
        SELECT
            id,
            geom,
            "Rd_Surface" AS rd_surface,
            "RSur_Type" AS rsur_type,
            "Ast_Typo" AS asset_type,
            "Type_R" AS rsurtypeid,
            "Width" AS width,
            "Length" AS length,
            "UnitRpCost" AS unit_cost
        FROM public.road_network
        WHERE TRIM("Vill_ID") = TRIM(%s)
        AND geom IS NOT NULL;
    """

    # Try lowercase first
    try:
        roads_gdf = gpd.read_postgis(
            sql_lower,
            engine,
            params=(village_code,),
            geom_col="geom",
            crs="EPSG:4326"
        )

        if not roads_gdf.empty:
            print(f"📍 Loaded {len(roads_gdf)} road features for village {village_code}")
            return roads_gdf

    except Exception as e:
        print("Lowercase query failed. Trying uppercase version...")

    # Try uppercase version
    try:
        roads_gdf = gpd.read_postgis(
            sql_upper,
            engine,
            params=(village_code,),
            geom_col="geom",
            crs="EPSG:4326"
        )

        if not roads_gdf.empty:
            print(f"📍 Loaded {len(roads_gdf)} road features for village {village_code}")
            return roads_gdf

    except Exception as e:
        print("Uppercase query also failed.")

    print(f"⚠️ No roads found for village_code={village_code}")
    return gpd.GeoDataFrame()  # return empty GeoDataFrame



# Lengths in meters are only valid in projected CRS
def reproject_for_length(roads_gdf, grid_gdf):
    # Ensure CRS exists
    if roads_gdf.crs is None:
        raise ValueError("Roads GeoDataFrame has no CRS")

    if grid_gdf.crs is None:
        print("⚠️ grid_gdf CRS missing — assuming EPSG:4326")
        grid_gdf = grid_gdf.set_crs("EPSG:4326")

    roads_utm = roads_gdf.to_crs("EPSG:32646")
    grid_utm = grid_gdf.to_crs("EPSG:32646")

    return roads_utm, grid_utm


# ZONAL INTERSECTION (THIS IS THE KEY STEP)
def intersect_roads_with_grid(roads_utm, grid_utm):
    """
    Intersect roads with raster grid.
    Each output geometry lies inside ONE grid cell.
    """

    intersections = gpd.overlay(
        roads_utm,
        grid_utm,
        how="intersection"
    )

    return intersections

# Calculate road length per pixel
def calculate_road_length(intersections):
    """
    Calculate road length inside each grid cell.
    """
    intersections["road_length_m"] = intersections.geometry.length

    intersected_length = intersections["road_length_m"].sum()

    print("✂️ TOTAL INTERSECTED ROAD LENGTH:", intersected_length)
    # print("📉 MISSING LENGTH:", total_road_length - intersected_length)
    return intersections

# If multiple road pieces fall in the same pixel:
def aggregate_by_grid_and_road(intersections):
    """
    Aggregate road length per grid cell
    AND per road attributes.
    """
    print(f"📊 Aggregating {len(intersections)} intersection records...")

    result = (
        intersections
        .groupby(
            [
                "grid_id",
                "flood_depth_m",
                "rd_surface",
                "rsur_type",
                "asset_type",
                "rsurtypeid",
                "width",
                "unit_cost",
            ],
            as_index=False
        )
        .agg(
            road_length_m=("road_length_m", "sum")
        )
    )
    
    print(f"✅ Aggregated to {len(result)} unique grid-road combinations")
    return result




def get_road_flood_mdr(flood_depth_m, road_type_id):
    from vdmp_dashboard.models import roadFloodMDRMapping

    # No flood → no damage
    if flood_depth_m is None or flood_depth_m <= 0:
        return 0.0

    # 1️⃣ Round depth
    flood_depth = round(float(flood_depth_m), 2)

    # 2️⃣ Pick MDR curve dynamically (no hardcoding)
    # Assumes only ONE curve exists (current data reality)
    base_qs = roadFloodMDRMapping.objects.all()

    if not base_qs.exists():
        return 0.0

    # 3️⃣ Nearest LOWER depth
    record = (
        base_qs
        .filter(flood_depth_m__lte=flood_depth)
        .order_by("-flood_depth_m")
        .first()
    )

    # 4️⃣ If depth > max available → cap to max MDR
    if not record:
        record = base_qs.order_by("-flood_depth_m").first()

    return float(record.mdr) if record else 0.0



def save_grid_results(result_df, village_obj, village_code):
    from vdmp_dashboard.models import VillageRoadInfo
    from django.db import transaction

    district_name, district_code = get_district_from_village(village_obj)
    records = []
    
    print(f"💾 Preparing to save {len(result_df)} road grid results...")

    # -----------------------------
    # DELETE old data for village
    # -----------------------------
    with transaction.atomic():
        deleted_count, _ = VillageRoadInfo.objects.filter(
            village=village_obj
        ).delete()

        print(f"🧹 Deleted {deleted_count} old road records for village {village_obj.name}")

        # -----------------------------
        # Prepare new records
        # -----------------------------
        for _, row in result_df.iterrows():


            # -----------------------------
            # OLD logic (kept commented)
            # -----------------------------
            # flood_depth_m = (
            #     float(row["flood_depth_m"])
            #     if row["flood_depth_m"] is not None
            #     else None
            # )
            
            # -----------------------------
            # NEW forceful logic
            # -----------------------------
            raw_depth = (
                float(row["flood_depth_m"])
                if row["flood_depth_m"] is not None
                else None
            )

            if raw_depth is not None:
                adjusted_depth = raw_depth - 1

                # if negative → treat as no flood
                flood_depth_m = adjusted_depth if adjusted_depth > 0 else 0
                # OR use 0 instead of None:
                # flood_depth_m = adjusted_depth if adjusted_depth > 0 else 0
            else:
                flood_depth_m = None

            road_length_m = float(row["road_length_m"] or 0.0)

            asset_typology = row["rsur_type"] or "Unknown"
            asset_type = row.get("asset_type")
            if asset_type is not None and hasattr(asset_type, "strip"):
                asset_type = asset_type.strip() or None
            elif pd.isna(asset_type):
                asset_type = None
            road_type_id = row["rsurtypeid"]
            road_width_m = row["width"]
            unit_cost = float(row["unit_cost"] or 0.0)

            flood_class = _classify_flood(flood_depth_m)

            replacement_cost = road_length_m * unit_cost * road_width_m
            flood_mdr = get_road_flood_mdr(flood_depth_m, road_type_id)
            flood_loss = replacement_cost * flood_mdr

            records.append(
                VillageRoadInfo(
                    village=village_obj,
                    village_code=village_code,
                    village_name=village_obj.name,
                    district_name=district_name,
                    district_code=district_code,

                    asset_type=asset_type,
                    road_surface_type=asset_typology,
                    road_width_m=road_width_m,
                    road_type_id=road_type_id,

                    road_length_m=road_length_m,
                    flood_depth_m=flood_depth_m,
                    flood_class=flood_class,

                    unit_cost=unit_cost,
                    replacement_cost_inr=replacement_cost,
                    flood_hazard_mdr=flood_mdr,
                    flood_loss=flood_loss,
                )
            )

        # -----------------------------
        # Bulk insert
        # -----------------------------
        if records:
            VillageRoadInfo.objects.bulk_create(
                records,
                batch_size=1000
            )

            print(f"✅ Inserted {len(records)} new road records for village {village_obj.name}")


def get_road_unit_cost(asset_typology):
    from vdmp_dashboard.models import RoadUnitCost
    rec = RoadUnitCost.objects.filter(
        asset_typology__iexact=asset_typology
    ).first()
    return float(rec.unit_cost) if rec and rec.unit_cost else 0.0

def calculate_replacement_cost_road(
    road_length_m,
    road_width_m,
    unit_cost
):
    if not unit_cost or not road_width_m:
        return 0.0

    return float(road_length_m) * float(road_width_m) * float(unit_cost)





def process_road_flood_zonal_length(
    village_obj,
    village_code,
    flood_raster_path
):
    """
    Full zonal line length analysis:
    road length per flood raster pixel.
    """

    # 1. Raster → grid
    grid_gdf = raster_to_grid_gdf(flood_raster_path, village_code)

    # 2. Roads
    roads_gdf = load_village_roads(village_code)
    # Total road length (ground truth)
    roads_utm_tmp = roads_gdf.to_crs("EPSG:32646")
    total_road_length = roads_utm_tmp.geometry.length.sum()

    print("🧮 TOTAL ROAD LENGTH (UTM):", total_road_length)

    if roads_gdf.empty or grid_gdf.empty:
        return

    # 3. Reproject
    roads_utm, grid_utm = reproject_for_length(
        roads_gdf, grid_gdf
    )

    # 4. Intersection
    intersections = intersect_roads_with_grid(
        roads_utm, grid_utm
    )

    if intersections.empty:
        return

    # 5. Length calculation
    intersections = calculate_road_length(intersections)

    # 6. Aggregate
    result = aggregate_by_grid_and_road(intersections)


    # 7. Save
    save_grid_results(result, village_obj, village_code)


def process_road_eq_zonal_length(
    village_obj,
    village_code,
    eq_raster_path
):
    """
    Earthquake zonal road length analysis
    Raster value = PGA_g
    """
    print("🌊 Processing earthquake hazard zonal length...")
    from vdmp_dashboard.models import VillageRoadInfoEQ
    district_name, district_code = get_district_from_village(village_obj)
    # 1. Raster → grid
    grid_gdf = raster_to_grid_gdf(
        eq_raster_path,
        village_code,
        export_geojson=False,
        eq=True

    )

    # 2. Roads
    roads_gdf = load_village_roads(village_code)
    if roads_gdf.empty or grid_gdf.empty:
        return

    # 3. Reproject to UTM
    roads_utm, grid_utm = reproject_for_length(
        roads_gdf, grid_gdf
    )

    # 4. Intersection
    intersections = intersect_roads_with_grid(
        roads_utm, grid_utm
    )

    if intersections.empty:
        return

    # 5. Length calculation
    intersections["road_length_m"] = intersections.geometry.length

    # 6. Aggregate
    result = (
        intersections
        .groupby(
            [
                "grid_id",
                "flood_depth_m",  # this column stores raster value
                "rd_surface",
                "rsur_type",
                "rsurtypeid",
                "width",
                "unit_cost",
            ],
            as_index=False
        )
        .agg(
            road_length_m=("road_length_m", "sum")
        )
    )

    # 7. Save
    records = []

    for _, row in result.iterrows():

        eq_hazard = float(row["flood_depth_m"] or 0.0)
        road_length_m = float(row["road_length_m"] or 0.0)

        road_surface = row["rsur_type"]
        road_type_id = row["rsurtypeid"]
        road_width_m = row["width"]
        unit_cost = float(row["unit_cost"] or 0.0)

        replacement_cost = calculate_replacement_cost_road(
            road_length_m,
            road_width_m,
            unit_cost
        )

        eq_mdr = get_mdr_value(
            hazard_value=eq_hazard,
            hazard_type="eq",
            road_type_id=road_type_id
        )

        eq_loss = replacement_cost * eq_mdr

        records.append(
            VillageRoadInfoEQ(
                village=village_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_obj.name,
                village_code=village_code,
                road_surface_type=road_surface,
                road_constructed_by="Unknown",
                road_length_m=road_length_m,
                road_width_m=road_width_m,
                road_type_id=road_type_id,
                unit_cost=unit_cost,
                replacement_cost_inr=replacement_cost,
                eq_hazard=eq_hazard,
                eq_hazard_mdr=eq_mdr,
                eq_loss=eq_loss,
            )
        )

    if records:
        VillageRoadInfoEQ.objects.bulk_create(
            records, batch_size=1000
        )


def process_road_wind_zonal_length(
    village_obj,
    village_code,
    wind_raster_path
):
    """
    Wind zonal road length analysis
    Raster value = wind_speed_kmph
    """

    from vdmp_dashboard.models import VillageRoadInfoWind
    district_name, district_code = get_district_from_village(village_obj)
    # 1. Raster → grid
    grid_gdf = raster_to_grid_gdf(
        wind_raster_path,
        village_code,
        export_geojson=False
    )

    # 2. Roads
    roads_gdf = load_village_roads(village_code)
    if roads_gdf.empty or grid_gdf.empty:
        return

    # 3. Reproject
    roads_utm, grid_utm = reproject_for_length(
        roads_gdf, grid_gdf
    )

    # 4. Intersection
    intersections = intersect_roads_with_grid(
        roads_utm, grid_utm
    )

    if intersections.empty:
        return

    # 5. Length
    intersections["road_length_m"] = intersections.geometry.length

    # 6. Aggregate
    result = (
        intersections
        .groupby(
            [
                "grid_id",
                "flood_depth_m",  # raster value
                "rd_surface",
                "rsur_type",
                "rsurtypeid",
                "width",
                "unit_cost",
            ],
            as_index=False
        )
        .agg(
            road_length_m=("road_length_m", "sum")
        )
    )

    # 7. Save
    records = []

    for _, row in result.iterrows():

        wind_hazard = float(row["flood_depth_m"] or 0.0)
        road_length_m = float(row["road_length_m"] or 0.0)

        road_surface = row["rsur_type"]
        road_type_id = row["rsurtypeid"]
        road_width_m = row["width"]
        unit_cost = float(row["unit_cost"] or 0.0)

        replacement_cost = calculate_replacement_cost_road(
            road_length_m,
            road_width_m,
            unit_cost
        )

        wind_mdr = get_mdr_value(
            hazard_value=wind_hazard,
            hazard_type="wind",
            road_type_id=road_type_id
        )

        wind_loss = replacement_cost * wind_mdr

        records.append(
            VillageRoadInfoWind(
                village=village_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_obj.name,
                village_code=village_code,
                road_surface_type=road_surface,
                road_constructed_by="Unknown",
                road_length_m=road_length_m,
                road_width_m=road_width_m,
                road_type_id=road_type_id,
                unit_cost=unit_cost,
                replacement_cost_inr=replacement_cost,
                wind_hazard=wind_hazard,
                wind_hazard_mdr=wind_mdr,
                wind_loss=wind_loss,
            )
        )

    if records:
        VillageRoadInfoWind.objects.bulk_create(
            records, batch_size=1000
        )




def _process_road_flood_data(
    conn,
    village_obj,
    village_code,
    district_code,
    district_name,
    village_name,
    district_id
):
   

    # ------------------------------------------------------------------
    # Load rasters ONCE
    # ------------------------------------------------------------------
    flood_raster = village_flood_raster_Files.objects.filter(
        village_id=village_obj.id
    ).first()

    if not flood_raster:
        return

    dist_wind_raster = district_wind_raster_file.objects.filter(
        district_id=district_id
    ).first()

    dist_eq_raster = district_eq_raster_file.objects.filter(
        district_id=district_id
    ).first()

    # Fallback to state-level rasters if district-level not available
    wind_raster_path = os.path.join(settings.MEDIA_ROOT, dist_wind_raster.raster_file.name) if dist_wind_raster else os.path.join(settings.MEDIA_ROOT, "pipeline_data", "wind_raster", "Wind.tif")
    eq_raster_path = os.path.join(settings.MEDIA_ROOT, dist_eq_raster.raster_file.name) if dist_eq_raster else os.path.join(settings.MEDIA_ROOT, "pipeline_data", "eq_raster", "eq.tif")

    print("🌊 Processing flood hazard zonal length...")
    process_road_flood_zonal_length(
        village_obj,
        village_code,
        os.path.join(settings.MEDIA_ROOT, flood_raster.raster_file.name)
    )

    # process_road_eq_zonal_length(
    #     village_obj,
    #     village_code,
    #     eq_raster_path
    # )
    # process_road_wind_zonal_length(
    #     village_obj,
    #     village_code,
    #     wind_raster_path
    # )

 



def _process_road_erosion_data(
    conn,
    village_obj,
    village_code,
    district_code,
    district_name,
    village_name
):
    """
    Erosion analysis:
    - Road × river buffer intersection
    - Length of road inside erosion-prone buffers
    - One record per road feature (NOT grouped)
    """

    from vdmp_dashboard.models import VillageRoadInfoErosion
    from django.db import transaction
    
    print(f"🌊 Starting road erosion analysis for {village_name}...")

    # Delete old data first
    with transaction.atomic():
        deleted_count, _ = VillageRoadInfoErosion.objects.filter(village=village_obj).delete()
        print(f"🧹 Deleted {deleted_count} old road erosion records for {village_name}")

    # Try uppercase column names first (QGIS import)
    sql_upper = """
    WITH road_utm AS (
        SELECT
            id,
            "Rd_Surface" AS rd_surface,
            "RSur_Type" AS rsur_type,
            ST_Length(ST_Transform(ST_SetSRID(geom, 4326), 32646)) AS road_length_m,
            ST_Centroid(ST_Transform(ST_SetSRID(geom, 4326), 32646)) AS centroid_utm
        FROM public.road_network
        WHERE "Vill_ID" = %s
    ),
    
    buffer_utm AS (
        SELECT
            "BUFF_DIST" AS buffer_distance,
            ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
        FROM public.riverbuffer
    ),
    
    road_with_erosion AS (
        SELECT
            r.id,
            r.rd_surface,
            r.rsur_type,
            r.road_length_m,
            MIN(b.buffer_distance) AS min_buffer_distance,
            ST_Y(ST_Transform(r.centroid_utm, 4326)) AS lat,
            ST_X(ST_Transform(r.centroid_utm, 4326)) AS lon
        FROM road_utm r
        LEFT JOIN buffer_utm b
          ON ST_Intersects(r.centroid_utm, b.geom_utm)
        GROUP BY r.id, r.rd_surface, r.rsur_type, r.road_length_m, r.centroid_utm
    )
    
    SELECT
        id,
        rd_surface,
        rsur_type,
        min_buffer_distance,
        road_length_m,
        lat,
        lon
    FROM road_with_erosion;
    """

    # Fallback to lowercase column names (CLI import)
    sql_lower = """
    WITH road_utm AS (
        SELECT
            id,
            rd_surface,
            rsur_type,
            ST_Length(ST_Transform(ST_SetSRID(geom, 4326), 32646)) AS road_length_m,
            ST_Centroid(ST_Transform(ST_SetSRID(geom, 4326), 32646)) AS centroid_utm
        FROM public.road_network
        WHERE vill_id = %s
    ),
    
    buffer_utm AS (
        SELECT
            "BUFF_DIST" AS buffer_distance,
            ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
        FROM public.riverbuffer
    ),
    
    road_with_erosion AS (
        SELECT
            r.id,
            r.rd_surface,
            r.rsur_type,
            r.road_length_m,
            MIN(b.buffer_distance) AS min_buffer_distance,
            ST_Y(ST_Transform(r.centroid_utm, 4326)) AS lat,
            ST_X(ST_Transform(r.centroid_utm, 4326)) AS lon
        FROM road_utm r
        LEFT JOIN buffer_utm b
          ON ST_Intersects(r.centroid_utm, b.geom_utm)
        GROUP BY r.id, r.rd_surface, r.rsur_type, r.road_length_m, r.centroid_utm
    )
    
    SELECT
        id,
        rd_surface,
        rsur_type,
        min_buffer_distance,
        road_length_m,
        lat,
        lon
    FROM road_with_erosion;
    """

    rows = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql_upper, (village_code,))
            rows = cur.fetchall()
            print(f"✅ Query returned {len(rows)} road features (uppercase columns)")
    except Exception as e:
        print(f"⚠️ Uppercase columns failed, trying lowercase: {e}")
        conn.rollback()
        try:
            with conn.cursor() as cur:
                cur.execute(sql_lower, (village_code,))
                rows = cur.fetchall()
                print(f"✅ Query returned {len(rows)} road features (lowercase columns)")
        except Exception as e2:
            print(f"❌ Road erosion query failed: {e2}")
            conn.rollback()
            return

    records = []
    for id, surf, rsur, buff_dist, length, lat, lon in rows:
        records.append(
            VillageRoadInfoErosion(
                village=village_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_name,
                village_code=village_code,
                latitude=str(lat) if lat is not None else None,
                longitude=str(lon) if lon is not None else None,
                road_surface_type=rsur or surf,
                road_constructed_by="Unknown",
                road_length_m=length,
                erosion_class=_classify_erosion_buffer(buff_dist),
            )
        )

    if records:
        VillageRoadInfoErosion.objects.bulk_create(records, batch_size=1000)
        print(f"✅ Inserted {len(records)} road erosion records for {village_name}")
    else:
        print(f"⚠️ No road erosion records to save for {village_name}")



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_survey_data(df, district_code, village_code, activity_type="household", village_id=None):
    """
    Common data cleaning function for all VDMP activities
    
    Args:
        df: Raw dataframe from mobile_db
        district_code: District code for the village
        village_code: Village code
        activity_type: Type of activity (household, commercial, etc.)
        village_id: Village ID for fetching household data
    
    Returns:
        Cleaned dataframe with standardized columns and classifications
    """
    logger.info(f"Starting data cleaning for {activity_type} activity")
    logger.info(f"Input dataframe shape: {df.shape}")
    
    # Exclude columns from cleaning
    exclude_columns = ['latitude', 'longitude', 'unique_id', 'village_name', 'district_name', 'form_id']
    
    # Apply text and numeric cleaning
    for col in df.columns:
        if col in exclude_columns:
            logger.debug(f"Skipping cleaning for excluded column: {col}")
            continue
        
        logger.debug(f"Cleaning column: {col}")
        df[col] = df[col].apply(lambda v: _clean_text(v, col_name=col))
        df[col]= df[col].apply(lambda v: _remove_empty_parentheses(v))
        df[col] = df[col].apply(lambda v: _convert_numeric(v, col_name=col))
    
    # Add standard codes
    df['district_code'] = district_code
    df['village_code'] = village_code
    logger.info(f"Added district_code: {district_code}, village_code: {village_code}")
    
    # Get village_id if not provided
    if not village_id and village_code:
        try:
            village = tblVillage.objects.get(code=village_code)
            village_id = village.id
            logger.info(f"Found village_id: {village_id} for village_code: {village_code}")
        except tblVillage.DoesNotExist:
            logger.warning(f"Village not found for code: {village_code}")
    
    # Extract flood depth from raster file and erosion buffer values (for all activity types)
    if village_id:
        df = extract_flood_depth_from_raster(df, village_id)
    df = extract_erosion_buffer_values_postgis(df)
    
    # Apply activity-specific processing
    if activity_type == "household":
        df = _process_household_specific(df, village_id)
    elif activity_type == "others":
        # For others (transformer/electric pole), apply flood depth mapping and building area calculation
        if village_id:
            df = map_flood_depth_from_household_db(df, village_id)
        df = _calculate_building_area(df)
    else:
        # For non-household activities, apply flood depth mapping and building area calculation
        if village_id:
            df = map_flood_depth_from_household_db(df, village_id)
        df = _calculate_building_area(df)
        df = _process_commercial_specific(df)
    
    logger.info(f"Cleaning completed. Output dataframe shape: {df.shape}")
    return df

def map_flood_depth_from_household_db(child_df, village_id):
    """Map flood depth, flood class, and erosion class from household database records to child activities"""
   
    
    if "flood_depth_m" not in child_df.columns:
        child_df["flood_depth_m"] = None
    if "flood_class" not in child_df.columns:
        child_df["flood_class"] = None
    if "erosion_class" not in child_df.columns:
        child_df["erosion_class"] = None

    flood_mask = (
        child_df["flood_depth_m"].isna() |
        (child_df["flood_depth_m"] <= 0)
    )
    flood_class_mask = child_df["flood_class"].isna()
    erosion_mask = child_df["erosion_class"].isna()

    if flood_mask.sum() == 0 and flood_class_mask.sum() == 0 and erosion_mask.sum() == 0:
        return child_df

    logger.info(f"🌧 Extracting flood and erosion data from raster for {max(flood_mask.sum(), flood_class_mask.sum(), erosion_mask.sum())} rows")

    # Extract flood depth from raster for missing values
    if flood_mask.sum() > 0:
        child_df = extract_flood_depth_from_raster(child_df, village_id)
    
    # Extract erosion class from PostGIS for missing values
    if erosion_mask.sum() > 0:
        child_df = extract_erosion_buffer_values_postgis(child_df)
        # Apply erosion classification using buffer values
        if 'erosion_buffer_m' in child_df.columns:
            child_df['erosion_class'] = child_df['erosion_buffer_m'].apply(_classify_erosion_buffer)
        elif 'your_agriculture_field_vulnerable_to_erosion' in child_df.columns:
            child_df['erosion_class'] = child_df['your_agriculture_field_vulnerable_to_erosion'].apply(_classify_erosion)
        else:
            child_df['erosion_class'] = None

    logger.info("✔ Flood depth and erosion class extracted from raster and PostGIS")
    return child_df

def extract_numeric_value(value):
    """Extract numeric value from string"""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        # Try to extract number from string
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', str(value))
        if match:
            return float(match.group(1))
        return None

def _calculate_building_area(df):
    """Calculate building area for non-household activities"""
    logger.info("Calculating building area")
    
    # Fill default values for length/width
    length_default = 30
    width_default = 20

    length_columns = [
        "Approximate_length_feet_of_the_house_main_building",
        "Approximate_length_feet_of_building",
        "average_room_length_ft",
        
    ]

    width_columns = [
        "Approximate_width_feet_of_the_house_main_building",
        "Approximate_width_feet_of_building",
        "average_room_width_ft"
    ]

    for col in length_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(length_default)

    for col in width_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(width_default)

    # Building area calculation
    length_candidates = [
        "Approximate_length_feet_of_the_house_main_building",
        "Approx_length",
        "average_room_length_ft",
        "Approximate_length_feet_of_building"
    ]
    width_candidates = [
        "Approximate_width_feet_of_the_house_main_building",
        "Approx_width",
        "average_room_width_ft",
        "Approximate_width_feet_of_building"
    ]
    
    length_col = next((c for c in length_candidates if c in df.columns), None)
    width_col = next((c for c in width_candidates if c in df.columns), None)

    if length_col and width_col:
        df["Building_Area_sqft"] = df.apply(
            lambda row: (extract_numeric_value(row[length_col]) * extract_numeric_value(row[width_col]))
            if extract_numeric_value(row[length_col]) is not None and extract_numeric_value(row[width_col]) is not None
            else None,
            axis=1
        )
        logger.info(f"Calculated Building_Area_sqft using {length_col} x {width_col}")
    else:
        if "Building_Area_sqft" in df.columns:
            logger.info("Found existing Building_Area_sqft column - using as is.")
        else:
            logger.info("Skipping Building_Area_sqft calculation (length/width not found).")
    
    return df

def _calculate_household_building_area(df):
    """Calculate building dimensions and area for household surveys"""
    logger.info("Calculating household building dimensions and area")
    
    # Default values for missing length/width
    length_default = 30
    width_default = 20
    
    # Building length columns to check
    length_columns = [
        "approximate_length_feet_of_the_house_main_building",
        "building_length_feet"
    ]
    
    # Building width columns to check
    width_columns = [
        "approximate_width_feet_of_the_house_main_building", 
        "building_width_feet"
    ]
    
    # Find the length column
    length_col = next((c for c in length_columns if c in df.columns), None)
    width_col = next((c for c in width_columns if c in df.columns), None)
    
    # Extract and clean length values
    if length_col:
        df['building_length_feet'] = df[length_col].apply(extract_numeric_value)
        logger.debug(f"Extracted building length from {length_col}")
    else:
        df['building_length_feet'] = None
        logger.debug("No building length column found")
    
    # Extract and clean width values  
    if width_col:
        df['building_width_feet'] = df[width_col].apply(extract_numeric_value)
        logger.debug(f"Extracted building width from {width_col}")
    else:
        df['building_width_feet'] = None
        logger.debug("No building width column found")
    
    # Fill missing values with defaults
    df['building_length_feet'] = df['building_length_feet'].fillna(length_default)
    df['building_width_feet'] = df['building_width_feet'].fillna(width_default)
    
    # Convert feet to meters (1 foot = 0.3048 meters)
    df['building_length_meter'] = (df['building_length_feet'] * 0.3048).round(2)
    df['building_width_meter'] = (df['building_width_feet'] * 0.3048).round(2)
    
    # Calculate area in square meters and square feet
    df['build_area_meter'] = (df['building_length_meter'] * df['building_width_meter']).round(2)
    df['building_area_sqft'] = (df['building_length_feet'] * df['building_width_feet']).round(2)
    
    logger.info(f"Calculated building dimensions - Length: {df['building_length_feet'].mean():.1f}ft, Width: {df['building_width_feet'].mean():.1f}ft, Area: {df['build_area_meter'].mean():.1f}m²")
    
    return df
    

def _remove_empty_parentheses(x):
    """Remove empty or punctuation-only parentheses"""
    if pd.isna(x) or not isinstance(x, str):
        return x
    
    # Special case: Remove ( Or ), ( or ), ( OR ), (/- Or -/) patterns
    x = re.sub(r'\(\s*[/\-]*\s*[Oo][Rr]\s*[/\-]*\s*\)', '', x)
    
    # Remove empty or punctuation-only parentheses - multiple passes to handle nested cases
    for _ in range(3):  # Run multiple times to handle deeply nested cases
        x = re.sub(r'\([\s,\/\-\(\)]*\)', '', x)
    
    return x.strip()

def _clean_text(x, col_name=None):
    """Clean text fields matching original cleaning script"""
    if pd.isna(x) or not isinstance(x, str):
        return x
    
    x = str(x).strip()
    if x == "" or x.startswith(("http://", "https://")):
        return x
    
    # Remove non-English content in parentheses
    x = re.sub(r'\([^A-Za-z0-9\s\.\-,\/\+\&:_%\']*\)', '', x)
    
    # Keep common punctuation like / + & - , . and parentheses (matching original)
    x = re.sub(r'[^A-Za-z0-9\s\.\-<\(\),\/\+\&:_%\']', '', x)
    x = re.sub(r'\s+', ' ', x).strip()
    
    # Title case with special handling
    x = x.title()
    
    # Fix acronyms
    x = re.sub(r'\bTv\b', 'TV', x)
    
    # preserve OBC in community column
    if col_name and "community" in col_name.lower():
        x = re.sub(r'\bObc\b', 'OBC', x)
    
    # Remove empty parentheses after all other processing
    x = _remove_empty_parentheses(x)
    
    return x

def _convert_numeric(x, col_name=None):
    """Convert numeric-like strings to float only for numeric fields"""
    if pd.isna(x) or isinstance(x, (int, float)):
        return x
    
    s = str(x).strip()
    if s == "" or s.startswith(("http://", "https://")):
        return x
    
    # Only convert if column name suggests it's numeric
    numeric_keywords = ['amount', 'number', 'height', 'income', 'expense', 'cost', 'price', 'value', 'bigha', 'year', 'age']
    if col_name and any(keyword in col_name.lower() for keyword in numeric_keywords):
        # Extract numeric value
        m = re.search(r'(-?\d+(?:\.\d+)?)', s.replace(',', ''))
        if m:
            try:
                num_val = float(m.group(1))
                # Return int if it's a whole number, otherwise float
                return int(num_val) if num_val.is_integer() else num_val
            except:
                return x
    return x

def _process_household_specific(df, village_id=None):
    """Apply household-specific processing and classifications"""
    logger.info("Applying household-specific processing")
    
    # Unit conversions (feet to meters)
    if 'maximum_flood_height_in_house_ft' in df.columns:
        df['maximum_flood_height_meter'] = df['maximum_flood_height_in_house_ft'].apply(
            lambda x: (x * 0.3048) if pd.notna(x) and isinstance(x, (int, float)) else None
        )
        logger.debug("Converted flood height from feet to meters")
    
    if 'plinth_or_stilt_height_ft' in df.columns:
        df['plinth_or_stilt_height_meter'] = df['plinth_or_stilt_height_ft'].apply(
            lambda x: (x * 0.3048) if pd.notna(x) and isinstance(x, (int, float)) else None
        )
        logger.debug("Converted plinth height from feet to meters")
    
    # Extract flood depth from raster file
    if village_id:
        df = extract_flood_depth_from_raster(df, village_id)
    
    # Extract erosion buffer values from shapefiles
    df = extract_erosion_buffer_values_postgis(df)
    
    # Calculate building dimensions and area for household
    df = _calculate_household_building_area(df)
    
    # Apply classifications
    df = _apply_classifications(df)
    
    return df

def _process_commercial_specific(df):
    """Apply commercial-specific processing"""
    logger.info("Applying commercial-specific processing")
    # Add commercial-specific logic here
    return df

def _apply_classifications(df):
    """Apply classification logic to dataframe"""
    logger.info("Applying classification logic")
    
    # Flood depth classification - use raster value from flood_depth_m
    if 'flood_depth_m' in df.columns:
        df['flood_class'] = df['flood_depth_m'].apply(_classify_flood)
        df['FLOOD_CLASS2'] = df['flood_depth_m'].apply(_classify_flood)
        logger.debug("Applied flood depth classification from raster")
    
    # Loan classifications
    if 'loan_amount' in df.columns:
        df['loan_class'] = df['loan_amount'].apply(_classify_loan)
        # df['loan_class_1'] = df['loan_amount'].apply(_classify_loan)  # Same as loan_class
        logger.debug("Applied loan classification")
    
    # Agricultural land classification
    if 'area_of_agriculture_land_owned_bigha' in df.columns:
        df['area_of_agriculture_land_owned_bigha'] = pd.to_numeric(
            df['area_of_agriculture_land_owned_bigha'], errors='coerce'
        ).fillna(0)
        df['agrculture_land_class'] = df['area_of_agriculture_land_owned_bigha'].apply(_classify_agri_land)
        logger.debug("Applied agricultural land classification")
    
    # Flood height household classification
    if 'maximum_flood_height_in_house_ft' in df.columns:
        df['fld_hh_class'] = df['maximum_flood_height_in_house_ft'].apply(_classify_flood_height)
        logger.debug("Applied flood height household classification")
    
    # Repair cost classification
    if 'expense_on_house_repair' in df.columns:
        df['repair_class'] = df['expense_on_house_repair'].apply(_classify_cost)
        logger.debug("Applied repair cost classification")
    
    # Economic loss household classification
    if 'economic_loss_to_your_house_due_to_flood' in df.columns:
        df['economic_loss_hh'] = df['economic_loss_to_your_house_due_to_flood'].apply(_classify_cost)
        logger.debug("Applied economic loss household classification")
    
    # Agriculture livelihood loss classification
    if 'loss_agricultire_livlihood' in df.columns:
        df['loss_AgriLivli'] = df['loss_agricultire_livlihood'].apply(_classify_cost)
        logger.debug("Applied agriculture livelihood loss classification")
    else:
        logger.debug(f"Agriculture livestock columns not found. Available columns: {[col for col in df.columns if 'agriculture' in col.lower() or 'livestock' in col.lower()]}")
    
    
    # Big cattle classification
    if 'number_of_big_cattle_animals' in df.columns:
        df['big_cattle'] = df['number_of_big_cattle_animals'].apply(lambda x: _classify_cattle(x, big=True))
        logger.debug("Applied big cattle classification")
    
    # Small cattle classification
    if 'number_of_small_cattle_animals' in df.columns:
        df['small_cattle'] = df['number_of_small_cattle_animals'].apply(lambda x: _classify_cattle(x, big=False))
        logger.debug("Applied small cattle classification")
    
    # House type classification
    if 'wall_type' in df.columns and 'roof_type' in df.columns:
        df['house_type'] = df.apply(
            lambda row: _classify_house_type(row['wall_type'], row['roof_type']), axis=1
        )
        logger.debug("Applied house type classification")
    
    # Income classification
    if 'approximate_income_earned_every_year_inr' in df.columns:
        df['income_class'] = df['approximate_income_earned_every_year_inr'].apply(_classify_income)
        logger.debug("Applied income classification")
    
    # Duration classification
    # if 'duration_of_flood_stay_in_your_agriculture_field' in df.columns:
    #     df['duration_class'] = df['duration_of_flood_stay_in_your_agriculture_field'].apply(_classify_duration)
    #     logger.debug("Applied duration classification")
    
    # Erosion classification - use buffer values from erosion_buffer_m
    if 'erosion_buffer_m' in df.columns:
        df['erosion_class'] = df['erosion_buffer_m'].apply(_classify_erosion_buffer)
        logger.debug("Applied erosion buffer classification")
    elif 'your_agriculture_field_vulnerable_to_erosion' in df.columns:
        df['erosion_class'] = df['your_agriculture_field_vulnerable_to_erosion'].apply(_classify_erosion)
    else:
        df['erosion_class'] = None
    logger.debug("Applied erosion classification")
    
    # Flood depth from survey classification (FLOOD_CLASS2)
    if 'flood_depth_m' in df.columns:
        df['FLOOD_CLASS2'] = df['flood_depth_m'].apply(_classify_flood)
        logger.debug("Applied FLOOD_CLASS2 classification")
        logger.debug("Applied FLOOD_CLASS2 classification")
    
    # Sanitation type classification
    if 'sanitation_facility' in df.columns:
        df['Sanitation_Type'] = df['sanitation_facility']
        logger.debug("Applied sanitation type classification")
    
    # Crops diversity calculation (proper classification)
    if 'number_of_crops_normally_raised_every_year' in df.columns:
        df['crops_diversity'] = df['number_of_crops_normally_raised_every_year'].apply(_classify_crops_diversity)
        logger.debug("Applied crops diversity classification")
    
    # Toilet classification
    if 'toilet_wall_material' in df.columns and 'toilet_roof_material' in df.columns and 'sanitation_facility' in df.columns:
        df['toilet_class'] = df.apply(
            lambda row: _classify_toilet_type(row['toilet_wall_material'], row['toilet_roof_material'], row['sanitation_facility']), axis=1
        )
        logger.debug("Applied toilet classification")
    
    return df

import math

def _classify_flood(depth):
    """
    Classify flood depth into categories.
    ALWAYS returns a non-null string.
    """

    # No data from raster
    if depth is None:
        return "No Data"

    # Handle NaN explicitly
    if isinstance(depth, float) and math.isnan(depth):
        return "No Data"

    try:
        depth = float(depth)
    except (ValueError, TypeError):
        return "No Data"

    # No flooding
    if depth <= 0:
        return "No Flood"

    if depth <= 0.3:
        return "0 – 0.3 m"

    if depth <= 0.5:
        return "0.3 – 0.5 m"

    if depth <= 1.0:
        return "0.5 – 1.0 m"

    return ">1.0 m"


def _classify_loan(amount):
    """Classify loan amount into categories"""
    if pd.isna(amount): return "No loan"
    try:
        amount = int(float(amount))
        if amount <= 0: return "No loan"
        if amount < 10000: return "Upto 10K"
        elif amount < 50000: return "Upto 50K"
        elif amount < 100000: return "Upto 100K"
        else: return "Morethan 100K"
    except (ValueError, TypeError):
        return "No loan"

def _classify_agri_land(area):
    """Classify agricultural land area"""
    if pd.isna(area): return None
    try:
        area = int(float(area))
        if area < 0.5: return "Lessthan 0.5 bigha"
        elif area < 1.5: return "Upto 1.5 bigha"
        elif area <= 2.5: return "Upto 2.5 bigha"
        else: return "Morethan 2.5 bigha"
    except (ValueError, TypeError):
        return None

def _classify_flood_height(height_ft):
    """Classify flood height in feet"""
    if pd.isna(height_ft): return "No Flood"
    try:
        height_ft = float(height_ft)
        if height_ft <= 0: return "No Flood"
        if height_ft < 0.5: return "Upto 0.5ft"
        elif height_ft < 1.5: return "Upto 1.5ft"
        elif height_ft < 2.5: return "Upto 2.5ft"
        else: return "Morethan 2.5ft"
    except (ValueError, TypeError):
        return "No Flood"

def _classify_cost(val):
    """Classify cost values"""
    if pd.isna(val): return "None"
    try:
        val = float(val)
        if val <= 0: return "None"
        if val < 5000: return "Upto 5K"
        elif val < 15000: return "Upto 15K"
        elif val < 25000: return "Upto 25K"
        else: return "Morethan 25K"
    except (ValueError, TypeError):
        return "None"

def _classify_cattle(num, big=True):
    """Classify cattle numbers"""
    if pd.isna(num): return "No big cattle" if big else "No small cattle"
    try:
        num = int(float(num))
        if num <= 0: return "No big cattle" if big else "No small cattle"
        if num < 4: return "Upto 3 big cattle" if big else "Upto 3 small cattle"
        elif num < 6: return "3 to 6 big cattle" if big else "3 to 6 small cattle"
        else: return "Morethan 6 big cattle" if big else "Morethan 6 small cattle"
    except (ValueError, TypeError):
        return "No big cattle" if big else "No small cattle"

def _classify_income(income):
    """Classify income levels"""
    if pd.isna(income): return None
    try:
        income = float(income)
        if income <= 50000: return "Upto 50K"
        elif income <= 150000: return "Upto 150K"
        elif income <= 250000: return "Upto 250K"
        else: return ">250K"
    except (ValueError, TypeError):
        return None

def _classify_house_type(wall, roof):
    """Classify house type based on wall and roof materials"""
    wall_map = {
       "brick with cement": "brick with cement",
        "brick without cement": "brick with cement",
        "concrete frame with infill brick walls": "brick with cement",

        "wood": "wood",
        "wood, bamboo & cow dung": "wood",
        "wood, bamboo & cow dung/mud": "wood",

        "grass": "grass",
        "grass/leaves/plastic": "grass",
        "grass/leaves/plastic & cow dung/mud": "grass",
    }
    roof_map = {
        "tin": "tin", "wood": "wood", "grass": "grass",
        "concrete": "concrete", "stone slabs": "concrete", "tiles": "concrete",
        "bamboo": "thatch", "ikra": "thatch", "thatch": "thatch"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), w)
    r_norm = next((v for k, v in roof_map.items() if k in r), r)
    
    if w_norm == "brick with cement" and r_norm == "concrete":
        return "Pucca"
    elif w_norm == "brick with cement" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"
       

def _classify_agri_land(area):
    """Classify agricultural land area"""
    if pd.isna(area): return None
    try:
        area = int(float(area))
        if area < 0.5: return "Lessthan 0.5 bigha"
        elif area < 1.5: return "Upto 1.5 bigha"
        elif area <= 2.5: return "Upto 2.5 bigha"
        else: return "Morethan 2.5 bigha"
    except (ValueError, TypeError):
        return None

def _classify_flood_height(height_ft):
    """Classify flood height in feet"""
    if pd.isna(height_ft): return "No Flood"
    try:
        height_ft = float(height_ft)
        if height_ft <= 0: return "No Flood"
        if height_ft < 0.5: return "Upto 0.5ft"
        elif height_ft < 1.5: return "Upto 1.5ft"
        elif height_ft < 2.5: return "Upto 2.5ft"
        else: return "Morethan 2.5ft"
    except (ValueError, TypeError):
        return "No Flood"

def _classify_cost(val):
    """Classify cost values"""
    if pd.isna(val): return "None"
    try:
        val = float(val)
        if val <= 0: return "None"
        if val < 5000: return "Upto 5K"
        elif val < 15000: return "Upto 15K"
        elif val < 25000: return "Upto 25K"
        else: return "Morethan 25K"
    except (ValueError, TypeError):
        return "None"

def _classify_cattle(num, big=True):
    """Classify cattle numbers"""
    if pd.isna(num): return "No big cattle" if big else "No small cattle"
    try:
        num = int(float(num))
        if num <= 0: return "No big cattle" if big else "No small cattle"
        if num < 4: return "Upto 3 big cattle" if big else "Upto 3 small cattle"
        elif num < 6: return "3 to 6 big cattle" if big else "3 to 6 small cattle"
        else: return "Morethan 6 big cattle" if big else "Morethan 6 small cattle"
    except (ValueError, TypeError):
        return "No big cattle" if big else "No small cattle"

def _classify_income(income):
    """Classify income levels"""
    if pd.isna(income): return None
    try:
        income = float(income)
        if income <= 50000: return "Upto 50K"
        elif income <= 150000: return "Upto 100K"
        elif income <= 250000: return "Upto 250K"
        else: return ">250K"
    except (ValueError, TypeError):
        return None

def _classify_house_type(wall, roof):
    """Classify house type based on wall and roof materials"""
    wall_map = {
        "brick with cement": "brick with cement",
        "brick without cement": "brick with cement",
        "concrete frame with infill brick walls": "brick with cement",
        "wood": "wood",
        "wood, bamboo & cow dung": "wood",
        "grass": "grass",
        "grass/leaves/plastic": "grass"
    }
    roof_map = {
        "tin": "tin", "wood": "wood", "grass": "grass",
        "concrete": "concrete", "stone slabs": "concrete", "tiles": "concrete",
        "bamboo": "thatch", "ikra": "thatch", "thatch": "thatch"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), w)
    r_norm = next((v for k, v in roof_map.items() if k in r), r)
    
    if w_norm == "brick with cement" and r_norm == "concrete":
        return "Pucca"
    elif w_norm == "brick with cement" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"
     

def _classify_agri_land(area):
    """Classify agricultural land area"""
    if pd.isna(area): return None
    try:
        area = int(float(area))
        if area < 0.5: return "Lessthan 0.5 bigha"
        elif area < 1.5: return "Upto 1.5 bigha"
        elif area <= 2.5: return "Upto 2.5 bigha"
        else: return "Morethan 2.5 bigha"
    except (ValueError, TypeError):
        return None

def _classify_flood_height(height_ft):
    """Classify flood height in feet"""
    if pd.isna(height_ft): return "No Flood"
    try:
        height_ft = float(height_ft)
        if height_ft <= 0: return "No Flood"
        if height_ft < 0.5: return "Upto 0.5ft"
        elif height_ft < 1.5: return "Upto 1.5ft"
        elif height_ft < 2.5: return "Upto 2.5ft"
        else: return "Morethan 2.5ft"
    except (ValueError, TypeError):
        return "No Flood"

def _classify_cost(val):
    """Classify cost values"""
    if pd.isna(val): return "None"
    try:
        val = float(val)
        if val <= 0: return "None"
        if val < 5000: return "Upto 5K"
        elif val < 15000: return "Upto 15K"
        elif val < 25000: return "Upto 25K"
        else: return "Morethan 25K"
    except (ValueError, TypeError):
        return "None"

def _classify_cattle(num, big=True):
    """Classify cattle numbers"""
    if pd.isna(num): return "No big cattle" if big else "No small cattle"
    try:
        num = int(float(num))
        if num <= 0: return "No big cattle" if big else "No small cattle"
        if num < 4: return "Upto 3 big cattle" if big else "Upto 3 small cattle"
        elif num < 6: return "3 to 6 big cattle" if big else "3 to 6 small cattle"
        else: return "Morethan 6 big cattle" if big else "Morethan 6 small cattle"
    except (ValueError, TypeError):
        return "No big cattle" if big else "No small cattle"

def _classify_income(income):
    """Classify income levels"""
    if pd.isna(income): return None
    try:
        income = float(income)
        if income <= 50000: return "Upto 50K"
        elif income <= 150000: return "Upto 100K"
        elif income <= 250000: return "Upto 250K"
        else: return ">250K"
    except (ValueError, TypeError):
        return None

def _classify_house_type(wall, roof):
    """Classify house type based on wall and roof materials"""
    wall_map = {
        "brick with cement": "brick with cement",
        "brick without cement": "brick with cement",
        "concrete frame with infill brick walls": "brick with cement",
        "wood": "wood",
        "wood, bamboo & cow dung": "wood",
        "grass": "grass",
        "grass/leaves/plastic": "grass"
    }
    roof_map = {
        "tin": "tin", "wood": "wood", "grass": "grass",
        "concrete": "concrete", "stone slabs": "concrete", "tiles": "concrete",
        "bamboo": "thatch", "ikra": "thatch", "thatch": "thatch"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), w)
    r_norm = next((v for k, v in roof_map.items() if k in r), r)
    
    if w_norm == "brick with cement" and r_norm == "concrete":
        return "Pucca"
    elif w_norm == "brick with cement" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"

def _classify_duration(duration):
    """Classify flood duration"""
    if pd.isna(duration): return None
    duration_str = str(duration).strip().lower()
    if "20" in duration_str and ("more" in duration_str or ">" in duration_str):
        return ">20 Days"
    elif "15" in duration_str and "20" in duration_str:
        return "15-20 Days"
    elif "7" in duration_str and "15" in duration_str:
        return "7-15 Days"
    else:
        return duration_str

def _classify_erosion_buffer(buffer_value):
    # print(f"Classifying erosion buffer value: {buffer_value}")
    """Classify erosion based on buffer distance"""
    if pd.isna(buffer_value) or buffer_value is None or buffer_value == 'None':
        return "Low"
    try:
        buffer_value = float(buffer_value)
        if buffer_value <= 50:
            return "Severe"
        elif buffer_value <= 100:
            return "High"
        elif buffer_value <= 150:
            return "Medium"
        else:
            return "Low"
    except (ValueError, TypeError):
        return "Low"


def validate_gis_data_availability(village_obj):
    """
    Validate required GIS data.
    River buffer / erosion is OPTIONAL.
    """
    from layers.models import (
        village_flood_raster_Files,
        district_wind_raster_file,
        district_eq_raster_file,
    )
    from django.db import connection
    import os

    errors = []
    warnings = []

    # ----------------------------
    # Flood raster (MANDATORY)
    # ----------------------------
    flood_raster = village_flood_raster_Files.objects.filter(village=village_obj).first()
    if not flood_raster or not flood_raster.raster_file:
        errors.append(f"Flood raster not available for village {village_obj.name}")

    # ----------------------------
    # District resolution
    # ----------------------------
    try:
        district = village_obj.gram_panchayat.circle.district
    except Exception:
        errors.append("Unable to determine district for village")
        return errors, warnings

    # ----------------------------
    # Wind raster (MANDATORY with fallback)
    # ----------------------------
    wind_raster = district_wind_raster_file.objects.filter(district=district).first()
    if not wind_raster or not wind_raster.raster_file:
        wind_fallback = os.path.join(settings.MEDIA_ROOT, "pipeline_data", "wind_raster", "Wind.tif")
        if not os.path.exists(wind_fallback):
            errors.append(
                f"Wind raster not available for district {district.name} "
                "and state-level fallback not found"
            )

    # ----------------------------
    # Earthquake raster (MANDATORY with fallback)
    # ----------------------------
    eq_raster = district_eq_raster_file.objects.filter(district=district).first()
    if not eq_raster or not eq_raster.raster_file:
        eq_fallback = os.path.join(settings.MEDIA_ROOT, "pipeline_data", "eq_raster", "eq.tif")
        if not os.path.exists(eq_fallback):
            errors.append(
                f"Earthquake raster not available for district {district.name} "
                "and state-level fallback not found"
            )

    # ----------------------------
    # River buffer / erosion (OPTIONAL)
    # ----------------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'riverbuffer'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                warnings.append("River buffer table does not exist (erosion risk will be skipped)")
            else:
                cursor.execute(
                    'SELECT COUNT(*) FROM public.riverbuffer WHERE "Vill_ID" = %s',
                    [village_obj.code],
                )
                buffer_count = cursor.fetchone()[0]

                if buffer_count == 0:
                    warnings.append(
                        f"No river buffer / erosion zones for village {village_obj.name} "
                        "(this is expected for many villages)"
                    )
    except Exception as e:
        warnings.append(f"River buffer check failed, skipping erosion risk: {str(e)}")

    return errors, warnings


def process_household_risk_assessment(village_obj, village_code, flood_raster_path):
    """Process household risk assessment with flood and erosion classification"""
    from vdmp_dashboard.models import HouseholdSurvey
    
    # Get household data
    household_df = get_household_data_for_village(village_code)
    if household_df.empty:
        return
    
    # Extract flood depth and erosion buffer values
    household_df = extract_flood_depth_from_raster(household_df, village_code)
    household_df = extract_erosion_buffer_values_postgis(household_df)
    
    # Apply classifications
    household_df['flood_class'] = household_df['flood_depth_m'].apply(_classify_flood)
    household_df['erosion_class'] = household_df['erosion_buffer_m'].apply(_classify_erosion_buffer)
    
    # Save to database
    save_household_results(household_df, village_obj, village_code)


def map_flood_depth_from_household_db(child_df, village_id):
    """Map flood depth, flood class, and erosion class from household database records to child activities"""
    from vdmp_dashboard.models import HouseholdSurvey
    
    if "flood_depth_m" not in child_df.columns:
        child_df["flood_depth_m"] = None
    if "flood_class" not in child_df.columns:
        child_df["flood_class"] = None
    if "erosion_class" not in child_df.columns:
        child_df["erosion_class"] = None

    flood_mask = (
        child_df["flood_depth_m"].isna() |
        (child_df["flood_depth_m"] <= 0)
    )
    flood_class_mask = child_df["flood_class"].isna()
    erosion_mask = child_df["erosion_class"].isna()
    
    # Get household data for mapping
    household_records = HouseholdSurvey.objects.filter(
        village_code=village_id
    ).values('flood_depth_m', 'flood_class', 'erosion_class')
    
    if household_records:
        # Use first available record for mapping (you may want to implement more sophisticated logic)
        sample_record = household_records[0]
        
        # Map flood data
        if flood_mask.any():
            child_df.loc[flood_mask, "flood_depth_m"] = sample_record.get('flood_depth_m')
        
        if flood_class_mask.any():
            child_df.loc[flood_class_mask, "flood_class"] = sample_record.get('flood_class')
        
        if erosion_mask.any():
            child_df.loc[erosion_mask, "erosion_class"] = sample_record.get('erosion_class')
    
    return child_df


def _process_model_flood_erosion(queryset, village_id, model_type):
    """Process flood depth and erosion values for a model queryset"""
    import pandas as pd
    
    # Get appropriate fields based on model type
    if model_type == 'household':
        fields = ['id', 'latitude', 'longitude', 'flood_depth_m', 'erosion_value', 'flood_depth_from_survey_meter']
    else:
        fields = ['id', 'latitude', 'longitude', 'flood_depth_m', 'erosion_value']
    
    # Convert queryset to DataFrame
    records = list(queryset.values(*fields))
    if not records:
        return
        
    df = pd.DataFrame(records)
    print("DataFrame length before processing:", len(df))
    # Always extract flood depth from raster
    print(f"Extracting flood depth for {len(df)} {model_type} records...")
    
    df = extract_flood_depth_from_raster(df, village_id)
    
    # Always extract erosion values
    print(f"Extracting erosion values for {len(df)} {model_type} records...")
    df = extract_erosion_buffer_values_postgis(df)
    if 'erosion_buffer_m' in df.columns:
        df['erosion_value'] = df['erosion_buffer_m']

    print("Length-----------------> ", len(df))
    
    # Apply classifications only for valid values
    df['flood_class'] = df['flood_depth_m'].apply(lambda x: _classify_flood(x) if pd.notna(x) and x > 0 else None)
    df['erosion_class'] = df['erosion_value'].apply(lambda x: _classify_erosion_buffer(x) if pd.notna(x) and x != '' else None)
    
    # Update records in database
    updated_count = 0
    for _, row in df.iterrows():
        try:
            record = queryset.get(id=row['id'])
            changed = False
            
            # Always update flood_depth_m (including None values)
            flood_value = row.get('flood_depth_m')
            if pd.notna(flood_value):
                record.flood_depth_m = float(flood_value)
                changed = True
                if model_type == 'household' and hasattr(record, 'flood_depth_from_survey_meter'):
                    record.flood_depth_from_survey_meter = float(flood_value)
            else:
                record.flood_depth_m = None
                changed = True
                if model_type == 'household' and hasattr(record, 'flood_depth_from_survey_meter'):
                    record.flood_depth_from_survey_meter = None
            
            # Update flood_class
            if hasattr(record, 'flood_class'):
                record.flood_class = row.get('flood_class')
                changed = True
            
            # Always update erosion_value (including None values)
            erosion_value = row.get('erosion_value')
            if pd.notna(erosion_value):
                record.erosion_value = str(erosion_value)
                changed = True
            else:
                record.erosion_value = None
                changed = True
            
            # Update erosion_class
            if hasattr(record, 'erosion_class'):
                record.erosion_class = row.get('erosion_class')
                changed = True
            
            if changed:
                record.save()
                updated_count += 1
            
        except Exception as e:
            print(f"Error updating {model_type} record {row['id']}: {e}")
            continue
    
    print(f"✅ Updated {updated_count}/{len(df)} {model_type} records with flood depth and erosion data")


def run_gis_risk_assessment_pipeline(village_obj, village_code):
    """Run complete GIS risk assessment pipeline for all activities"""
    from layers.models import village_flood_raster_Files, district_wind_raster_file, district_eq_raster_file
    from vdmp_progress.risk_assessment_pipeline import run_risk_assessment_pipeline
    from vdmp_dashboard.models import HouseholdSurvey, Commercial, Critical_Facility, Transformer, ElectricPole
    
    # Validate data availability first
    validation_errors, validation_warnings = validate_gis_data_availability(village_obj)

    # Log warnings but continue
    for warning in validation_warnings:
        print(f"⚠️ GIS warning: {warning}")

    # Stop ONLY on real errors
    if validation_errors:
        raise ValueError(
            "Missing required data: " + "; ".join(validation_errors)
        )
        
    # Get raster file paths
    flood_raster = village_flood_raster_Files.objects.filter(village=village_obj).first()
    district = village_obj.gram_panchayat.circle.district
    wind_raster = district_wind_raster_file.objects.filter(district=district).first()
    eq_raster = district_eq_raster_file.objects.filter(district=district).first()
    
    flood_raster_path = os.path.join(settings.MEDIA_ROOT, flood_raster.raster_file.name)
    wind_raster_path = os.path.join(settings.MEDIA_ROOT, wind_raster.raster_file.name) if wind_raster else os.path.join(settings.MEDIA_ROOT, "pipeline_data", "wind_raster", "Wind.tif")
    eq_raster_path = os.path.join(settings.MEDIA_ROOT, eq_raster.raster_file.name) if eq_raster else os.path.join(settings.MEDIA_ROOT, "pipeline_data", "eq_raster", "eq.tif")
    
    village_id = village_obj.id
    
    # Step 1: Process all models to extract flood depth and erosion values
    print("🌊 Step 1: Extracting flood depth and erosion values for all models...")
    
    # Process HouseholdSurvey
    household_records = HouseholdSurvey.objects.filter(village=village_obj)
    if household_records.exists():
        print(f"Processing {household_records.count()} household records...")
        _process_model_flood_erosion(household_records, village_id, 'household')
    
    print(f"Processing {household_records.count()} household records...")

    print("-------------------- Commercial Records --------------------")
    # Process Commercial
    commercial_records = Commercial.objects.filter(village=village_obj)
    if commercial_records.exists():
        print(f"Processing {commercial_records.count()} commercial records...")
        _process_model_flood_erosion(commercial_records, village_id, 'commercial')
    
    print("-------------------- Critical_Facility --------------------")
    # Process Critical_Facility
    critical_records = Critical_Facility.objects.filter(village=village_obj)
    if critical_records.exists():
        print(f"Processing {critical_records.count()} critical facility records...")
        _process_model_flood_erosion(critical_records, village_id, 'critical')
    
    # Process Transformer
    transformer_records = Transformer.objects.filter(village=village_obj)
    if transformer_records.exists():
        print(f"Processing {transformer_records.count()} transformer records...")
        _process_model_flood_erosion(transformer_records, village_id, 'transformer')
    
    # Process ElectricPole
    electric_pole_records = ElectricPole.objects.filter(village=village_obj)
    if electric_pole_records.exists():
        print(f"Processing {electric_pole_records.count()} electric pole records...")
        _process_model_flood_erosion(electric_pole_records, village_id, 'electric_pole')
    
    # Step 2: Run risk assessment pipelines
    print("🏠 Step 2: Running household risk assessment pipeline...")
    try:
        run_risk_assessment_pipeline(village_id, 'household')
    except Exception as e:
        print(f"Household processing failed: {e}")
    
    print("🏢 Step 3: Running commercial risk assessment pipeline...")
    try:
        run_risk_assessment_pipeline(village_id, 'commercial')
    except Exception as e:
        print(f"Commercial processing failed: {e}")
    
    print("🏥 Step 4: Running critical facilities risk assessment pipeline...")
    try:
        run_risk_assessment_pipeline(village_id, 'critical')
    except Exception as e:
        print(f"Critical facilities processing failed: {e}")
    
    # Step 3: Process road assessments
    print("🛣️ Step 5: Processing road risk assessments...")
    # Process road flood analysis
    process_road_flood_zonal_length(village_obj, village_code, flood_raster_path)
    
   
    
    #Process road erosion analysis
    try:
        import psycopg2
        conn = psycopg2.connect(**_get_db_config())
        
        district_name, district_code = get_district_from_village(village_obj)
        _process_road_erosion_data(
            conn, village_obj, village_code, district_code,
            district_name, village_obj.name
        )
        conn.close()
    except Exception as e:
        print(f"Road erosion processing failed: {e}")
    
    # Step 5: Process agriculture assessments
    print("🌾 Step 6: Processing agriculture risk assessments...")
    try:
        district_name, district_code = get_district_from_village(village_obj)
        process_all_agriculture_hazards(
            village_obj.id, village_code, district_name, 
            district_code, village_obj.name
        )
    except Exception as e:
        print(f"Agriculture processing failed: {e}")
    
    print(f"✅ GIS risk assessment pipeline completed for village {village_obj.name}")


def get_household_data_for_village(village_code):
    """Get household data for a specific village - Updated for new pipeline"""
    from vdmp_dashboard.models import HouseholdSurvey
    import pandas as pd
    
    try:
        village = tblVillage.objects.get(code=village_code)
        household_data = HouseholdSurvey.objects.filter(village=village).values(
            'id', 'latitude', 'longitude', 'wall_type', 'roof_type', 'floor_type',
            'building_area_sqft', 'point_id', 'flood_depth_m', 'flood_class', 
            'erosion_value', 'erosion_class'
        )
        return pd.DataFrame(household_data)
    except Exception as e:
        print(f"Error getting household data: {e}")
        return pd.DataFrame()





# 


def save_household_results(household_df, village_obj, village_code):
    """Save household risk assessment results to database - DEPRECATED
    
    This function is now deprecated as we update records directly in _process_model_flood_erosion.
    Keeping for backward compatibility.
    """
    print("⚠️ save_household_results is deprecated - records are now updated directly")
    pass

def _classify_erosion(vulnerable):
    """Classify erosion vulnerability"""
    if pd.isna(vulnerable): return "No"
    vulnerable_str = str(vulnerable).strip().lower()
    if vulnerable_str in ["yes", "y", "1", "true"]:
        return "Yes"
    else:
        return "No"
def _classify_toilet_type(wall, roof, sanitation_facility):
    """Classify toilet type based on wall, roof materials and sanitation facility"""
    if pd.isna(sanitation_facility) or str(sanitation_facility).strip().lower() != 'own':
        return None
    
    wall_map = {
        "brick": "brick",
        "brick with cement": "brick",
        "brick without cement": "brick",
        "concrete": "brick"
    }
    roof_map = {
        "brick": "brick",
        "concrete": "brick",
        "tin": "tin"
    }
    
    w = str(wall).strip().lower()
    r = str(roof).strip().lower()
    
    w_norm = next((v for k, v in wall_map.items() if k in w), None)
    r_norm = next((v for k, v in roof_map.items() if k in r), None)
    
    if w_norm == "brick" and r_norm == "brick":
        return "Pucca"
    elif w_norm == "brick" and r_norm == "tin":
        return "Semi Pucca"
    else:
        return "Kachcha"
    

def _classify_crops_diversity(num_crops):
    """Classify crops diversity"""
    if pd.isna(num_crops): return "No crops"
    try:
        num_crops = int(float(num_crops))
        if num_crops <= 0: return "No crops"
        elif num_crops == 1: return "Single crop"
        elif num_crops <= 3: return "Low diversity"
        elif num_crops <= 5: return "Medium diversity"
        else: return "High diversity"
    except (ValueError, TypeError):
        return "No crops"




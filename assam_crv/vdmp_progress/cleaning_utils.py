import pandas as pd
import re
import logging
from sklearn.neighbors import NearestNeighbors

from osgeo import gdal, osr
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from vdmp_dashboard.models import HouseholdSurvey
from layers.models import village_flood_raster_Files
from village_profile.models import tblVillage
import math
import psycopg2
from village_profile.models import tblVillage

def extract_flood_depth_from_raster(df, village_id):
    """
    SAFE flood depth extraction from raster (EPSG:4326)
    - Uses inverse geotransform
    - Checks raster extent
    - Skips invalid / outside points
    """

  

    print("---- Extracting flood depth from raster ----")

    raster_file = village_flood_raster_Files.objects.filter(
        village_id=village_id
    ).first()

    if not raster_file or not raster_file.raster_file:
        return df

    raster_path = f"c:\\assamcrv\\assam_crv\\media\\{raster_file.raster_file}"
    ds = gdal.Open(raster_path)

    if not ds:
        return df

    band = ds.GetRasterBand(1)
    gt = ds.GetGeoTransform()
    nodata = band.GetNoDataValue()

    inv_gt = gdal.InvGeoTransform(gt)
    if inv_gt is None:
        return df

    # Raster extent (lon/lat)
    minx = gt[0]
    maxy = gt[3]
    maxx = minx + gt[1] * ds.RasterXSize
    miny = maxy + gt[5] * ds.RasterYSize

    flood_values = []

    for _, row in df.iterrows():
        try:
            lat = safe_float(row["latitude"])
            lon = safe_float(row["longitude"])

            if lat is None or lon is None:
                flood_values.append(0.0)
                continue

            # 🔒 EXTENT CHECK (CRITICAL)
            if not (minx <= lon <= maxx and miny <= lat <= maxy):
                flood_values.append(0.0)
                continue

            px, py = gdal.ApplyGeoTransform(inv_gt, lon, lat)
            px, py = int(px), int(py)

            if (
                px < 0 or py < 0 or
                px >= ds.RasterXSize or
                py >= ds.RasterYSize
            ):
                flood_values.append(0.0)
                continue

            val = band.ReadAsArray(px, py, 1, 1)[0, 0]

            if val is None or (isinstance(val, float) and math.isnan(val)):
                flood_values.append(0.0)
            elif nodata is not None and val == nodata:
                flood_values.append(0.0)
            else:
                flood_values.append(round(float(val), 3))

        except Exception:
            flood_values.append(0.0)

    df["flood_depth_m"] = flood_values
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

    geojson_path = (
        r"c:\assamcrv\assam_crv\media\pipeline_data"
        r"\river_buff_shp_file\new_river_buff.geojson"
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


def extract_erosion_buffer_values_postgis(
    df,
    buffer_table="public.new_river_buff",
    db_name="crv_assam",
    db_user="postgres",
    db_password="admin",
    db_host="localhost",
    db_port="5434",
):
    """
    SAFE erosion extraction using PostGIS
    - Skips invalid coordinates
    - NEVER crashes on bad data
    """

    import psycopg2

    df["latitude_f"] = df["latitude"].apply(safe_float)
    df["longitude_f"] = df["longitude"].apply(safe_float)
    df["erosion_buffer_m"] = None
    df["erosion_value"] = None

    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )

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
            ST_Transform(geom, 32646)
        );
    """

    with conn.cursor() as cur:
        for idx, row in df.iterrows():

            lat = row["latitude_f"]
            lon = row["longitude_f"]

            # 🔒 HARD SAFETY CHECK (THIS FIXES EVERYTHING)
            if (
                lat is None or lon is None or
                lat < -90 or lat > 90 or
                lon < -180 or lon > 180
            ):
                continue

            try:
                cur.execute(sql, (lon, lat))
                result = cur.fetchone()[0]
            except Exception:
                # 🔕 SILENT SKIP — DO NOT CRASH PIPELINE
                continue

            if result is not None:
                val = str(int(result))
                df.at[idx, "erosion_buffer_m"] = val
                df.at[idx, "erosion_value"] = val

    conn.close()
    return df


def process_road_data_pipeline(
    village_id,
    village_code,
    district_code,
    district_name,
    village_name,
    db_name="crv_assam",
    db_user="postgres",
    db_password="admin",
    db_host="localhost",
    db_port="5434",
):
   
  

    print(f"🛣️ Processing roads for village: {village_name}")

    village_obj = tblVillage.objects.get(id=village_id)

    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )

 

    # Flood / EQ / Wind (combined in one function)
    print("🌊 Processing flood, earthquake, and wind hazards...")
    _process_road_flood_data(
        conn,
        village_obj,
        village_code,
        district_code,
        district_name,
        village_name,
    )

    # # ✅ Erosion (vector only)
    # print("🌊 Processing erosion hazard...")
    # _process_road_erosion_data(
    #     conn,
    #     village_obj,
    #     village_code,
    #     district_code,
    #     district_name,
    #     village_name,
    # )

    conn.close()
    print("✅ Road processing completed")




def get_road_unit_cost(asset_typology):
    from vdmp_dashboard.models import RoadUnitCost
    rec = RoadUnitCost.objects.filter(
        asset_typology__iexact=asset_typology
    ).first()
    return float(rec.unit_cost) if rec and rec.unit_cost else 0.0




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


def raster_to_grid_gdf(
    raster_path,
    export_geojson=True,
    geojson_name="flood_grid_debug.geojson"
):
    """
    Convert raster pixels into vector grid polygons.
    Each polygon represents ONE raster pixel.

    Optionally exports the grid as GeoJSON
    to assam_crv/media for visual verification.
    """

    # --------------------------------------------------
    # 1. Open raster
    # --------------------------------------------------
    ds = gdal.Open(raster_path)
    if not ds:
        raise RuntimeError("Cannot open raster")

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
        media_dir = r"c:\assamcrv\assam_crv\media"
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
import geopandas as gpd
from sqlalchemy import create_engine
from django.conf import settings
def get_sqlalchemy_engine():
    """
    Create SQLAlchemy engine using Django DB settings.
    Keeps DB config in ONE place (env → settings.py).
    """

    db = settings.DATABASES["default"]

    engine_url = (
        f"postgresql+psycopg2://"
        f"{db['USER']}:{db['PASSWORD']}@"
        f"{db['HOST']}:{db['PORT']}/"
        f"{db['NAME']}"
    )

    return create_engine(engine_url)


def load_village_roads(village_code):
    """
    Load all road geometries and related attributes
    for a given village from PostGIS.

    Geometry CRS: EPSG:4326
    Length calculation will be done later in EPSG:32646
    """

    engine = get_sqlalchemy_engine()

    sql = """
    SELECT
        gid,
        geom,
        rd_surface,
        rsur_type,
        rsurtypeid,
        width,
        length
    FROM public.road_network
    WHERE vill_id = %s
      AND geom IS NOT NULL;
    """

    roads_gdf = gpd.read_postgis(
        sql,
        engine,
        params=(village_code,),
        geom_col="geom",
        crs="EPSG:4326"
    )

    # Safety check
    if roads_gdf.empty:
        print(f"⚠️ No roads found for village_code={village_code}")

    return roads_gdf


# Lengths in meters are only valid in projected CRS
def reproject_for_length(roads_gdf, grid_gdf):
    """
    Reproject both roads and grid to EPSG:32646
    so that length is measured in meters.
    """
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
    return intersections

# If multiple road pieces fall in the same pixel:
def aggregate_by_grid(intersections):
    """
    Aggregate total road length per raster pixel.
    """

    result = (
        intersections
        .groupby(["grid_id", "flood_depth_m"])["road_length_m"]
        .sum()
        .reset_index()
    )

    return result


def save_grid_results(result_df, village_obj, village_code):
    from vdmp_dashboard.models import VillageRoadInfo

    records = []

    for _, row in result_df.iterrows():
        records.append(
            VillageRoadInfo(
                village=village_obj,
                village_code=village_code,
                # grid_id=int(row["grid_id"]),
                flood_depth_m=float(row["flood_depth_m"]),
                road_length_m=float(row["road_length_m"]),
            )
        )

    if records:
        VillageRoadInfo.objects.bulk_create(
            records,
            batch_size=1000
        )




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
    grid_gdf = raster_to_grid_gdf(flood_raster_path)

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

    # 5. Length calculation
    intersections = calculate_road_length(intersections)

    # 6. Aggregate
    result = aggregate_by_grid(intersections)

    # 7. Save
    save_grid_results(result, village_obj, village_code)



def _process_road_flood_data(
    conn,
    village_obj,
    village_code,
    district_code,
    district_name,
    village_name,
):
    from vdmp_dashboard.models import VillageRoadInfo
    from layers.models import village_flood_raster_Files
    from shapely import wkt

    # ------------------------------------------------------------------
    # Load rasters ONCE
    # ------------------------------------------------------------------
    flood_raster = village_flood_raster_Files.objects.filter(
        village_id=village_obj.id
    ).first()

    if not flood_raster:
        return

    print("🌊 Processing flood hazard zonal length...")
    process_road_flood_zonal_length(
        village_obj,
        village_code,
       f"c:\\assamcrv\\assam_crv\\media\\{flood_raster.raster_file}"
    )

    # eq_sampler = RasterSampler(
    #     r"c:\assamcrv\assam_crv\static\risk_assessment_raster\PGA_Raster.img"
    # )

    # wind_sampler = RasterSampler(
    #     r"c:\assamcrv\assam_crv\static\risk_assessment_raster\Wind_Raster.tif"
    # )

    # # ------------------------------------------------------------------
    # # SQL: WHOLE ROAD, LENGTH IN UTM, POINT IN WGS84
    # # ------------------------------------------------------------------
    # sql = """
    # SELECT
    #     gid,
    #     rd_surface,
    #     rsur_type,
    #     rsurtypeid,
    #     width,

    #     ST_Length(
    #         ST_Transform(geom, 32646)
    #     ) AS road_len_m,

    #     ST_AsText(
    #         ST_Centroid(geom)
    #     ) AS centroid_wkt

    # FROM public.road_network
    # WHERE vill_id = %s
    #   AND geom IS NOT NULL;
    # """

    # with conn.cursor() as cur:
    #     cur.execute(sql, (village_code,))
    #     rows = cur.fetchall()

    # records = []

    # for (
    #     gid,
    #     surface,
    #     rsur,
    #     rsurtypeid,
    #     width,
    #     road_len,
    #     centroid_wkt,
    # ) in rows:

    #     if not centroid_wkt or road_len <= 0:
    #         continue

    #     pt = wkt.loads(centroid_wkt)
    #     lon, lat = pt.x, pt.y

    #     flood = flood_sampler.sample(lon, lat)
    #     eq = eq_sampler.sample(lon, lat)
    #     wind = wind_sampler.sample(lon, lat)

    #     asset_typology = rsur or surface or "Unknown"

    #     unit_cost = get_road_unit_cost(asset_typology)
    #     replacement_cost = road_len * unit_cost

    #     flood_mdr = get_mdr_value(flood, "flood", rsurtypeid)
    #     eq_mdr = get_mdr_value(eq, "eq", rsurtypeid)
    #     wind_mdr = get_mdr_value(wind, "wind", rsurtypeid)

    #     records.append(
    #         VillageRoadInfo(
    #             village=village_obj,
    #             district_name=district_name,
    #             district_code=district_code,
    #             village_name=village_name,
    #             village_code=village_code,
    #             latitude=str(lat),
    #             longitude=str(lon),
    #             road_surface_type=asset_typology,
    #             road_length_m=road_len,
    #             flood_depth_m=flood,
    #             unit_cost=unit_cost,
    #             replacement_cost_inr=replacement_cost,
    #             flood_hazard_mdr=flood_mdr,
    #             eq_hazard_mdr=eq_mdr,
    #             wind_hazard_mdr=wind_mdr,
    #             flood_loss=replacement_cost * flood_mdr,
    #             eq_loss=replacement_cost * eq_mdr,
    #             wind_loss=replacement_cost * wind_mdr,
    #         )
    #     )

    # if records:
    #     VillageRoadInfo.objects.bulk_create(records, batch_size=1000)








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
    - One record per road (grouped)
    """

    from vdmp_dashboard.models import VillageRoadInfoErosion

    sql = """
    WITH road_utm AS (
        SELECT
            gid,
            rd_surface,
            rsur_type,
            ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
        FROM public.road_network
        WHERE vill_id = %s
    ),

    buffer_utm AS (
        SELECT
            "BUFF_DIST" AS buffer_distance,
            ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
        FROM public.new_river_buff
    ),

    road_buffer_intersections AS (
        SELECT
            r.gid,
            r.rd_surface,
            r.rsur_type,
            b.buffer_distance,
            ST_Intersection(r.geom_utm, b.geom_utm) AS intersection_geom
        FROM road_utm r
        JOIN buffer_utm b
          ON ST_Intersects(r.geom_utm, b.geom_utm)
    ),

    erosion_summary AS (
        SELECT
            gid,
            rd_surface,
            rsur_type,
            MIN(buffer_distance) AS min_buffer_distance,
            SUM(ST_Length(intersection_geom)) AS total_length,
            ST_Centroid(ST_Collect(intersection_geom)) AS centroid_geom
        FROM road_buffer_intersections
        WHERE intersection_geom IS NOT NULL
          AND NOT ST_IsEmpty(intersection_geom)
        GROUP BY gid, rd_surface, rsur_type
    )

    SELECT
        gid,
        rd_surface,
        rsur_type,
        min_buffer_distance,
        total_length,
        ST_Y(ST_Transform(centroid_geom, 4326)) AS lat,
        ST_X(ST_Transform(centroid_geom, 4326)) AS lon
    FROM erosion_summary;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (village_code,))
        rows = cur.fetchall()

    records = []

    for gid, surf, rsur, buff_dist, length, lat, lon in rows:
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
        child_df = extract_flood_depth_from_raster(child_df)
    
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
    if 'amount_spent_for_agriculture_livestock' in df.columns:
        df['loss_agricultire_livelihood'] = df['amount_spent_for_agriculture_livestock'].apply(_classify_cost)
        logger.debug("Applied agriculture livelihood loss classification")
    
    if "amount_spent_for_agriculture_livestock_every_year" in df.columns:
        df["loss_AgriLivli"] = df["amount_spent_for_agriculture_livestock_every_year"].apply(_classify_cost)
        logger.debug("Applied Loss_AgriLivli classification")
    elif "amount_spent_for_agriculture_livestock" in df.columns:
        df["loss_AgriLivli"] = df["amount_spent_for_agriculture_livestock"].apply(_classify_cost)
        logger.debug("Applied Loss_AgriLivli classification from amount_spent_for_agriculture_livestock")
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
    """Classify erosion based on buffer distance"""
    if pd.isna(buffer_value) or buffer_value is None:
        return "Low"
    print("------------ erosion value ---------------- >",buffer_value)
    try:
        buffer_value = int(buffer_value)
        if buffer_value == 50:
            return "Seviere"
        elif buffer_value == 100:
            return "High"
        elif buffer_value == 150:
            return "medium"
        else:
            return "Low"
    except (ValueError, TypeError):
        return "Low"

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



def _process_road_eq_data(
    conn, village_obj, village_code,
    district_code, district_name, village_name
):
    """Process earthquake hazard for roads with 1500m segmentation"""
    from vdmp_dashboard.models import VillageRoadInfoEQ
    from osgeo import gdal
    from shapely import wkt
    import math

    # EQ raster pixel size ~1538m, use 1500m segments
    sql = """
    WITH road_utm AS (
        SELECT
            gid, rd_surface, rsur_type, rsurtypeid, width,
            ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
        FROM public.road_network
        WHERE vill_id = %s
    ),
    road_segments AS (
        SELECT
            gid, rd_surface, rsur_type, rsurtypeid, width,
            ST_LineSubstring(
                geom_utm,
                LEAST(gs / ST_Length(geom_utm), 1),
                LEAST((gs + 1500) / ST_Length(geom_utm), 1)
            ) AS segment_geom_utm
        FROM road_utm
        CROSS JOIN LATERAL generate_series(0, ST_Length(geom_utm)::int, 1500) AS gs
    )
    SELECT
        gid, rd_surface, rsur_type, rsurtypeid, width,
        ST_Length(segment_geom_utm) AS seg_len,
        ST_AsText(ST_Transform(ST_Centroid(segment_geom_utm), 4326)) AS p_center
    FROM road_segments
    WHERE ST_Length(segment_geom_utm) > 0;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (village_code,))
        rows = cur.fetchall()

    records = []
    for gid, surface, rsur, rsurtypeid, width, seg_len, p_center in rows:
        if not p_center:
            continue
            
        pt = wkt.loads(p_center)
        lon, lat = pt.x, pt.y
        
        eq_hazard = extract_eq_hazard_from_raster(lat, lon)
        asset_typology = rsur or surface or "Unknown"
        unit_cost = get_road_unit_cost_by_id(rsurtypeid) if rsurtypeid else get_road_unit_cost(asset_typology)
        replacement_cost = seg_len * unit_cost
        eq_mdr = get_mdr_value(eq_hazard, 'eq', rsurtypeid) if rsurtypeid else 0.0
        eq_loss = replacement_cost * eq_mdr

        records.append(
            VillageRoadInfoEQ(
                village=village_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_name,
                village_code=village_code,
                latitude=str(lat),
                longitude=str(lon),
                road_surface_type=asset_typology,
                road_constructed_by="Unknown",
                road_length_m=seg_len,
                road_width_m=width,
                road_type_id=rsurtypeid,
                unit_cost=unit_cost,
                replacement_cost_inr=replacement_cost,
                eq_hazard=eq_hazard,
                eq_hazard_mdr=eq_mdr,
                eq_loss=eq_loss,
            )
        )

    if records:
        VillageRoadInfoEQ.objects.bulk_create(records, batch_size=1000)

def _process_road_wind_data(
    conn, village_obj, village_code,
    district_code, district_name, village_name
):
    """Process wind hazard for roads with 90m segmentation"""
    from vdmp_dashboard.models import VillageRoadInfoWind
    from osgeo import gdal
    from shapely import wkt
    import math

    # Wind raster pixel size ~90m, use 90m segments
    sql = """
    WITH road_utm AS (
        SELECT
            gid, rd_surface, rsur_type, rsurtypeid, width,
            ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
        FROM public.road_network
        WHERE vill_id = %s
    ),
    road_segments AS (
        SELECT
            gid, rd_surface, rsur_type, rsurtypeid, width,
            ST_LineSubstring(
                geom_utm,
                LEAST(gs / ST_Length(geom_utm), 1),
                LEAST((gs + 90) / ST_Length(geom_utm), 1)
            ) AS segment_geom_utm
        FROM road_utm
        CROSS JOIN LATERAL generate_series(0, ST_Length(geom_utm)::int, 90) AS gs
    )
    SELECT
        gid, rd_surface, rsur_type, rsurtypeid, width,
        ST_Length(segment_geom_utm) AS seg_len,
        ST_AsText(ST_Transform(ST_Centroid(segment_geom_utm), 4326)) AS p_center
    FROM road_segments
    WHERE ST_Length(segment_geom_utm) > 0;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (village_code,))
        rows = cur.fetchall()

    records = []
    for gid, surface, rsur, rsurtypeid, width, seg_len, p_center in rows:
        if not p_center:
            continue
            
        pt = wkt.loads(p_center)
        lon, lat = pt.x, pt.y
        
        wind_hazard = extract_wind_hazard_from_raster(lat, lon)
        asset_typology = rsur or surface or "Unknown"
        unit_cost = get_road_unit_cost_by_id(rsurtypeid) if rsurtypeid else get_road_unit_cost(asset_typology)
        replacement_cost = seg_len * unit_cost
        wind_mdr = get_mdr_value(wind_hazard, 'wind', rsurtypeid) if rsurtypeid else 0.0
        wind_loss = replacement_cost * wind_mdr

        records.append(
            VillageRoadInfoWind(
                village=village_obj,
                district_name=district_name,
                district_code=district_code,
                village_name=village_name,
                village_code=village_code,
                latitude=str(lat),
                longitude=str(lon),
                road_surface_type=asset_typology,
                road_constructed_by="Unknown",
                road_length_m=seg_len,
                road_width_m=width,
                road_type_id=rsurtypeid,
                unit_cost=unit_cost,
                replacement_cost_inr=replacement_cost,
                wind_hazard=wind_hazard,
                wind_hazard_mdr=wind_mdr,
                wind_loss=wind_loss,
            )
        )

    if records:
        VillageRoadInfoWind.objects.bulk_create(records, batch_size=1000)
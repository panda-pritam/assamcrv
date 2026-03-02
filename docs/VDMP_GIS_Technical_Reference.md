# 🌊 VDMP GIS Pipeline — Technical Reference Document
> **Flood Damage & Erosion Risk Assessment System | Assam, India**

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Core GIS Concepts](#2-core-gis-concepts)
3. [Function Reference — Flood Pipeline](#3-function-reference--flood-pipeline)
4. [Point-Based Flood Extraction](#4-point-based-flood-extraction)
5. [Erosion Buffer Analysis](#5-erosion-buffer-analysis)
6. [Road Erosion SQL Analysis](#6-road-erosion-sql-analysis)
7. [End-to-End Flow Summary](#7-end-to-end-flow-summary)
8. [Quick Reference Cheat Sheet](#8-quick-reference-cheat-sheet)

---

## 1. System Overview

### What Does This System Do?

The VDMP GIS Pipeline is a geospatial disaster risk assessment system for villages in Assam, India.

Given a flood raster map and road/asset vector data, it computes for each village:
- Which roads and assets are flooded
- How deep the flood is at each location
- The financial cost of damage (in INR)
- Which assets fall inside river erosion buffer zones

### Big Picture Pipeline

```
                    VDMP GIS PIPELINE
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐
  │  FLOOD      │  │  EROSION     │  │  POINT-BASED   │
  │  ANALYSIS   │  │  BUFFER      │  │  EXTRACTION    │
  │  (Roads)    │  │  (Roads)     │  │  (Assets/Bldg) │
  └─────────────┘  └──────────────┘  └────────────────┘
        │                 │                  │
        ▼                 ▼                  ▼
  Raster → Grid     SQL Intersection    InvGeoTransform
  Overlay Roads      PostGIS CTE         Point → Pixel
        │                 │                  │
        └─────────────────┴──────────────────┘
                          │
                          ▼
             VillageRoadInfo (DB)
             VillageRoadInfoErosion (DB)
             flood_depth_m, flood_loss columns
```

### Key Technologies

| Tool | What It Does | Where Used |
|------|-------------|------------|
| **GDAL** | Opens rasters, clips, warps, reads pixel values | Raster clipping, pixel extraction |
| **GeoPandas** | Vector GeoDataFrames, spatial joins | Road overlay, grid creation |
| **PostGIS** | Spatial SQL in PostgreSQL | Road/buffer queries, erosion |
| **Shapely** | Geometry objects (Point, Polygon, Line) | Point-in-polygon, box creation |
| **psycopg2** | Raw PostgreSQL connection | Erosion buffer PostGIS queries |
| **SQLAlchemy** | ORM-style DB connection | Road/boundary GDF loading |
| **Django ORM** | Save results to application DB | `VillageRoadInfo` bulk_create |

---

## 2. Core GIS Concepts

### 2.1 Raster vs Vector

**Raster** — an image where every pixel has a numeric value (flood depth in metres). Like a spreadsheet laid over a map.

**Vector** — geometric shapes (points, lines, polygons) with attribute tables. Roads, buildings, village boundaries.

```
RASTER (flood depth pixels)         VECTOR (road lines)

┌──────┬──────┬──────┐
│ 0.0  │ 0.0  │ 0.0  │             ══════════════════════> Road A
├──────┼──────┼──────┤
│ 0.0  │ 2.5  │ 1.2  │    ══════════════════════> Road B
├──────┼──────┼──────┤
│ 0.0  │ 3.1  │ 2.5  │
└──────┴──────┴──────┘

Each cell = real area on ground      Each line = road geometry
Value = flood depth (metres)         Attributes = surface, width, cost
```

> **The Problem:** Roads are vector lines. Raster pixels are images. You can't directly do math between them. You need to convert raster pixels into vector polygons first — this is what `raster_to_grid_gdf()` does.

---

### 2.2 CRS — Coordinate Reference Systems

Two types of CRS are used. **Always check which one you are in before measuring anything!**

| CRS | Units | Good For |
|-----|-------|----------|
| **EPSG:4326** — WGS84 (Geographic) | Degrees of lat/lon | Storing and displaying data (GPS standard) |
| **EPSG:32646** — UTM Zone 46N (Projected) | Metres | Measuring real distance/area in Assam |

```
EPSG:4326 (degrees)            EPSG:32646 (meters)

lat=26.298, lon=91.502   →    X=245832m, Y=2908441m
                to_crs('EPSG:32646')

road.length = 0.0023  ❌         road.length = 234.5m  ✅
(meaningless degrees)            (real metres!)
```

> ⚠️ **Rule:** Store in 4326. Calculate length/area in 32646. Never mix them!

---

### 2.3 GeoTransform — The Bridge Between Pixels and Coordinates

A GeoTransform is a 6-number array that maps pixel positions ↔ real-world coordinates.

```
gt = (91.500,  0.001,  0,   26.300,  0,  -0.001)
      │        │       │    │         │    │
     gt[0]   gt[1]  gt[2]  gt[3]   gt[4] gt[5]

gt[0] = X of top-left corner (min longitude)   → 91.500°
gt[1] = Pixel width in degrees                 → 0.001° per pixel
gt[2] = Row rotation (always 0 for North-up)   → 0
gt[3] = Y of top-left corner (max latitude)    → 26.300°
gt[4] = Column rotation (always 0)             → 0
gt[5] = Pixel height (NEGATIVE — Y goes down)  → -0.001°
```

**Pixel → Coordinate (normal GeoTransform):**
```python
x = gt[0] + col * gt[1]
y = gt[3] + row * gt[5]
```

**Coordinate → Pixel (inverse GeoTransform):**
```python
inv_gt = gdal.InvGeoTransform(gt)
px, py = gdal.ApplyGeoTransform(inv_gt, lon, lat)
```

> ❓ **Why is `gt[5]` negative?** Row 0 is at the TOP (northernmost). Row numbers increase going DOWN (southward). But latitude increases going UP. So pixel height is negative to match this flip.

---

### 2.4 Spatial Intersection / Overlay

When a road line crosses multiple flood pixels, overlay cuts the road at each pixel boundary.

```
BEFORE overlay:
Road A = one long line from lon 91.500 → 91.503
Passes through grid cells 0, 1, 2

┌──────────┬──────────┬──────────┐
│          │          │          │
│  grid=0  │  grid=1  │  grid=2  │
│ flood=0m │flood=2.5m│ flood=0m │
│  ━━━━━━━━│━━━━━━━━━━│━━━━━━━━━ │
└──────────┴──────────┴──────────┘

AFTER overlay (gpd.overlay how='intersection'):
Row 1: grid=0, flood=0.0m,  road_length=100m, Paved
Row 2: grid=1, flood=2.5m,  road_length=150m, Paved  ← FLOODED!
Row 3: grid=2, flood=0.0m,  road_length=80m,  Paved

Each row inherits attributes from BOTH road AND grid!
```

---

## 3. Function Reference — Flood Pipeline

### 3.1 `load_village_boundary(village_code)`

**Purpose:** Fetch the polygon boundary of a village from PostGIS.

```python
def load_village_boundary(village_code):
    sql = """
    SELECT geom
    FROM public.village_boundary
    WHERE TRIM("Vill_ID") = %s;
    """
    gdf = gpd.read_postgis(sql, engine, params=(village_code,),
                           geom_col="geom", crs="EPSG:4326")
```

**SQL Explained:**

| SQL Part | Why It Exists |
|----------|--------------|
| `public.village_boundary` | Table in PostgreSQL public schema storing village polygons |
| `"Vill_ID"` | Double-quoted because column name has mixed case — PostgreSQL is case-sensitive |
| `TRIM(...)` | Removes accidental spaces in stored IDs like `'VG001  '` |
| `%s` | Parameterized placeholder — prevents SQL injection |
| `gpd.read_postgis()` | Like `pd.read_sql()` but understands geometry columns, returns GeoDataFrame |
| `crs='EPSG:4326'` | Tells GeoPandas the geometry is in lat/lon degrees |

---

### 3.2 `clip_raster_to_village(raster_path, village_gdf)`

**Purpose:** Crop the large flood raster (may cover all of Assam) down to just the village extent.

```
INPUT: Full Assam flood raster (large file)
       +  Village boundary GeoJSON (the 'cutline')
       ↓
gdal.Warp(
   clipped_raster,           ← OUTPUT path
   raster_path,              ← INPUT raster
   cutlineDSName=village,    ← clip boundary polygon
   cropToCutline=True,       ← physically crop to boundary
   dstNodata=0,              ← outside boundary = 0 (no flood)
   dstSRS='EPSG:4326',       ← keep lat/lon
   resampleAlg=NearestNeighbour,  ← do NOT average pixel values
   outputType=GDT_Float32    ← pixels store decimal values
)
       ↓
OUTPUT: Small raster clipped to village boundary only
```

**Why Each Flag Matters:**

| Flag | Explanation |
|------|-------------|
| `cropToCutline=True` | Without this, output is same size as input — just masked. With this, output is physically cropped. Much smaller file! |
| `dstNodata=0` | Pixels outside the village boundary get value 0 (no flood). Design choice: unknown = no flood. |
| `GRA_NearestNeighbour` | Do not interpolate/average. Flood depth classes (1m, 2m, 3m) must stay as whole values. Bilinear would create weird decimals like 1.73m. |
| `GDT_Float32` | Store pixel values as 32-bit floats — supports decimals like 2.75m flood depth. |

---

### 3.3 `raster_to_grid_gdf(raster_path, village_code)`

**Purpose:** Convert every raster pixel into a real vector polygon (rectangle) with flood depth as an attribute. Necessary because spatial overlay requires two vector datasets.

**Pixel to Polygon Conversion:**
```python
for row in range(rows):
    for col in range(cols):
        val = arr[row, col]           # flood depth value

        x_min = gt[0] + col * gt[1]  # left edge longitude
        x_max = x_min + gt[1]         # right edge
        y_max = gt[3] + row * gt[5]   # top edge (gt[5] negative!)
        y_min = y_max + gt[5]          # bottom edge

        polygons.append(box(x_min, y_min, x_max, y_max))
        values.append(float(val))
```

**Worked Example:**
```
GeoTransform: gt = (91.500, 0.001, 0, 26.300, 0, -0.001)

Row=0, Col=0:
  x_min = 91.500 + 0*0.001 = 91.500
  x_max = 91.500 + 0.001   = 91.501
  y_max = 26.300 + 0*-0.001= 26.300
  y_min = 26.300 + (-0.001)= 26.299
  → box(91.500, 26.299, 91.501, 26.300)  flood=0.0m

Row=2, Col=2:  (deeply flooded pixel)
  x_min = 91.502,  x_max = 91.503
  y_max = 26.298,  y_min = 26.297
  → box(91.502, 26.297, 91.503, 26.298)  flood=3.1m 🌊
```

**Result — `grid_gdf`:**

| grid_id | flood_depth_m | geometry |
|---------|--------------|----------|
| 0 | 0.0 | `POLYGON(91.500 26.299, 91.501 26.299 ...)` |
| 5 | 1.2 | `POLYGON(91.500 26.298, 91.501 26.298 ...)` |
| 6 | 3.1 | `POLYGON(91.501 26.298, 91.502 26.298 ...)` |
| 7 | 0.8 | `POLYGON(91.502 26.298, 91.503 26.298 ...)` |

---

### 3.4 `load_village_roads(village_code)`

**Purpose:** Load all road line geometries and attributes from PostGIS.

The function tries two SQL queries — **uppercase column names first** (QGIS import format), then **lowercase** (CLI import format). Defensive approach for inconsistent imports.

**SQL Column Meaning:**

| Column | Meaning |
|--------|---------|
| `rd_surface` | Road surface category (Paved, Unpaved, Gravel...) |
| `rsur_type` | Surface material detail (Bitumen, WBM, Earthen...) |
| `rsurtypeid / type_r` | Numeric ID of road type — used for MDR lookup |
| `width` | Road width in metres — used in replacement cost |
| `unit_cost / unitrpcost` | Cost per square metre in INR — from cost database |
| `geom IS NOT NULL` | Skip records with missing geometry (data entry errors) |
| `TRIM(vill_id)` | Remove spaces from stored village ID |

---

### 3.5 `reproject_for_length(roads_gdf, grid_gdf)`

**Purpose:** Convert both roads and grid from EPSG:4326 (degrees) to EPSG:32646 (metres).

```python
roads_utm = roads_gdf.to_crs("EPSG:32646")
grid_utm  = grid_gdf.to_crs("EPSG:32646")
```

```
BEFORE (degrees):  roads_gdf.geometry.length = 0.00234  ❌
AFTER  (metres):   roads_utm.geometry.length = 234.5m   ✅

Both layers must be in the SAME CRS before overlay!
EPSG:32646 = UTM Zone 46N = correct for Assam, India
```

---

### 3.6 `intersect_roads_with_grid(roads_utm, grid_utm)`

**Purpose:** The most critical spatial step — cut each road at every pixel boundary it crosses.

```python
intersections = gpd.overlay(roads_utm, grid_utm, how="intersection")
```

This is conceptually equivalent to:
```sql
SELECT r.*, g.grid_id, g.flood_depth_m
FROM roads r, grid g
WHERE ST_Intersects(r.geom, g.geom)
```

**Attributes each row gets:**

| Source | Columns |
|--------|---------|
| From roads layer | `rd_surface, rsur_type, rsurtypeid, width, unit_cost, id` |
| From grid layer | `grid_id, flood_depth_m` |
| Computed after | `road_length_m = geometry.length` (metres, since UTM) |

**Why Two Rows of Same Road in Same Pixel?**

```
Scenario 1 — Two different roads of same type in same pixel:
┌──────────────────────┐
│      Pixel 42        │
│  Road A ━━━━━━━━━━━  │  → 80m piece
│  Road B ━━━━━━━━━━━  │  → 120m piece  (parallel road!)
└──────────────────────┘

Scenario 2 — Curved road enters/exits same pixel twice:
┌──────────────────────┐
│      Pixel 42        │
│   ━━━━━━━┓           │  → 80m piece (entering)
│          ┃           │
│          ┗━━━━━━━    │  → 120m piece (re-entering)
└──────────────────────┘
```

That's exactly why aggregation is needed next!

---

### 3.7 `aggregate_by_grid_and_road(intersections)`

**Purpose:** Combine multiple road segments of the same type in the same pixel into one row.

```python
result = (
    intersections
    .groupby(
        ["grid_id", "flood_depth_m", "rd_surface",
         "rsur_type", "rsurtypeid", "width", "unit_cost"],
        as_index=False
    )
    .agg(road_length_m=("road_length_m", "sum"))
)
```

**SQL equivalent:**
```sql
SELECT grid_id, flood_depth_m, rd_surface, rsur_type,
       rsurtypeid, width, unit_cost,
       SUM(road_length_m) AS road_length_m
FROM intersections
GROUP BY grid_id, flood_depth_m, rd_surface,
         rsur_type, rsurtypeid, width, unit_cost;
```

**Before vs After:**

```
BEFORE (intersections):                   AFTER (result):

grid│flood│surface│length           grid│flood│surface│length
────┼─────┼───────┼──────           ────┼─────┼───────┼──────
 42 │ 2.5 │ Paved │  80m             42 │ 2.5 │ Paved │ 200m  ← merged!
 42 │ 2.5 │ Paved │ 120m             42 │ 2.5 │Gravel │  60m
 42 │ 2.5 │Gravel │  60m             43 │ 1.0 │ Paved │ 325m  ← merged!
 43 │ 1.0 │ Paved │ 200m
 43 │ 1.0 │ Paved │  50m
 43 │ 1.0 │ Paved │  75m
```

> ⚠️ **Why all road attributes are in GROUP BY?** Different road types (Paved vs Gravel) have different replacement costs. You must keep them separate — you cannot average costs across road types.

---

### 3.8 `save_grid_results(result_df, village_obj, village_code)`

**Purpose:** Calculate financial flood damage for each road segment and save to Django DB.

**Damage Calculation Formula:**

```
Step 1: Adjust depth (domain logic)
  adjusted_depth = raw_depth - 1.0
  flood_depth_m  = adjusted_depth if adjusted_depth > 0 else 0
  (First 1m of flood assumed to not cause structural damage)

Step 2: Replacement cost
  replacement_cost = road_length_m × unit_cost × road_width_m
  Example: 200m × ₹5,000/m² × 5m width = ₹50,00,000

Step 3: MDR (Mean Damage Ratio) lookup
  flood_mdr = get_road_flood_mdr(flood_depth_m, road_type_id)
  MDR range: 0.0 (no damage) → 1.0 (total loss)
  Example: 2m flood on paved road → MDR = 0.45

Step 4: Flood loss
  flood_loss = replacement_cost × flood_mdr
  Example: ₹50,00,000 × 0.45 = ₹22,50,000 damage
```

**What is MDR?**

> **Mean Damage Ratio (MDR)** is a number between 0.0 and 1.0 representing what fraction of an asset's value is typically destroyed at a given flood depth. Values come from the `roadFloodMDRMapping` table based on historical data. For example, a paved road flooded to 2 metres loses ~45% of its value → MDR = 0.45.

---

## 4. Point-Based Flood Extraction

### 4.1 `extract_flood_depth_from_raster(df, village_id)`

**Purpose:** For a DataFrame of assets (buildings etc.) with lat/lon coordinates, find the flood depth at each asset's exact location by reading the raster pixel that covers it.

**Core Concept — Inverse GeoTransform:**

```
Normal GeoTransform:    pixel(row=5, col=3)  →  lon=91.503, lat=26.295
Inverse GeoTransform:   lon=91.503, lat=26.295  →  pixel(col=3, row=5)

GDAL usage:
inv_gt = gdal.InvGeoTransform(gt)                  ← compute inverse
px, py = gdal.ApplyGeoTransform(inv_gt, lon, lat)  ← apply it
px, py = int(px), int(py)                          ← must be integers!

val = band.ReadAsArray(px, py, 1, 1)[0, 0]
     ReadAsArray(startX, startY, width=1, height=1)
     → returns 1×1 array, [0,0] gets the single value
```

**Safety Checks Flow:**

```
For each asset row in df:
│
├─ lat/lon is None or invalid string?  → append None, skip
│               ↑ handled by safe_float()
│
├─ Point outside raster extent?        → append None, skip
│  (minx <= lon <= maxx and miny <= lat <= maxy)
│
├─ Pixel index out of raster bounds?   → append None, skip
│  (px < 0 or py < 0 or px >= RasterXSize)
│
├─ Pixel value == NoData?              → append None, skip
│
├─ Pixel value is NaN?                 → append None, skip
│
└─ Valid value!                        → append flood_depth_m ✅
```

---

### 4.2 `safe_float(x)`

Critical utility that prevents a single bad coordinate from crashing the entire loop.

| Input | Output |
|-------|--------|
| `"26.5"` | `26.5` ✅ |
| `"  26.5  "` (spaces) | `26.5` ✅ (stripped) |
| `"NA"` or `"null"` or `"none"` | `None` ✅ |
| `""` (empty string) | `None` ✅ |
| `None` | `None` ✅ |
| `"abc"` (non-numeric) | `None` ✅ (exception caught) |
| `26.5` (already float) | `26.5` ✅ |

---

## 5. Erosion Buffer Analysis

### 5.1 What is River Erosion Buffer?

Rivers erode the land around them. GIS analysts draw concentric buffer zones at different distances from the river.

```
              100m  200m  500m
               ↓     ↓     ↓
──────────────────────────────────────────  ← 500m buffer
       ──────────────────────────────       ← 200m buffer
              ──────────────────            ← 100m buffer
                    🌊🌊🌊                  ← River
              ──────────────────            ← 100m buffer
       ──────────────────────────────       ← 200m buffer
──────────────────────────────────────────  ← 500m buffer

Asset at X: inside 100m, 200m, 500m zones
MIN(BUFF_DIST) = 100  ← most dangerous zone returned
```

**Why `MIN()`?** Buffers are nested — if you're in the 100m zone, you're also inside 200m and 500m. You want the **innermost** (most dangerous) one.

---

### 5.2 `extract_erosion_buffer_values()` — GeoJSON Version

**Purpose:** Loop-based point-in-polygon check using a GeoJSON file on disk.

| Step | What Happens |
|------|-------------|
| Load buffer GeoJSON | Read buffer polygons from file into GeoPandas GeoDataFrame |
| Create asset points | `gpd.points_from_xy(longitude, latitude)` → Point geometry per asset |
| Reproject both to UTM | Both points and buffers → EPSG:32646 for accurate intersection |
| Extent check | If points and buffers don't overlap geographically → silently return |
| Nested loop intersection | `pt.intersects(buff.geometry)` for each asset vs each buffer |
| MIN buffer distance | If point is in multiple buffers → take smallest (closest to river = highest risk) |

---

### 5.3 `extract_erosion_buffer_values_postgis()` — PostGIS Version

**Purpose:** Same erosion check but using PostGIS SQL. Much faster for large datasets.

**The SQL — Reading Inside Out:**

```sql
SELECT MIN("BUFF_DIST")
FROM public.riverbuffer
WHERE ST_Intersects(
    ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 32646),
    ST_Transform(ST_SetSRID(geom, 4326), 32646)
);
```

```
ST_MakePoint(lon, lat)           → create Point geometry (no CRS yet)
ST_SetSRID(..., 4326)            → assign WGS84 lat/lon CRS
ST_Transform(..., 32646)         → reproject to UTM metres

ST_SetSRID(geom, 4326)           → buffer geometry is in lat/lon
ST_Transform(..., 32646)         → reproject buffer to UTM metres

ST_Intersects(point, buffer)     → is asset inside any buffer polygon?

MIN('BUFF_DIST')                 → return smallest = most critical zone

⚠️ Both geometries must be in SAME CRS for ST_Intersects to work!
```

**`conn.rollback()` — Why It's Critical:**

```
WITHOUT rollback:                  WITH rollback:

Query 1 ✅                         Query 1 ✅
Query 2 ✅                         Query 2 ✅
Query 3 💥 FAILS                   Query 3 💥 FAILS
     ↓                                  ↓
Connection in ERROR state          conn.rollback()  ← cleans state
Query 4 ❌ aborted                      ↓
Query 5 ❌ aborted                 Query 4 ✅
All remaining rows FAIL!           Query 5 ✅  continues normally!
```

---

## 6. Road Erosion SQL Analysis

### 6.1 `_process_road_erosion_data()`

**Purpose:** For every road in a village, find how close it is to the river using a PostGIS CTE query — entirely inside the database, no Python loops needed.

**Overall Flow:**
```
village_code
     ↓
Delete old VillageRoadInfoErosion records
     ↓
Try SQL with UPPERCASE columns ("Vill_ID", "Rd_Surface"...)
     ↓ (if fails → conn.rollback())
Try SQL with lowercase columns (vill_id, rd_surface...)
     ↓
For each road row:
  → Build VillageRoadInfoErosion object
  → erosion_class = _classify_erosion_buffer(min_buffer_distance)
     ↓
bulk_create(records, batch_size=1000)
```

---

### 6.2 The CTE SQL — Block by Block

**What is a CTE?** `WITH block_name AS (...)` lets you write a complex query in named steps. Each block builds on the previous one.

#### CTE Block 1: `road_utm`

```sql
WITH road_utm AS (
    SELECT
        id,
        rd_surface,
        rsur_type,
        ST_Length(
            ST_Transform(ST_SetSRID(geom, 4326), 32646)
        ) AS road_length_m,
        ST_Centroid(
            ST_Transform(ST_SetSRID(geom, 4326), 32646)
        ) AS centroid_utm
    FROM public.road_network
    WHERE "Vill_ID" = %s
),
```

| SQL Part | What It Does |
|----------|-------------|
| `ST_SetSRID(geom, 4326)` | Tell PostGIS the geometry is in lat/lon |
| `ST_Transform(..., 32646)` | Reproject to UTM metres — **required** for `ST_Length` to return metres |
| `ST_Length(...)` | Calculate road length in metres (only correct in projected CRS) |
| `ST_Centroid(...)` | Find the centre point of the road line — used to check buffer membership |

> 💡 **Why centroid?** For flood, we need road length per pixel → intersect the full line. For erosion, we just want to classify the road as near/far from river → centroid is a simpler, faster representative point.

---

#### CTE Block 2: `buffer_utm`

```sql
buffer_utm AS (
    SELECT
        "BUFF_DIST" AS buffer_distance,
        ST_Transform(ST_SetSRID(geom, 4326), 32646) AS geom_utm
    FROM public.riverbuffer
),
```

Loads all river buffer polygons and reprojects to UTM metres to match the road centroids from Block 1.

---

#### CTE Block 3: `road_with_erosion`

```sql
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
    GROUP BY r.id, r.rd_surface, r.rsur_type,
             r.road_length_m, r.centroid_utm
)
```

| SQL Part | What It Does |
|----------|-------------|
| `LEFT JOIN` | Keep ALL roads — even those not inside any buffer. NULL = road is not near river. |
| `ON ST_Intersects(centroid, buffer)` | Join condition: road centroid falls inside buffer polygon |
| `MIN(buffer_distance)` | Road centroid inside 100m, 200m, 500m → return 100 (most critical) |
| `GROUP BY r.id ...` | One row per road feature — collapse multiple buffer matches into MIN |
| `ST_Y(ST_Transform(centroid, 4326))` | Convert centroid back to lat/lon → extract latitude (Y coordinate) |
| `ST_X(...)` | Extract longitude (X coordinate) |

> ⚠️ **`LEFT JOIN` vs `INNER JOIN`:**
> `LEFT JOIN` keeps roads NOT inside any buffer (NULL buffer_distance).
> `INNER JOIN` would silently drop all roads outside the buffer zone.
> Using `LEFT JOIN` ensures every road gets a record.

---

#### Full Query Visualised

```
public.road_network (village=VG001):
  Road A: Paved,   length=234m, centroid=(245832m, 2908441m) UTM
  Road B: Gravel,  length=156m, centroid=(245901m, 2908390m) UTM
  Road C: Earthen, length=89m,  centroid=(246100m, 2908600m) UTM

public.riverbuffer:
  Polygon 1: BUFF_DIST=100,  polygon covers river ±100m
  Polygon 2: BUFF_DIST=200,  polygon covers river ±200m
  Polygon 3: BUFF_DIST=500,  polygon covers river ±500m

ST_Intersects results:
  Road A centroid ∩ 100m buffer? YES → BUFF_DIST=100
  Road A centroid ∩ 200m buffer? YES → BUFF_DIST=200
  Road A centroid ∩ 500m buffer? YES → BUFF_DIST=500
  → MIN = 100  (extreme erosion risk) 🔴

  Road B centroid ∩ 100m buffer? NO
  Road B centroid ∩ 200m buffer? YES → BUFF_DIST=200
  Road B centroid ∩ 500m buffer? YES → BUFF_DIST=500
  → MIN = 200  (moderate erosion risk) 🟡

  Road C centroid ∩ any buffer?  NO
  → NULL  (no erosion risk) 🟢
```

---

### 6.3 Python Side — Building Records

```python
for id, surf, rsur, buff_dist, length, lat, lon in rows:
    records.append(
        VillageRoadInfoErosion(
            road_surface_type = rsur or surf,       # use rsur_type first, fallback to rd_surface
            road_length_m     = length,
            erosion_class     = _classify_erosion_buffer(buff_dist),
            latitude          = str(lat) if lat is not None else None,
            longitude         = str(lon) if lon is not None else None,
            ...
        )
    )
```

| Code | Why |
|------|-----|
| `rsur or surf` | Use `rsur_type` first (more specific). If None/empty, fall back to `rd_surface`. |
| `_classify_erosion_buffer(buff_dist)` | Converts 100/200/500/None → `'Extreme'/'High'/'Moderate'/'No Risk'` |
| `str(lat)` | Django model stores lat/lon as `CharField` — convert float to string |
| `bulk_create(batch_size=1000)` | Insert up to 1000 records per DB round-trip — much faster than one INSERT per row |

---

## 7. End-to-End Flow Summary

### 7.1 Flood Damage Pipeline

```
INPUT: village_code='VG001', flood_raster='assam_flood_2024.tif'

1. load_village_boundary('VG001')
   → Fetch village polygon from PostGIS
   → GeoDataFrame with 1 polygon, EPSG:4326

2. clip_raster_to_village(raster, village_gdf)
   → gdal.Warp() crops large raster to village extent
   → Small GeoTIFF with only village pixels

3. raster_to_grid_gdf(clipped_raster)
   → Loop: every pixel → box polygon
   → grid_gdf: 500 polygons each with flood_depth_m

4. load_village_roads('VG001')
   → Fetch road lines from PostGIS
   → roads_gdf: 45 road features

5. reproject_for_length(roads_gdf, grid_gdf)
   → Both → EPSG:32646 (UTM metres)

6. intersect_roads_with_grid(roads_utm, grid_utm)
   → gpd.overlay(how='intersection')
   → Road lines cut at pixel boundaries
   → 312 intersection segments

7. calculate_road_length(intersections)
   → Each segment.geometry.length → metres

8. aggregate_by_grid_and_road(intersections)
   → GROUP BY grid_id + road attributes
   → SUM(road_length_m)
   → 87 unique grid-road combinations

9. save_grid_results(result, village_obj, village_code)
   → replacement_cost = length × width × unit_cost
   → flood_mdr from roadFloodMDRMapping table
   → flood_loss = replacement_cost × flood_mdr
   → VillageRoadInfo.objects.bulk_create()

OUTPUT: 87 DB records with flood_loss in INR for each road segment
```

---

### 7.2 Erosion Risk Pipeline

```
Option A — Python-side (GeoJSON):
  1. Load buffer polygons from file
  2. Create Point geometry per asset
  3. Reproject both → EPSG:32646
  4. pt.intersects(buff.geometry) for each pair
  5. MIN(BUFF_DIST) per asset
  → Best for: small datasets, simple setup

Option B — PostGIS SQL per point (loop):
  1. For each asset: execute SQL with lon/lat
  2. PostGIS: ST_MakePoint → ST_SetSRID → ST_Transform → ST_Intersects
  3. MIN(BUFF_DIST) inside SQL
  4. conn.rollback() on any failure, continue to next
  → Best for: medium datasets, need per-row error handling

Option C — Road centroid SQL (batch, fastest):
  1. CTE query: road_utm + buffer_utm + LEFT JOIN
  2. ST_Centroid per road → check against all buffers
  3. GROUP BY road + MIN(buffer_distance)
  4. One query returns ALL roads at once
  5. bulk_create VillageRoadInfoErosion records
  → Best for: large datasets, batch road processing

OUTPUT: Each road classified as Extreme/High/Moderate/No Erosion Risk
```

---

## 8. Quick Reference Cheat Sheet

### 8.1 Key Concepts

| Concept | What It Means | Where Used |
|---------|--------------|-----------|
| **Raster** | Image grid where each pixel = a value (flood depth) | All flood functions |
| **Vector** | Point/Line/Polygon geometries with attributes | Roads, boundaries |
| **CRS** | Coordinate system — always check before measuring! | All functions |
| **EPSG:4326** | Lat/Lon degrees — for storage and display | PostGIS data storage |
| **EPSG:32646** | UTM metres, NE India — for length calculation | All reproject steps |
| **GeoTransform** | Maps pixel row/col ↔ real-world coordinates | All raster functions |
| **Inverse GT** | Converts lat/lon → pixel position | `extract_flood_depth` |
| **Overlay** | Cuts lines at polygon boundaries, merges attributes | `intersect_roads_with_grid` |
| **MDR** | Mean Damage Ratio 0–1, from flood depth lookup table | `save_grid_results` |
| **NoData** | "No information" — different from zero! | All raster functions |
| **CTE** | SQL `WITH` blocks — named steps in one query | `_process_road_erosion` |
| **LEFT JOIN** | Keep all rows even with no match (NULL result) | road erosion CTE |
| **ST_Intersects** | PostGIS: does geometry A overlap geometry B? | All erosion functions |
| **ST_Transform** | PostGIS: reproject geometry to different CRS | All erosion SQL |
| **ST_Centroid** | PostGIS: find the centre point of a geometry | Road erosion centroid |
| **conn.rollback()** | Reset PostgreSQL connection after a failed query | PostGIS loop functions |
| **bulk_create** | Django: insert many rows in one DB call | All save functions |

---

### 8.2 CRS Decision Guide

| Operation | Use This CRS |
|-----------|-------------|
| Store data in PostGIS | EPSG:4326 |
| Display on a map | EPSG:4326 |
| Calculate road/line length | EPSG:32646 |
| Calculate area of a polygon | EPSG:32646 |
| Spatial intersection / overlay | EPSG:32646 (both layers must match) |
| Read pixel from raster | EPSG:4326 (match the raster's CRS) |
| `ST_Length` in PostGIS | After `ST_Transform` to 32646 |

---

### 8.3 PostGIS Functions Used

| PostGIS Function | What It Does |
|-----------------|-------------|
| `ST_MakePoint(lon, lat)` | Create a Point geometry from coordinates |
| `ST_SetSRID(geom, 4326)` | Assign a CRS to a geometry (does NOT transform) |
| `ST_Transform(geom, 32646)` | Reproject geometry to a different CRS |
| `ST_Intersects(geom_a, geom_b)` | Returns TRUE if geometries overlap/touch |
| `ST_Length(geom)` | Length of a line in the geometry's CRS units |
| `ST_Centroid(geom)` | Returns the centre point of a geometry |
| `ST_X(point)` | Extract the X (longitude) coordinate from a point |
| `ST_Y(point)` | Extract the Y (latitude) coordinate from a point |
| `MIN(BUFF_DIST)` | Return smallest buffer distance (= closest to river) |

---

### 8.4 GeoJSON vs PostGIS Comparison

| | GeoJSON (Python loop) | PostGIS SQL |
|--|----------------------|-------------|
| Data source | File on disk | Database table |
| Speed | Slow (Python loops) | Fast (DB spatial index) |
| Memory | Loads all buffers into RAM | DB handles it |
| Best for | Small datasets | Large datasets |
| Crash safety | try/except per loop | rollback per row |
| Setup complexity | Simple | Needs PostGIS table |

---

*Document Version: 1.0 | System: VDMP GIS Pipeline | Coverage: Assam, India*

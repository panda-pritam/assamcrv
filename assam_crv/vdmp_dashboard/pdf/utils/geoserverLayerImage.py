"""
GeoServer Map Generation Utilities for Django Reports

This module provides functions to:
1. Fetch map images from GeoServer WMS
2. Auto-calculate optimal dimensions based on bbox aspect ratios
3. Cache calculations to improve performance
4. Generate ReportLab-compatible images for PDF reports

Main workflow:
- get_geoserver_image_as_rl_image() -> Primary function for getting map images
- Uses caching to avoid repeated bbox/dimension calculations
- Handles village-specific filtering via CQL_FILTER
"""

from PIL import Image
from io import BytesIO
import requests
import xml.etree.ElementTree as ET
from village_profile.models import tblVillage
from reportlab.platypus import Image as RLImage

# =============================================================================
# GLOBAL CACHE VARIABLES
# =============================================================================
_cached_bbox = {}           # Cache for village bbox calculations
_cached_layer_data = {}     # Cache for layer dimensions and bbox data

# =============================================================================
# BBOX VALIDATION AND MANIPULATION
# =============================================================================

def validate_bbox(bbox):
    """
    Validate that bbox string has proper format and non-zero area.
    
    Args:
        bbox (str): Comma-separated bbox "minx,miny,maxx,maxy"
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    try:
        minx, miny, maxx, maxy = map(float, bbox.split(","))
        
        if minx >= maxx or miny >= maxy:
            return False, f"Invalid bbox: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}"
        
        width = maxx - minx
        height = maxy - miny
        
        if width == 0 or height == 0:
            return False, f"Zero-area bbox: width={width}, height={height}"
            
        return True, "Valid bbox"
    except Exception as e:
        return False, f"Error parsing bbox: {e}"

def expand_bbox(bbox, padding_percent=0.1):
    """
    Expand bbox by given percentage to add padding around features.
    
    Args:
        bbox (str): Original bbox string
        padding_percent (float): Percentage to expand (0.1 = 10%)
        
    Returns:
        str: Expanded bbox string or original if expansion failed
    """
    print(f"Expanding bbox by {padding_percent*100}%")
    
    # Validate input bbox first
    is_valid, message = validate_bbox(bbox)
    if not is_valid:
        print(f"Cannot expand invalid bbox: {message}")
        return None
    
    minx, miny, maxx, maxy = map(float, bbox.split(","))
    width = maxx - minx
    height = maxy - miny

    pad_x = width * padding_percent
    pad_y = height * padding_percent

    new_bbox = (
        minx - pad_x,
        miny - pad_y,
        maxx + pad_x,
        maxy + pad_y
    )
    expanded = ",".join(map(str, new_bbox))
    
    # Validate expanded bbox
    is_valid, message = validate_bbox(expanded)
    if is_valid:
        print(f"Expanded bbox: {expanded}")
        return expanded
    else:
        print(f"Expanded bbox is invalid: {message}")
        return bbox  # Return original if expansion failed

def create_bbox_from_center(lat, lon, zoom_level=0.8):
    """
    Create a bounding box centered on given lat/lon coordinates.
    Used as fallback when layer-based bbox calculation fails.
    
    Args:
        lat (float): Latitude of center point
        lon (float): Longitude of center point
        zoom_level (float): Size of bbox (degrees)
        
    Returns:
        str: Bbox string "minx,miny,maxx,maxy"
    """
    print(f"Creating bbox from center: {lat}, {lon}")
    
    # Ensure minimum zoom level to prevent zero-area bbox
    if zoom_level <= 0:
        zoom_level = 0.01
        print(f"Warning: zoom_level was <= 0, using default: {zoom_level}")
    
    minx = lon - zoom_level
    miny = lat - zoom_level
    maxx = lon + zoom_level
    maxy = lat + zoom_level
    
    bbox = f"{minx},{miny},{maxx},{maxy}"
    print(f"Created bbox: {bbox}")
    return bbox

# =============================================================================
# GEOSERVER DATA FETCHING
# =============================================================================

def get_layer_bbox_from_wfs(layer_name, village_code, zoom_factor=0.5):
    """
    Get bbox for a specific village from a layer using WFS.
    This gives the most accurate bbox for village-filtered data.
    
    Args:
        layer_name (str): GeoServer layer name (e.g., 'assam:building_footprint')
        village_code (str): Village code for filtering
        zoom_factor (float): Zoom multiplier - higher values = tighter zoom
                           1.0 = original extent
                           2.0 = 2x zoom (4x smaller area)
                           3.0 = 3x zoom (9x smaller area)
        
    Returns:
        str or None: Bbox string if successful, None if failed
    """
    wfs_url = "http://10.2.114.150:8085/geoserver/wfs"
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typeName': layer_name,
        'outputFormat': 'application/json',
        'CQL_FILTER': f"vill_id='{village_code}'"
    }
    
    try:
        response = requests.get(wfs_url, params=params)
        response.raise_for_status()
        geojson = response.json()
        
        if not geojson.get('features'):
            print(f"No features found for village {village_code} in layer {layer_name}")
            return None
        
        # Calculate bbox from all feature coordinates
        coords = []
        for feature in geojson['features']:
            geom = feature['geometry']
            if geom['type'] == 'Point':
                coords.append(geom['coordinates'])
            elif geom['type'] == 'Polygon':
                for ring in geom['coordinates']:
                    coords.extend(ring)
            elif geom['type'] == 'MultiPolygon':
                for polygon in geom['coordinates']:
                    for ring in polygon:
                        coords.extend(ring)
        
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            
            # Calculate original bbox
            minx, miny, maxx, maxy = min(lons), min(lats), max(lons), max(lats)
            
            # Apply zoom factor by reducing the bbox size around its center
            if zoom_factor > 1.0:
                center_x = (minx + maxx) / 2
                center_y = (miny + maxy) / 2
                
                # Calculate new dimensions (smaller for higher zoom)
                width = (maxx - minx) / zoom_factor
                height = (maxy - miny) / zoom_factor
                
                # Recalculate bbox around center with new dimensions
                minx = center_x - width / 2
                maxx = center_x + width / 2
                miny = center_y - height / 2
                maxy = center_y + height / 2
                
                print(f"Applied zoom factor {zoom_factor} to WFS bbox")
            
            bbox = f"{minx},{miny},{maxx},{maxy}"
            
            # Validate the bbox
            is_valid, message = validate_bbox(bbox)
            if is_valid:
                print(f"Got valid bbox from WFS with zoom {zoom_factor}: {bbox}")
                return bbox
            else:
                print(f"Invalid bbox from WFS: {message}")
                
    except Exception as e:
        print(f"Error in WFS request for {layer_name}: {e}")
    
    return None

def get_layer_bbox_from_capabilities(layer_name):
    """
    Get bbox for a layer from GeoServer capabilities (fallback method).
    This gives the full extent of the layer, not filtered by village.
    
    Args:
        layer_name (str): GeoServer layer name
        
    Returns:
        str or None: Bbox string if successful, None if failed
    """
    capabilities_url = "http://10.2.114.150:8085/geoserver/wms"
    params = {
        'service': 'WMS',
        'version': '1.1.1',
        'request': 'GetCapabilities'
    }

    try:
        response = requests.get(capabilities_url, params=params)
        response.raise_for_status()
        xml_root = ET.fromstring(response.content)

        for layer in xml_root.findall(".//Layer/Layer"):
            name_elem = layer.find("Name")
            if name_elem is not None and name_elem.text == layer_name:
                bbox_elem = layer.find("LatLonBoundingBox")
                if bbox_elem is not None:
                    minx = bbox_elem.attrib['minx']
                    miny = bbox_elem.attrib['miny']
                    maxx = bbox_elem.attrib['maxx']
                    maxy = bbox_elem.attrib['maxy']
                    bbox = f"{minx},{miny},{maxx},{maxy}"
                    
                    # Validate the bbox
                    is_valid, message = validate_bbox(bbox)
                    if is_valid:
                        print(f"Got valid bbox from capabilities: {bbox}")
                        return bbox
                    else:
                        print(f"Invalid bbox from capabilities: {message}")

    except Exception as e:
        print(f"Error in capabilities request: {e}")
    
    return None

# =============================================================================
# DIMENSION CALCULATION AND CACHING
# =============================================================================

def get_optimal_dimensions_for_layer(layer_name, village_id=None, max_width=500):
    """
    Get optimal width/height for a layer based on its bbox aspect ratio.
    Uses caching to avoid repeated calculations.
    
    This is the core function that:
    1. Gets bbox for the layer (WFS -> capabilities -> village center)
    2. Calculates aspect ratio
    3. Determines optimal dimensions
    4. Caches results
    
    Args:
        layer_name (str): GeoServer layer name
        village_id (int): Village ID for filtering
        max_width (int): Maximum width constraint
        
    Returns:
        tuple: (width: int, height: int, bbox: str)
    """
    global _cached_layer_data
    
    # Create cache key combining layer and village
    cache_key = f"{layer_name}_{village_id or 'no_village'}"
    
    # Check cache first
    if cache_key in _cached_layer_data:
        print(f"Using cached dimensions for {cache_key}")
        return _cached_layer_data[cache_key]
    
    print(f"Calculating optimal dimensions for {cache_key}")
    
    # Get village code for filtering
    village_code = None
    village = None
    if village_id:
        try:
            village = tblVillage.objects.get(id=village_id)
            village_code = village.code
        except tblVillage.DoesNotExist:
            print(f"Village with id {village_id} not found")
    
    bbox = None
    
    # PRIORITY 1: Try to get bbox from WFS (most accurate for village data)
    if village_code:
        # bbox = get_layer_bbox_from_wfs(layer_name, village_code)
         bbox = get_layer_bbox_from_wfs('assam:village_boundary', village_code)
    
    # PRIORITY 2: Fallback to layer capabilities (full layer extent)
    if not bbox:
        bbox = get_layer_bbox_from_capabilities(layer_name)
    
    # PRIORITY 3: Last resort - use village center coordinates
    if not bbox and village and village.latitude and village.longitude:
        bbox = create_bbox_from_center(village.latitude, village.longitude, zoom_level=2)
        print(f"Using village center bbox as fallback")
    
    # If still no bbox, return defaults
    if not bbox:
        print(f"Could not get bbox for layer {layer_name}, using defaults")
        result = (max_width, 600, None)
        _cached_layer_data[cache_key] = result
        return result
    
    # Expand bbox with padding for better visualization
    expanded_bbox = expand_bbox(bbox, padding_percent=0.05)
    if expanded_bbox:
        bbox = expanded_bbox
    
    # Calculate optimal dimensions based on aspect ratio
    minx, miny, maxx, maxy = map(float, bbox.split(","))
    bbox_width = maxx - minx
    bbox_height = maxy - miny

    print("-------- BBOX-w and H ----------",bbox_width,bbox_height)
    
    if bbox_height == 0:
        aspect_ratio = 1.0
    else:
        aspect_ratio = bbox_width / bbox_height
    
    # Calculate height from width and aspect ratio
    width = max_width
    height = int(width / aspect_ratio)
    
    # Ensure reasonable height bounds
    height = max(height, 100)   # minimum 100px height
    height = min(height, 2000)  # maximum 2000px height
    
    result = (width, height, bbox)
    print("-------- BBOX-w and H ----------",bbox_width,bbox_height,height)
    
    # Cache the result
    _cached_layer_data[cache_key] = result
    print(f"Cached optimal dimensions for {cache_key}: {width}x{height}")
    
    return result



# =============================================================================
# MAP IMAGE GENERATION
# =============================================================================

def fetch_geoserver_map(layers, width, height, village_id=None):
    """
    Fetch map image from GeoServer WMS with village filtering.
    
    Handles two types of layers:
    - Layers WITH vill_id field: Apply CQL_FILTER for village-specific data
    - Layers WITHOUT vill_id field: No filtering (base layers like OSM)
    
    Args:
        layers (list): List of layer names
        width (int): Image width in pixels
        height (int): Image height in pixels
        village_id (int): Village ID for filtering
        
    Returns:
        PIL.Image: Composite map image
    """
    # Get bbox from cache or calculate
    bbox = get_cached_bbox_for_village(village_id, layers)
    
    if not bbox:
        raise Exception("Failed to retrieve valid bounding box for map.")
    
    # Final validation before making requests
    is_valid, message = validate_bbox(bbox)
    if not is_valid:
        raise Exception(f"Invalid bbox before WMS request: {message}")
    
    print(f"Fetching map with bbox: {bbox}, size: {width}x{height}")
    
    # Get village code for filtering
    village_code = None
    if village_id:
        try:
            village = tblVillage.objects.get(id=village_id)
            village_code = village.code
        except tblVillage.DoesNotExist:
            pass
    
    # Base layers that should always be included (no filtering)
    base_layers = ['assam:OSM-WMS', 'assam:state_boundary']
    
    # Separate user-provided layers from base layers
    user_filtered_layers = [layer for layer in layers if layer not in base_layers]
    
    # Always add village boundary for context if we have a village
    if village_code and 'assam:village_boundary' not in user_filtered_layers:
        user_filtered_layers.insert(0, 'assam:village_boundary')
    
    wms_url = "http://10.2.114.150:8085/geoserver/wms"
    final_image = None
    
    # 1. Get base layers (no filtering needed) - ALWAYS include these
    params_no_filter = {
        'service': 'WMS',
        'version': '1.1.1',
        'request': 'GetMap',
        'layers': ','.join(base_layers),  # Always include base layers
        'bbox': bbox,
        'width': width,
        'height': height,
        'srs': 'EPSG:4326',
        'format': 'image/png',
        'transparent': 'true'
    }
    
    try:
        print(f"Fetching base layers: {base_layers}")
        response = requests.get(wms_url, params=params_no_filter)
        response.raise_for_status()
        
        if 'image' in response.headers.get('content-type', ''):
            final_image = Image.open(BytesIO(response.content))
            print("Successfully fetched base layers")
        else:
            print(f"Error with base layers: {response.text}")
    except Exception as e:
        print(f"Error fetching base layers: {e}")
    
    # 2. Get filtered layers (village-specific data)
    if village_code and user_filtered_layers:
        # Apply same filter to all layers that support it
        filters_per_layer = [f"vill_id='{village_code}'"] * len(user_filtered_layers)
        
        params_filtered = {
            'service': 'WMS',
            'version': '1.1.1',
            'request': 'GetMap',
            'layers': ','.join(user_filtered_layers),
            'bbox': bbox,
            'width': width,
            'height': height,
            'srs': 'EPSG:4326',
            'format': 'image/png',
            'transparent': 'true',
            'CQL_FILTER': ';'.join(filters_per_layer),
             'format_options':'layout:test'
        }
        
        print(f"Applied CQL_FILTER for village {village_code} to layers: {user_filtered_layers}")
        
        try:
            response = requests.get(wms_url, params=params_filtered)
            response.raise_for_status()
            
            if 'image' in response.headers.get('content-type', ''):
                filtered_image = Image.open(BytesIO(response.content))
                print("Successfully fetched filtered layers")
                
                # Composite the images
                if final_image is None:
                    final_image = filtered_image
                else:
                    # Paste filtered layers on top of base layers
                    final_image.paste(filtered_image, (0, 0), filtered_image)
            else:
                print(f"Error with filtered layers: {response.text}")
        except Exception as e:
            print(f"Error fetching filtered layers: {e}")
            if final_image is None:
                raise
    elif not village_code and user_filtered_layers:
        # If no village code but user provided layers, fetch them without filtering
        params_unfiltered = {
            'service': 'WMS',
            'version': '1.1.1',
            'request': 'GetMap',
            'layers': ','.join(user_filtered_layers),
            'bbox': bbox,
            'width': width,
            'height': height,
            'srs': 'EPSG:4326',
            'format': 'image/png',
            'transparent': 'true',
             'format_options':'layout:test'
        }
        
        print(f"Fetching unfiltered user layers: {user_filtered_layers}")
        
        try:
            response = requests.get(wms_url, params=params_unfiltered)
            response.raise_for_status()
            
            if 'image' in response.headers.get('content-type', ''):
                unfiltered_image = Image.open(BytesIO(response.content))
                print("Successfully fetched unfiltered layers")
                
                # Composite the images
                if final_image is None:
                    final_image = unfiltered_image
                else:
                    final_image.paste(unfiltered_image, (0, 0), unfiltered_image)
            else:
                print(f"Error with unfiltered layers: {response.text}")
        except Exception as e:
            print(f"Error fetching unfiltered layers: {e}")
            if final_image is None:
                raise
    
    if final_image is None:
        raise Exception("Failed to fetch any map layers")
    
    return final_image



def get_cached_bbox_for_village(village_id, layers):
    """
    Get bbox for village with caching. Uses the first filterable layer to determine bbox.
    
    Args:
        village_id (int): Village ID
        layers (list): List of layer names
        
    Returns:
        str: Cached or calculated bbox string
    """
    global _cached_bbox
    
    cache_key = str(village_id)
    
    # Check cache
    if cache_key in _cached_bbox:
        print(f"Using cached bbox for village_id {village_id}")
        return _cached_bbox[cache_key]
    
    print(f"Calculating new bbox for village_id {village_id}")
    
    # Find a suitable layer for bbox calculation
    primary_layer = None
    for layer in layers:
        if layer not in ['assam:OSM-WMS', 'assam:state_boundary']:
            primary_layer = layer
            break
    
    if primary_layer:
        _, _, bbox = get_optimal_dimensions_for_layer('assam:village_boundary', village_id)
    else:
        # Fallback to village center if no suitable layer
        try:
            village = tblVillage.objects.get(id=village_id)
            if village.latitude and village.longitude:
                bbox = create_bbox_from_center(village.latitude, village.longitude, zoom_level=2)
            else:
                bbox = None
        except tblVillage.DoesNotExist:
            bbox = None
    
    if bbox:
        _cached_bbox[cache_key] = bbox
        print(f"Cached bbox for village_id {village_id}: {bbox}")
    
    return bbox

# =============================================================================
# MAIN PUBLIC FUNCTIONS
# =============================================================================

def get_geoserver_image_as_rl_image(layers, village_id=None, max_width=500, custom_height=None):
    """
    **MAIN FUNCTION**: Get geoserver map image as ReportLab Image object.
    
    This is the primary function you should use for generating maps in reports.
    It handles:
    - Auto-calculating optimal dimensions based on bbox aspect ratio
    - Caching to improve performance on repeated calls
    - Village-specific filtering
    - Memory-based image handling (no temp files)
    
    Args:
        layers (list): List of GeoServer layer names
        village_id (int): Village ID for filtering and bbox calculation
        max_width (int): Maximum width constraint (default: 500)
        custom_height (int): Override auto-calculated height if needed
        
    Returns:
        tuple: (rl_image: RLImage, actual_width: int, actual_height: int)
               Returns (None, None, None) if error occurs
    
    Example usage:
        layers = ['assam:building_footprint']
        img, width, height = get_geoserver_image_as_rl_image(layers, village_id=550)
        if img:
            elements.append(img)  # Add directly to ReportLab story
    """
    try:
        if custom_height:
            # Use custom height if provided

            img = fetch_geoserver_map(layers, max_width, custom_height, village_id)
            # Convert PIL image to BytesIO for ReportLab
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            rl_image = RLImage(img_buffer, width=max_width, height=custom_height)
            return rl_image, max_width, custom_height
        else:
            # Auto-calculate optimal dimensions
            primary_layer = None
            for layer in layers:
                if layer not in ['assam:OSM-WMS', 'assam:state_boundary']:
                    primary_layer = layer
                    break
            
            if primary_layer:
                width, height, bbox = get_optimal_dimensions_for_layer(primary_layer, village_id, max_width)
                print(f"Using optimal dimensions: {width}x{height}")
            else:
                width, height = max_width, 600
                print("Using default dimensions: {width}x{height}")
            
            img = fetch_geoserver_map(layers, width, height, village_id)
            # Convert PIL image to BytesIO for ReportLab
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            rl_image = RLImage(img_buffer, width=width, height=height)
            return rl_image, width, height
            
    except Exception as e:
        print(f"Error in get_geoserver_image_as_rl_image: {e}")
        return None, None, None

# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def clear_all_caches():
    """
    Clear both bbox and layer data caches.
    Call this when village data or layer configurations change.
    """
    global _cached_bbox, _cached_layer_data
    _cached_bbox.clear()
    _cached_layer_data.clear()
    print("All caches cleared")

def get_cache_status():
    """
    Get current cache status for debugging.
    
    Returns:
        dict: Cache statistics
    """
    return {
        'bbox_cache_size': len(_cached_bbox),
        'layer_cache_size': len(_cached_layer_data),
        'cached_villages': list(_cached_bbox.keys()),
        'cached_layers': list(_cached_layer_data.keys())
    }

import tempfile
import os
def get_geoserver_legend_path(layers, width=20, height=20):
    """Get geoserver legends and save to temp files, return paths"""
    try:
        legend_images = fetch_geoserver_legends(layers, width, height)
        legend_paths = []
        
        for i, img in enumerate(legend_images):
            if img:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                img.save(temp_file.name, 'PNG')
                legend_paths.append(temp_file.name)
        
        return legend_paths
    except Exception as e:
        print(f"Error in get_geoserver_legend_path: {e}")
        return []
    

def fetch_geoserver_legends(layers, width=20, height=20):
    """Fetch legends from geoserver for multiple layers"""
    wms_url = "http://10.2.114.150:8085/geoserver/wms"
    legend_images = []
    
    for layer in layers:
        params = {
            'service': 'WMS',
            'version': '1.1.1',
            'request': 'GetLegendGraphic',
            'layer': layer,
            'format': 'image/png',
            'width': width,
            'height': height
        }
        try:
            response = requests.get(wms_url, params=params)
            response.raise_for_status()
            legend_images.append(Image.open(BytesIO(response.content)))
        except Exception as e:
            print(f"Error fetching legend for {layer}: {e}")
    
    return legend_images

let mapObj = null;
let geoserverURL = "http://10.2.114.150:8085/geoserver";

// Add these variables at the top of your map.js file after existing declarations
//let printSelectedLayers = new Set(); // To store selected layers for printing
let printLayerCheckboxes = new Map(); // To track checkbox states

// ol-ext popup variables
let popup = null;
let selectInteraction = null;

// Multi-layer popup variables
let clickedLayers = [];
let currentLayerIndex = 0;

// Single base layer reference
let baseLayer = null;

let other_layer_zIndex=10000;
const districtSelect = document.getElementById('Layer_district');
const villageSelect = document.getElementById('layer_village');

document.addEventListener('DOMContentLoaded', function () {
    // Create single base layer with OSM as default
    console.log(ol);
    console.log(ol.control.FullScreen,ol.control.PrintDialog);
    

    // Add event listeners after DOM is ready
    setTimeout(() => {
        const districtSelect = document.getElementById('Layer_district');
        const villageSelect = document.getElementById('layer_village');
        
        if (districtSelect) {
            districtSelect.addEventListener('change', reloadLayersWithFilter);
        }
        if (villageSelect) {
            villageSelect.addEventListener('change', reloadLayersWithFilter);
        }
    }, 100);
    
    baseLayer = new ol.layer.Tile({
        title: 'BaseMap',
        type: 'base',
        visible: true,
        zIndex: 0,
        source: new ol.source.OSM({
            crossOrigin: 'anonymous'
        })
    });

    // Create map with single base layer
    const map = new ol.Map({
        target: 'mapDiv',
        layers: [baseLayer], // Only one base layer
        view: new ol.View({
            projection: 'EPSG:4326',
            center: [92.9376, 26.2006],
            zoom: 7
        })
    });

    // Add controls directly
    map.addControl(new ol.control.FullScreen());
    map.addControl(new ol.control.PrintDialog());
    // map.addControl(new ol.control.ZoomSlider());
    // map.addControl(new ol.control.ScaleLine({bar: true, text: true, minWidth: 125}));

    

    // Add a title control
    map.addControl(new ol.control.CanvasTitle({ 
    title: 'my title', 
    visible: false,
    style: new ol.style.Style({ text: new ol.style.Text({ font: '20px "Lucida Grande",Verdana,Geneva,Lucida,Arial,Helvetica,sans-serif'}) })
    }));
    // Add a ScaleLine control 
map.addControl(new ol.control.CanvasScaleLine());

// Print control
var printControl = new ol.control.PrintDialog({ 
  // target: document.querySelector('.info'),
  // targetDialog: map.getTargetElement() 
  // save: false,
  // copy: false,
  // pdf: false
});
printControl.setSize('A4');
map.addControl(printControl);

/* On print > save image file */
printControl.on(['print', 'error'], function(e) {
  // Print success
  if (e.image) {
    if (e.pdf) {
      // Export pdf using the print info
      var pdf = new jsPDF({
        orientation: e.print.orientation,
        unit: e.print.unit,
        format: e.print.size
      });
      pdf.addImage(e.image, 'JPEG', e.print.position[0], e.print.position[0], e.print.imageWidth, e.print.imageHeight);
      pdf.save(e.print.legend ? 'legend.pdf' : 'map.pdf');
    } else  {
      // Save image as file
      e.canvas.toBlob(function(blob) {
        var name = (e.print.legend ? 'legend.' : 'map.')+e.imageType.replace('image/','');
        saveAs(blob, name);
      }, e.imageType, e.quality);
    }
  } else {
    console.warn('No canvas to export');
  }
});


    mapObj = map;

    // Initialize enhanced multi-layer popup
    initializeMultiLayerPopup();

    // Enhanced base map switch logic
    document.querySelectorAll('.basemap-item').forEach(item => {
        item.addEventListener('click', function () {
            document.querySelectorAll('.basemap-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            const selectedType = this.getAttribute('data-map-type');
            
            // Switch base layer source based on selection
            switchBaseMapSource(selectedType);
        });
    });
});

// Function to switch base map source
function switchBaseMapSource(mapType) {
    if (!baseLayer) {
        console.error('Base layer not initialized');
        return;
    }

    let newSource;

    switch(mapType) {
        case 'osm':
            newSource = new ol.source.OSM({
                crossOrigin: 'anonymous'
            });
            baseLayer.setVisible(true);
            break;
            
        case 'satellite':
            newSource = new ol.source.XYZ({
                url: 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
                crossOrigin: 'anonymous'
            });
            baseLayer.setVisible(true);
            break;
            
        case 'terrain':
            newSource = new ol.source.XYZ({
                url: 'http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}&s=Ga',
                crossOrigin: 'anonymous'
            });
            baseLayer.setVisible(true);
            break;
            
        case 'blank':
            // For blank, hide the base layer instead of creating empty source
            baseLayer.setVisible(false);
            console.log('Base layer hidden for blank map');
            return; // Exit early, no need to set new source
            
        default:
            console.warn('Unknown map type:', mapType);
            return;
    }
    
    // Set the new source to the base layer
    baseLayer.setSource(newSource);
    
    // Ensure overlay layers stay on top
    ensureOverlayLayersOnTop();
    
    console.log(`Base map switched to: ${mapType}`);
}

// Function to ensure overlay layers are always on top
function ensureOverlayLayersOnTop() {
    const layers = mapObj.getLayers().getArray();
    
    // Set z-index for all layers
    layers.forEach((layer, index) => {
        if (layer.get('type') === 'base') {
            layer.setZIndex(0); // Base layer at bottom
        } else {
            layer.setZIndex(1000 + index); // Overlay layers on top
        }
    });
    
    // Force map refresh
    mapObj.render();
    
    console.log('Layer z-index updated');
}

// Initialize enhanced multi-layer popup
function initializeMultiLayerPopup() {
    // Create popup using ol-ext
    popup = new ol.Overlay.Popup({
        popupClass: "default anim multi-layer-popup",
        closeBox: true,
        positioning: 'auto',
        autoPan: {
            animation: {
                duration: 250,
            },
        }
    });
    
    mapObj.addOverlay(popup);

    // Handle map clicks for all layers (both Vector and WMS)
    mapObj.on('singleclick', handleMultiLayerClick);
    
    // Add event delegation for navigation buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('#prevLayerBtn')) {
            e.stopPropagation();
            navigateLayer(-1);
        } else if (e.target.closest('#nextLayerBtn')) {
            e.stopPropagation();
            navigateLayer(1);
        }
    });

    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (popup && popup.getVisible()) {
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    navigateLayer(-1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    navigateLayer(1);
                    break;
                case 'Escape':
                    e.preventDefault();
                    hidePopup();
                    break;
            }
        }
    });
}

// Enhanced click handler to collect data from ALL layers at clicked location
async function handleMultiLayerClick(event) {
    const coordinate = event.coordinate;
    const pixel = event.pixel;
    
    // Reset variables
    clickedLayers = [];
    currentLayerIndex = 0;
    
    // Show loading indicator
    showLoadingPopup(coordinate);
    
    // Get all layers at clicked location
    const layers = mapObj.getLayers().getArray();
    
    // Process each layer to check if it has features at clicked location
    for (let layer of layers) {
        // Skip base layers
        if (layer.get('type') === 'base') continue;
        
        const layerName = layer.get('name') || layer.get('title');
        if (!layerName) continue;
        
        try {
            if (layer instanceof ol.layer.Vector) {
                // Handle vector layers
                await handleVectorLayer(layer, coordinate, layerName);
            } else if (layer instanceof ol.layer.Tile && layer.getSource() instanceof ol.source.TileWMS) {
                // Handle WMS layers with GetFeatureInfo
                await handleWMSLayer(layer, coordinate, layerName);
            }
        } catch (error) {
            console.warn(`Error querying layer ${layerName}:`, error);
        }
    }
    
    // Show results or hide popup
    if (clickedLayers.length > 0) {
        showMultiLayerPopup(coordinate);
        console.log(`Found ${clickedLayers.length} features at clicked location`);
    } else {
        hidePopup();
        console.log('No data found at clicked location');
    }
}

// Handle vector layer features
async function handleVectorLayer(layer, coordinate, layerName) {
    const features = layer.getSource().getFeaturesAtCoordinate(coordinate);
    if (features && features.length > 0) {
        features.forEach((feature, index) => {
            const properties = feature.getProperties();
            delete properties.geometry;
            
            clickedLayers.push({
                name: features.length > 1 ? `${layerName} (Feature ${index + 1})` : layerName,
                properties: properties,
                type: 'Vector',
                layer: layer,
                feature: feature,
                layerOrder: getLayerZIndex(layer)
            });
        });
    }
}

// Handle WMS layer features
async function handleWMSLayer(layer, coordinate, layerName) {
    const wmsSource = layer.getSource();
    const url = wmsSource.getFeatureInfoUrl(
        coordinate,
        mapObj.getView().getResolution(),
        mapObj.getView().getProjection(),
        {
            'INFO_FORMAT': 'application/json',
            'FEATURE_COUNT': 10, // Get multiple features if available
            'QUERY_LAYERS': wmsSource.getParams()['LAYERS']
        }
    );
    
    if (url) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.features && data.features.length > 0) {
                data.features.forEach((feature, index) => {
                    const properties = feature.properties;
                    
                    clickedLayers.push({
                        name: data.features.length > 1 ? `${layerName} (Feature ${index + 1})` : layerName,
                        properties: properties,
                        type: 'WMS',
                        layer: layer,
                        feature: feature,
                        layerOrder: getLayerZIndex(layer)
                    });
                });
            }
        } catch (fetchError) {
            console.warn(`Error fetching feature info for ${layerName}:`, fetchError);
        }
    }
}

// Get layer z-index for ordering
function getLayerZIndex(layer) {
    const layers = mapObj.getLayers().getArray();
    return layers.indexOf(layer);
}

// Show loading popup
function showLoadingPopup(coordinate) {
    const loadingContent = `
        <div class="popup-header">
            <h6 class="popup-title">Loading...</h6>
        </div>
        <div class="popup-body text-center py-3">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 mb-0 text-muted">Querying layers...</p>
        </div>
    `;
    popup.show(coordinate, loadingContent);
}

// Show popup with multi-layer navigation support
function showMultiLayerPopup(coordinate) {
    // Sort layers by their order (top layers first)
    clickedLayers.sort((a, b) => b.layerOrder - a.layerOrder);
    
    const content = createMultiLayerPopupContent();
    popup.show(coordinate, content);
}

// Create popup content with navigation controls
function createMultiLayerPopupContent() {
    const layerData = clickedLayers[currentLayerIndex];
    const totalLayers = clickedLayers.length;
    console.log("layerData-> ",layerData)
    // Create navigation header (only show if multiple layers)
    const navigationHeader = totalLayers > 1 ? `
        <div class="popup-navigation d-flex justify-content-between align-items-center mb-1 p-2 bg-light rounded">
            <button id="prevLayerBtn" class="btn btn-sm btn-outline-primary ${currentLayerIndex === 0 ? 'disabled' : ''}" 
                    ${currentLayerIndex === 0 ? 'disabled' : ''}>
                <i class="fa-solid fa-chevron-left"></i>
            </button>
            <div class="layer-info text-center">
                <span class="layer-counter fw-bold text-primary">
                    ${currentLayerIndex + 1} of ${totalLayers}
                </span>
                <br>
                <small class="text-muted">Use arrows to navigate</small>
            </div>
            <button id="nextLayerBtn" class="btn btn-sm btn-outline-primary ${currentLayerIndex === totalLayers - 1 ? 'disabled' : ''}"
                    ${currentLayerIndex === totalLayers - 1 ? 'disabled' : ''}>
                <i class="fa-solid fa-chevron-right"></i>
            </button>
        </div>
    ` : '';
    
    // Create main content
    let content = `
        <div class="multi-layer-popup-container">
            ${navigationHeader}
            <div class="popup-header">
                <h6 class="popup-title">${layerData.name}</h6>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">Type: ${layerData.type}</small>
                    ${totalLayers > 1 ? `<small class="badge bg-secondary">${currentLayerIndex + 1}/${totalLayers}</small>` : ''}
                </div>
            </div>
            <div class="popup-body">
    `;
    
    // Add properties table
    if (Object.keys(layerData.properties).length === 0) {
        content += `
            <div class="text-center py-4">
                <i class="fa-solid fa-info-circle text-muted mb-2" style="font-size: 24px;"></i>
                <p class="text-muted mb-0">No properties available</p>
            </div>
        `;
    } else {
        content += `
            <div class="table-responsive">
                <table class="table table-sm table-striped table-hover mb-0 popover_table">
                    <thead class="table-dark ">
                        <tr>
                            <th scope="col" style="min-width: 120px;">Property</th>
                            <th scope="col">Value</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        for (const [key, value] of Object.entries(layerData.properties)) {
            const displayValue = value !== null && value !== undefined ? String(value) : 'N/A';
            // Truncate long values and add tooltip
            const truncatedValue = displayValue.length > 50 ? 
                `${displayValue.substring(0, 50)}...` : displayValue;
            
            content += `
                <tr>
                    <td class=" text-nowrap">${key}</td>
                    <td title="${displayValue}">${truncatedValue}</td>
                </tr>
            `;
        }
        
        content += '</tbody></table></div>';
    }
    
    // Add footer with layer summary (if multiple layers)
    if (totalLayers > 1) {
        // content += `
        //     <div class="popup-footer mt-3 pt-2 border-top">
        //         <small class="text-muted">
        //             <i class="fa-solid fa-layers me-1"></i>
        //             ${totalLayers} layers found at this location
        //         </small>
        //     </div>
        // `;
    }
    
    content += '</div></div>';
    return content;
}

// Navigate between layers
function navigateLayer(direction) {
    const newIndex = currentLayerIndex + direction;
    
    if (newIndex >= 0 && newIndex < clickedLayers.length) {
        currentLayerIndex = newIndex;
        updatePopupContent();
        console.log(`Navigated to layer ${currentLayerIndex + 1} of ${clickedLayers.length}: ${clickedLayers[currentLayerIndex].name}`);
    }
}

// Update popup content without hiding/showing (smoother transition)
function updatePopupContent() {
    const content = createMultiLayerPopupContent();
    const popupElement = popup.getElement();
    
    if (popupElement) {
        // Find the content container and update it
        const contentContainer = popupElement.querySelector('.ol-popup-content');
        if (contentContainer) {
            // Add fade effect
            contentContainer.style.opacity = '0.7';
            
            setTimeout(() => {
                contentContainer.innerHTML = content;
                contentContainer.style.opacity = '1';
            }, 100);
        }
    }
}

// Function to get current CQL filter
function getCurrentCQLFilter() {
    const districtSelect = document.getElementById('Layer_district');
    const villageSelect = document.getElementById('layer_village');
    
    const districtId = districtSelect?.selectedOptions[0]?.getAttribute('code') || null;
    const villageId = villageSelect?.selectedOptions[0]?.getAttribute('code') || null;
    
    const filters = [];
    if (districtId) filters.push(`dist_id='${districtId}'`);
    if (villageId) filters.push(`vill_id='${villageId}'`);
    
    return filters.length > 0 ? filters.join(' AND ') : null;
}

// Enhanced function to add layer to map with popup support
function addLayerToMap(layer, type = 'vector') {
    const fullLayerName = `${layer.id}_${layer.layer_name}_${layer.workspace}`;
    let newLayer;
    const currentFilter = getCurrentCQLFilter();

    other_layer_zIndex+=1;
    
    if (type === 'vector') {
        const params = {
            'LAYERS': `${layer.workspace}:${layer.layer_name}`,
            'TILED': true,
            'FORMAT': 'image/png',
            'TRANSPARENT': true
        };
        if (currentFilter) params.CQL_FILTER = currentFilter;
        
        newLayer = new ol.layer.Tile({
            title: fullLayerName,
            source: new ol.source.TileWMS({
                url: `${geoserverURL}/${layer.workspace}/wms`,
                params: params,
                serverType: 'geoserver'
            }),
            zIndex: other_layer_zIndex
        });
    } else if (type === 'raster') {
        const params = {
            'LAYERS': `${layer.workspace}:${layer.layer_name}`,
            'TILED': true,
            'FORMAT': 'image/png',
            'TRANSPARENT': true
        };
        if (currentFilter) params.CQL_FILTER = currentFilter;
        
        newLayer = new ol.layer.Tile({
            title: fullLayerName,
            source: new ol.source.TileWMS({
                url: `${geoserverURL}/${layer.workspace}/wms`,
                params: params,
                serverType: 'geoserver'
            }),
            zIndex: other_layer_zIndex
        });
    } else if (type === 'geojson') {
        newLayer = new ol.layer.Vector({
            title: fullLayerName,
            source: new ol.source.Vector({
                url: `/static/temp_Map_data/${layer.layer_name}.geojson`,
                format: new ol.format.GeoJSON()
            }),
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'blue',
                    width: 1
                }),
                fill: new ol.style.Fill({
                    color: 'rgba(0, 0, 255, 0.1)'
                })
            }),
            zIndex: other_layer_zIndex
        });
    } else {
        console.error('Invalid layer type. Use "vector", "raster", or "geojson"');
        return;
    }
    
  
    newLayer.set('name', fullLayerName);
    mapObj.addLayer(newLayer);
    
    console.log(`Layer ${fullLayerName} added to map as ${type} layer`);
    return newLayer;
}

// Function to change layer opacity
function changeLayerOpacity(layerName, opacityValue) {
    const opacity = parseFloat(opacityValue);
    const layers = mapObj.getLayers().getArray();
    const targetLayer = layers.find(layer => {
        const layerName_prop = layer.get('name') || layer.get('title');
        return layerName_prop === layerName;
    });
    
    if (targetLayer) {
        targetLayer.setOpacity(opacity);
        console.log(`Opacity of layer ${layerName} changed to ${opacityValue}%`);
    } else {
        console.error(`Layer ${layerName} not found in map`);
    }
}

// Function to remove layer from map
function removeLayerFromMap(layerName) {
    const layers = mapObj.getLayers().getArray();
    const targetLayer = layers.find(layer => {
        const layerName_prop = layer.get('name') || layer.get('title');
        return layerName_prop === layerName;
    });
    
    if (targetLayer) {
        mapObj.removeLayer(targetLayer);
        
        if (targetLayer instanceof ol.layer.Vector) {
            const source = targetLayer.getSource();
            if (source && source.clear) {
                source.clear();
            }
        }
        
        console.log(`Layer ${layerName} removed from map`);
        return true;
    } else {
        console.error(`Layer ${layerName} not found in map`);
        return false;
    }
}

// Utility functions

// Show popup at specific coordinate with custom content
function showPopupAt(coordinate, title, content) {
    const html = `
        <div class="popup-header">
            <h6>${title}</h6>
        </div>
        <div class="popup-body">
            ${content}
        </div>
    `;
    popup.show(coordinate, html);
}

// Hide popup and reset multi-layer state
function hidePopup() {
    if (popup) {
        popup.hide();
        clickedLayers = [];
        currentLayerIndex = 0;
    }
}

// Check if popup is visible
function isPopupVisible() {
    return popup && popup.getVisible();
}

// Get current layer information
function getCurrentLayerInfo() {
    if (clickedLayers.length > 0) {
        return {
            current: currentLayerIndex,
            total: clickedLayers.length,
            layer: clickedLayers[currentLayerIndex]
        };
    }
    return null;
}

// Jump to specific layer by index
function jumpToLayer(index) {
    if (index >= 0 && index < clickedLayers.length) {
        currentLayerIndex = index;
        updatePopupContent();
    }
}

// Get all layers at current click location
function getAllLayersAtLocation() {
    return clickedLayers.map((layer, index) => ({
        index: index,
        name: layer.name,
        type: layer.type,
        propertyCount: Object.keys(layer.properties).length
    }));
}

// Function to zoom to specific lat/lon with default zoom level
function zoomToLatLon(lat, lon, zoomLevel = 12) {
    if (!mapObj) {
        console.error('Map object not initialized');
        return;
    }
    
    const coordinate = [lon, lat]; // OpenLayers uses [lon, lat] format
    
    mapObj.getView().animate({
        center: coordinate,
        zoom: zoomLevel,
        duration: 1000 // Animation duration in milliseconds
    });
    
    console.log(`Zoomed to coordinates: ${lat}, ${lon} at zoom level ${zoomLevel}`);
}

// Function to reload layers with CQL filter
function reloadLayersWithFilter() {
    const districtSelect = document.getElementById('Layer_district');
    const villageSelect = document.getElementById('layer_village');
    
    const districtId = districtSelect.selectedOptions[0]?.getAttribute('code') || null;
    const villageId = villageSelect.selectedOptions[0]?.getAttribute('code') || null;
    
    console.log("reload the layer ",districtId, villageId)
    let cqlFilter = '';
    const filters = [];
    
    if (districtId) {
        filters.push(`dist_id='${districtId}'`);
    }
    if (villageId) {
        filters.push(`vill_id='${villageId}'`);
    }
    
    if (filters.length > 0) {
        cqlFilter = filters.join(' AND ');
    }

    console.log('CQL filter:', cqlFilter || 'No filter');
    
    // Get all layers from map and reload with filter
    mapObj.getLayers().forEach(layer => {
        if (layer.get('name') && layer.getSource() instanceof ol.source.TileWMS) {
            const source = layer.getSource();
            const params = source.getParams();
            
            if (cqlFilter) {
                params.CQL_FILTER = cqlFilter;
            } else {
                delete params.CQL_FILTER;
            }
            
            source.updateParams(params);
        }
    });
    
    console.log('Layers reloaded with CQL filter:', cqlFilter || 'No filter');
}



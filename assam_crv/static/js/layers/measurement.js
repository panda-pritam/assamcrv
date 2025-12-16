// Enhanced Measurement tool variables
let measurementSource = null;
let measurementLayer = null;
let drawInteraction = null;
let modifyInteraction = null;
let snapInteraction = null;
let measurementType = 'length';
let measurementUnits = 'm';
let currentMeasurement = null;
let measurements = [];
let isDrawing = false;

// Style definitions
const drawingStyle = new ol.style.Style({
    fill: new ol.style.Fill({
        color: 'rgba(255, 255, 255, 0.2)'
    }),
    stroke: new ol.style.Stroke({
        color: '#242727',
        width: 2
    }),
    image: new ol.style.Circle({
        radius: 5,
        stroke: new ol.style.Stroke({
            color: '#242727'
        }),
        fill: new ol.style.Fill({
            color: 'rgba(255, 255, 255, 0.2)'
        })
    })
});

const finishedStyle = new ol.style.Style({
    fill: new ol.style.Fill({
        color: 'rgba(255, 204, 51, 0.2)'
    }),
    stroke: new ol.style.Stroke({
        color: '#242727',
        width: 2
    }),
    image: new ol.style.Circle({
        radius: 6,
        fill: new ol.style.Fill({
            color: '#242727'
        })
    })
});

const hoveredStyle = new ol.style.Style({
    fill: new ol.style.Fill({
        color: 'rgba(255, 0, 0, 0.3)'
    }),
    stroke: new ol.style.Stroke({
        color: '#ff0000',
        width: 3
    }),
    image: new ol.style.Circle({
        radius: 6,
        fill: new ol.style.Fill({
            color: '#ff0000'
        })
    })
});

// Label styles
const mainLabelStyle = new ol.style.Style({
    text: new ol.style.Text({
        font: 'bold 14px Arial, sans-serif',
        fill: new ol.style.Fill({
            color: '#ffffff'
        }),
        backgroundFill: new ol.style.Fill({
            color: 'rgba(0, 0, 0, 0.7)'
        }),
        padding: [4, 8, 4, 8],
        textBaseline: 'bottom',
        offsetY: -15
    })
});

const sideLabelStyle = new ol.style.Style({
    text: new ol.style.Text({
        font: '12px Arial, sans-serif',
        fill: new ol.style.Fill({
            color: '#ffffff'
        }),
        backgroundFill: new ol.style.Fill({
            color: 'rgba(255, 87, 34, 0.8)'
        }),
        padding: [2, 6, 2, 6],
        textBaseline: 'bottom',
        offsetY: -10
    })
});

// Initialize measurement tool
function initializeMeasurementTool() {
    // Create measurement source and layer
    measurementSource = new ol.source.Vector();
    measurementLayer = new ol.layer.Vector({
        source: measurementSource,
        style: createFeatureStyle,
        zIndex: 1000
    });
    
    mapObj.addLayer(measurementLayer);
    
    // Create snap interaction
    snapInteraction = new ol.interaction.Snap({ 
        source: measurementSource 
    });
    mapObj.addInteraction(snapInteraction);
    
    // Event listeners
    document.getElementById('measurementTogglerBtn').addEventListener('click', toggleMeasurementPanel);
    document.getElementById('measurementDivCloseButton').addEventListener('click', closeMeasurementPanel);
    document.getElementById('startMeasureBtn').addEventListener('click', startMeasurement);
    // document.getElementById('stopMeasureBtn').addEventListener('click', stopMeasurement);
    document.getElementById('clearMeasureBtn').addEventListener('click', clearMeasurements);
    
    // Radio button change
    document.querySelectorAll('input[name="measureType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            measurementType = this.value;
            updateUnitsOptions();
        });
    });
    
    // Units change
    document.getElementById('measurementUnits').addEventListener('change', function() {
        measurementUnits = this.value;
        updateExistingMeasurements();
    });
    
    updateUnitsOptions();
    createMeasurementsList();
}

// Create feature style with labels
function createFeatureStyle(feature, resolution) {
    const styles = [];
    const geometry = feature.getGeometry();
    const type = geometry.getType();
    const isDrawingMode = feature.get('isDrawing') || false;
    const isHovered = feature.get('isHovered') || false;
    
    // Base style
    if (isHovered) {
        styles.push(hoveredStyle);
    } else {
        styles.push(isDrawingMode ? drawingStyle : finishedStyle);
    }
    
    let point, label, line;
    
    if (type === 'Polygon') {
        point = geometry.getInteriorPoint();
        label = formatArea(geometry);
        line = new ol.geom.LineString(geometry.getCoordinates()[0]);
    } else if (type === 'LineString') {
        point = new ol.geom.Point(geometry.getLastCoordinate());
        label = formatLength(geometry);
        line = geometry;
    }
    
    // Main label for finished features
    if (label && point && !isDrawingMode) {
        const mainStyle = mainLabelStyle.clone();
        mainStyle.setGeometry(point);
        mainStyle.getText().setText(label);
        styles.push(mainStyle);
    }
    
    // Segment labels
    if (line && resolution < 100) { // Only show segment labels at close zoom
        const coordinates = line.getCoordinates();
        for (let i = 0; i < coordinates.length - 1; i++) {
            const start = coordinates[i];
            const end = coordinates[i + 1];
            const segment = new ol.geom.LineString([start, end]);
            const segmentLength = formatLength(segment);
            const midPoint = new ol.geom.Point(segment.getCoordinateAt(0.5));
            
            const sideStyle = (isDrawingMode ? drawingStyle : sideLabelStyle).clone();
            sideStyle.setGeometry(midPoint);
            sideStyle.getText().setText(segmentLength);
            styles.push(sideStyle);
        }
    }
    
    return styles;
}

// Toggle measurement panel
function toggleMeasurementPanel() {
    const panel = document.getElementById('measurementOptionsDiv');
    const isVisible = panel.style.display === 'block';
    
    // Hide other panels
    document.getElementById('baseMapOptionsDiv').style.display = 'none';
    document.getElementById('layerDiv').style.display = 'none';
    
    panel.style.display = isVisible ? 'none' : 'block';
}

// Close measurement panel
function closeMeasurementPanel() {
    document.getElementById('measurementOptionsDiv').style.display = 'none';
    stopMeasurement();
}

// Update units options based on measurement type
function updateUnitsOptions() {
    const unitsSelect = document.getElementById('measurementUnits');
    unitsSelect.innerHTML = '';
    
    if (measurementType === 'length') {
        unitsSelect.innerHTML = `
            <option value="m">Meters (m)</option>
            <option value="km">Kilometers (km)</option>
            <option value="ft">Feet (ft)</option>
            <option value="mi">Miles (mi)</option>
            <option value="cm">Centimeters (cm)</option>
        `;
    } else {
        unitsSelect.innerHTML = `
            <option value="m2">Square Meters (m²)</option>
            <option value="km2">Square Kilometers (km²)</option>
            <option value="ft2">Square Feet (ft²)</option>
            <option value="ha">Hectares (ha)</option>
            <option value="cm2">Square Centimeters (cm²)</option>
        `;
    }
    measurementUnits = unitsSelect.value;
}

// Start measurement
function startMeasurement() {
    stopMeasurement(); // Stop any existing measurement
    
    const geometryType = measurementType === 'length' ? 'LineString' : 'Polygon';
    
    drawInteraction = new ol.interaction.Draw({
        source: measurementSource,
        type: geometryType,
        style: function(feature) {
            feature.set('isDrawing', true);
            return createFeatureStyle(feature);
        }
    });
    
    mapObj.addInteraction(drawInteraction);
    isDrawing = true;
    
    let sketch;
    let listener;
    
    // Handle draw start
    drawInteraction.on('drawstart', function(event) {
        sketch = event.feature;
        sketch.set('isDrawing', true);
        
        // Listen to geometry changes during drawing
        listener = sketch.getGeometry().on('change', function(evt) {
            const geom = evt.target;
            let output;
            
            if (geom instanceof ol.geom.Polygon) {
                output = formatArea(geom);
            } else if (geom instanceof ol.geom.LineString) {
                output = formatLength(geom);
            }
            
            updateCurrentMeasurementDisplay(output);
        });
    });
    
    // Handle draw end
    drawInteraction.on('drawend', function(event) {
        const feature = event.feature;
        const geometry = feature.getGeometry();
        
        // Remove drawing flag and set ID
        feature.unset('isDrawing');
        feature.setId(Date.now().toString());
        
        let measurement;
        if (measurementType === 'length') {
            measurement = getLength(geometry);
        } else {
            measurement = getArea(geometry);
        }
        
        // Add to measurements array
        measurements.push({
            id: feature.getId(),
            type: measurementType,
            value: measurement.formatted,
            feature: feature
        });
        
        displayMeasurement(measurement);
        updateMeasurementsList();
        currentMeasurement = measurement;
        
        // Clean up listener
        if (listener) {
            ol.Observable.unByKey(listener);
            listener = null;
        }
        
        // Auto stop after drawing
        setTimeout(() => stopMeasurement(), 100);
    });
    
    // Handle draw abort
    drawInteraction.on('drawabort', function() {
        hideCurrentMeasurementDisplay();
        if (listener) {
            ol.Observable.unByKey(listener);
            listener = null;
        }
    });
    
    // Update UI
    document.getElementById('startMeasureBtn').disabled = true;
    // document.getElementById('stopMeasureBtn').disabled = false;
    document.getElementById('measurementResult').style.display = 'none';
    showCurrentMeasurementDisplay();
}

// Stop measurement
function stopMeasurement() {
    if (drawInteraction) {
        mapObj.removeInteraction(drawInteraction);
        drawInteraction = null;
    }
    
    isDrawing = false;
    hideCurrentMeasurementDisplay();
    
    // Update UI
    document.getElementById('startMeasureBtn').disabled = false;
    // document.getElementById('stopMeasureBtn').disabled = true;
}

// Clear all measurements
function clearMeasurements() {
    measurementSource.clear();
    measurements = [];
    document.getElementById('measurementResult').style.display = 'none';
    currentMeasurement = null;
    updateMeasurementsList();
    stopMeasurement();
}

// Update existing measurements when units change
function updateExistingMeasurements() {
    measurements.forEach(measurement => {
        const geometry = measurement.feature.getGeometry();
        let newValue;
        
        if (geometry instanceof ol.geom.LineString) {
            newValue = getLength(geometry);
        } else if (geometry instanceof ol.geom.Polygon) {
            newValue = getArea(geometry);
        }
        
        measurement.value = newValue.formatted;
    });
    
    // Force re-render of all features
    measurementSource.changed();
    updateMeasurementsList();
}

// Calculate length with proper formatting
function getLength(geometry) {
    const length = ol.sphere.getLength(geometry, {projection: 'EPSG:4326'});
    return convertLength(length, measurementUnits);
}

// Calculate area with proper formatting
function getArea(geometry) {
    const area = ol.sphere.getArea(geometry, {projection: 'EPSG:4326'});
    return convertArea(area, measurementUnits);
}

// Format length for display
function formatLength(geometry) {
    const length = ol.sphere.getLength(geometry, {projection: 'EPSG:4326'});
    return convertLength(length, measurementUnits).formatted;
}

// Format area for display
function formatArea(geometry) {
    const area = ol.sphere.getArea(geometry, {projection: 'EPSG:4326'});
    return convertArea(area, measurementUnits).formatted;
}

// Convert length units (enhanced)
function convertLength(lengthInMeters, unit) {
    let value, unitLabel;
    
    switch(unit) {
        case 'km':
            value = lengthInMeters / 1000;
            unitLabel = 'km';
            break;
        case 'ft':
            value = lengthInMeters * 3.28084;
            unitLabel = 'ft';
            break;
        case 'mi':
            value = lengthInMeters * 0.000621371;
            unitLabel = 'mi';
            break;
        case 'cm':
            value = lengthInMeters * 100;
            unitLabel = 'cm';
            break;
        default:
            value = lengthInMeters;
            unitLabel = 'm';
    }
    
    return {
        value: parseFloat(value.toFixed(2)),
        unit: unitLabel,
        formatted: `${parseFloat(value.toFixed(2))} ${unitLabel}`
    };
}

// Convert area units (enhanced)
function convertArea(areaInSquareMeters, unit) {
    let value, unitLabel;
    
    switch(unit) {
        case 'km2':
            value = areaInSquareMeters / 1000000;
            unitLabel = 'km²';
            break;
        case 'ft2':
            value = areaInSquareMeters * 10.7639;
            unitLabel = 'ft²';
            break;
        case 'ha':
            value = areaInSquareMeters / 10000;
            unitLabel = 'ha';
            break;
        case 'cm2':
            value = areaInSquareMeters * 10000;
            unitLabel = 'cm²';
            break;
        default:
            value = areaInSquareMeters;
            unitLabel = 'm²';
    }
    
    return {
        value: parseFloat(value.toFixed(2)),
        unit: unitLabel,
        formatted: `${parseFloat(value.toFixed(2))} ${unitLabel}`
    };
}

// Display measurement result
function displayMeasurement(measurement) {
    const resultDiv = document.getElementById('measurementResult');
    const valueDiv = document.getElementById('measurementValue');
    
    valueDiv.textContent = measurement.formatted;
    resultDiv.style.display = 'block';
}

// Current measurement display functions
function showCurrentMeasurementDisplay() {
    let currentDiv = document.getElementById('currentMeasurementDisplay');
    if (!currentDiv) {
        currentDiv = document.createElement('div');
        currentDiv.id = 'currentMeasurementDisplay';
        currentDiv.className = 'mt-3 p-2 bg-info text-white rounded';
        currentDiv.style.display = 'none';
        currentDiv.innerHTML = `
            <small>Current Measurement:</small>
            <div class="fw-bold" id="currentMeasurementValue">-</div>
        `;
        document.querySelector('.measurement-container').appendChild(currentDiv);
    }
}

function updateCurrentMeasurementDisplay(value) {
    const currentDiv = document.getElementById('currentMeasurementDisplay');
    const valueDiv = document.getElementById('currentMeasurementValue');
    if (currentDiv && valueDiv) {
        currentDiv.style.display = 'block';
        valueDiv.textContent = value;
    }
}

function hideCurrentMeasurementDisplay() {
    const currentDiv = document.getElementById('currentMeasurementDisplay');
    if (currentDiv) {
        currentDiv.style.display = 'none';
    }
}

// Create measurements list
function createMeasurementsList() {
    let listDiv = document.getElementById('measurementsList');
    if (!listDiv) {
        listDiv = document.createElement('div');
        listDiv.id = 'measurementsList';
        listDiv.innerHTML = `
            <div class="mt-3">
                <h6 class="fw-bold">Measurements (<span id="measurementsCount">0</span>)</h6>
                <div id="measurementsContainer" class="overflow-auto" style="max-height: 200px;"></div>
            </div>
        `;
        document.querySelector('.measurement-container').appendChild(listDiv);
    }
}

// Update measurements list
function updateMeasurementsList() {
    const countSpan = document.getElementById('measurementsCount');
    const container = document.getElementById('measurementsContainer');
    
    if (!countSpan || !container) return;
    
    countSpan.textContent = measurements.length;
    
    if (measurements.length === 0) {
        container.innerHTML = '<p class="text-muted small">No measurements yet</p>';
        return;
    }
    
    container.innerHTML = measurements.map((measurement, index) => `
        <div class="measurement-item p-2 mb-2 bg-light rounded d-flex justify-content-between align-items-center"
             data-measurement-id="${measurement.id}"
             onmouseenter="highlightMeasurement('${measurement.id}')"
             onmouseleave="unhighlightMeasurement('${measurement.id}')">
            <div>
                <div class="small text-muted">
                    ${measurement.type === 'length' ? '📏 Distance' : '📐 Area'} #${index + 1}
                </div>
                <div class="fw-bold">${measurement.value}</div>
            </div>
            <button class="btn btn-sm btn-outline-danger" onclick="removeMeasurement('${measurement.id}')">
                <i class="fa-solid fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Highlight measurement on hover
function highlightMeasurement(measurementId) {
    const measurement = measurements.find(m => m.id === measurementId);
    if (measurement) {
        measurement.feature.set('isHovered', true);
        measurementSource.changed();
    }
}

// Remove highlight
function unhighlightMeasurement(measurementId) {
    const measurement = measurements.find(m => m.id === measurementId);
    if (measurement) {
        measurement.feature.set('isHovered', false);
        measurementSource.changed();
    }
}

// Remove individual measurement
function removeMeasurement(measurementId) {
    const measurement = measurements.find(m => m.id === measurementId);
    if (measurement) {
        measurementSource.removeFeature(measurement.feature);
        measurements = measurements.filter(m => m.id !== measurementId);
        updateMeasurementsList();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for map to be initialized
    setTimeout(() => {
        if (typeof mapObj !== 'undefined' && mapObj) {
            initializeMeasurementTool();
        }
    }, 1000);
});

// Make functions globally available for HTML onclick handlers
window.highlightMeasurement = highlightMeasurement;
window.unhighlightMeasurement = unhighlightMeasurement;
window.removeMeasurement = removeMeasurement;
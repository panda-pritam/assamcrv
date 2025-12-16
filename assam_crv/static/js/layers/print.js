// Global variable to track selected layers for printing
if (typeof printSelectedLayers === 'undefined') {
    var printSelectedLayers = new Set(['basemap']); // Default to include basemap
}

// Functions to manage print layer selection
function addLayerToPrintSelection(layerName) {
    printSelectedLayers.add(layerName);
}

function removeLayerFromPrintSelection(layerName) {
    printSelectedLayers.delete(layerName);
}

function toggleLayerInPrintSelection(layerName, isSelected) {
    if (isSelected) {
        addLayerToPrintSelection(layerName);
    } else {
        removeLayerFromPrintSelection(layerName);
    }
}

// Function to populate layer selection in print modal
function populateLayerSelection() {
    const layerSelectionDiv = document.getElementById('layerSelectionList');
    if (!layerSelectionDiv) return;
    
    layerSelectionDiv.innerHTML = '';
    
    const layers = mapObj.getLayers().getArray();
    let hasLayers = false;
    
    // Add base layer option
    const baseLayerDiv = document.createElement('div');
    baseLayerDiv.className = 'form-check mb-2';
    baseLayerDiv.innerHTML = `
        <input class="form-check-input layer-checkbox" type="checkbox" id="print_basemap" data-layer="basemap" checked>
        <label class="form-check-label" for="print_basemap">
            <strong>Base Map</strong>
            <br><small class="text-muted">Background map layer</small>
        </label>
    `;
    layerSelectionDiv.appendChild(baseLayerDiv);
    hasLayers = true;
    
    // Add other layers
    layers.forEach((layer, index) => {
        const layerName = layer.get('name') || layer.get('title');
        const layerType = layer.get('type');
        
        // Skip base layers
        if (layerType === 'base' || !layerName) return;
        
        const layerDiv = document.createElement('div');
        layerDiv.className = 'form-check mb-2';
        
        const checkboxId = `print_layer_${index}`;
        const isVisible = layer.getVisible();
        
        layerDiv.innerHTML = `
            <input class="form-check-input layer-checkbox" type="checkbox" id="${checkboxId}" 
                   data-layer="${layerName}" ${isVisible ? 'checked' : ''}>
            <label class="form-check-label" for="${checkboxId}">
                <strong>${layerName}</strong>
                <br><small class="text-muted">Opacity: ${Math.round(layer.getOpacity() * 100)}%</small>
            </label>
        `;
        
        layerSelectionDiv.appendChild(layerDiv);
        hasLayers = true;
        
        // Add to print selection if visible
        if (isVisible) {
            addLayerToPrintSelection(layerName);
        }
    });
    
    if (!hasLayers) {
        layerSelectionDiv.innerHTML = '<p class="text-muted">No layers available</p>';
    }
    
    // Add event listeners to checkboxes
    const checkboxes = layerSelectionDiv.querySelectorAll('.layer-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const layerName = this.dataset.layer;
            toggleLayerInPrintSelection(layerName, this.checked);
        });
    });
}

// Function to update current map info in modal
function updateCurrentMapInfo() {
    const view = mapObj.getView();
    const zoom = view.getZoom();
    const center = view.getCenter();
    const resolution = view.getResolution();
    
    // Update zoom
    const zoomElement = document.getElementById('currentZoom');
    if (zoomElement) {
        zoomElement.textContent = zoom ? zoom.toFixed(2) : 'N/A';
    }
    
    // Update center
    const centerElement = document.getElementById('currentCenter');
    if (centerElement && center) {
        centerElement.textContent = `${center[1].toFixed(4)}, ${center[0].toFixed(4)}`;
    }
    
    // Update scale (approximate)
    const scaleElement = document.getElementById('currentScale');
    if (scaleElement && resolution) {
        const scale = Math.round(resolution * 96 * 39.37); // Approximate scale
        scaleElement.textContent = `1:${scale.toLocaleString()}`;
    }
}

// Event handlers for print modal
function initializePrintModalEvents() {
    // Show modal event
    const printModal = document.getElementById('customPrintModal');
    if (printModal) {
        printModal.addEventListener('show.bs.modal', function() {
            console.log('Print modal opening...');
            populateLayerSelection();
            updateCurrentMapInfo();
            createMapPreview();
        });
        
        // Hide modal event - cleanup loading states
        printModal.addEventListener('hide.bs.modal', function() {
            console.log('Print modal closing - cleaning up...');
            cleanupModalStates();
        });
    }
    
    // Function to cleanup modal states
    function cleanupModalStates() {
        // Hide preview loading spinner
        const previewLoading = document.getElementById('previewLoading');
        if (previewLoading) {
            previewLoading.classList.remove('show');
            previewLoading.style.display = 'none';
            previewLoading.style.visibility = 'hidden';
        }
        
        // Reset generate button
        const generateBtn = document.getElementById('generateCustomPrintBtn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fa-solid fa-file-pdf me-2"></i>Generate PDF';
            generateBtn.classList.remove('btn-success', 'btn-danger');
            generateBtn.classList.add('btn-primary');
        }
        
        // Clear preview map
        const previewDiv = document.getElementById('previewMapDiv');
        if (previewDiv) {
            previewDiv.innerHTML = '';
        }
        
        console.log('Modal cleanup completed');
    }
    
    // Custom print button event
    const customPrintBtn = document.getElementById('customPrintBtn');
    if (customPrintBtn) {
        customPrintBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('customPrintModal'));
            modal.show();
        });
    }
    
    // Select all layers
    const selectAllBtn = document.getElementById('selectAllLayers');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('#layerSelectionList .layer-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
                const layerName = checkbox.dataset.layer;
                addLayerToPrintSelection(layerName);
            });
        });
    }
    
    // Deselect all layers
    const deselectAllBtn = document.getElementById('deselectAllLayers');
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('#layerSelectionList .layer-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
                const layerName = checkbox.dataset.layer;
                removeLayerFromPrintSelection(layerName);
            });
        });
    }
    
    // Generate PDF button
    const generateBtn = document.getElementById('generateCustomPrintBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            generateCustomPDF();
        });
    }
}

// Custom PDF Generation Function with improved loading management
async function generateCustomPDF() {
    const generateBtn = document.getElementById('generateCustomPrintBtn');
    
    if (!generateBtn) {
        console.error('Generate button not found');
        return;
    }
    
    // Store original button state
    const originalText = generateBtn.innerHTML;
    const originalDisabled = generateBtn.disabled;
    
    // Function to reset button state
    const resetButton = () => {
        generateBtn.disabled = originalDisabled;
        generateBtn.innerHTML = originalText;
    };
    
    try {
        // Show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Generating PDF...';
        
        console.log('Starting PDF generation...');
        
        // Get print settings
        const settings = getPrintSettings();
        console.log('Print settings:', settings);
        
        // Get current map state
        const mapState = getCurrentMapState();
        console.log('Map state:', mapState);
        
        // Validate required data
        if (!mapState.center || !mapState.extent) {
            throw new Error('Invalid map state - missing center or extent');
        }
        
        // Create PDF
        const pdf = createPDFDocument(settings);
        
        // Add title
        addTitleToPDF(pdf, settings);
        
        // Calculate map area
        const mapArea = calculateMapArea(pdf, settings);
        
        // Update button text for different stages
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading base map...';
        
        // Always add base map for context
        await addBaseMapToPDF(pdf, mapArea, mapState, settings);
        
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Adding layers...';
        
        // Add selected layers
        await addLayersToPDF(pdf, mapArea, mapState, settings);
        
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Finalizing PDF...';
        
        // Add legend if requested
        if (settings.includeLegend) {
            addLegendToPDF(pdf, settings);
        }
        
        // Add scale bar if requested
        if (settings.includeScaleBar) {
            addScaleBarToPDF(pdf, mapState, settings);
        }
        
        // Add map info
        addMapInfoToPDF(pdf, mapState, settings);
        
        // Save PDF
        const fileName = `${settings.title.replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
        pdf.save(fileName);
        
        console.log('PDF generated successfully:', fileName);
        
        // Show success message briefly
        generateBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i>PDF Generated!';
        generateBtn.classList.add('btn-success');
        generateBtn.classList.remove('btn-primary');
        
        // Close modal after brief success display
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('customPrintModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reset button appearance
            generateBtn.classList.remove('btn-success');
            generateBtn.classList.add('btn-primary');
            resetButton();
        }, 1500);
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        
        // Show error state
        generateBtn.innerHTML = '<i class="fa-solid fa-exclamation-triangle me-2"></i>Error occurred';
        generateBtn.classList.add('btn-danger');
        generateBtn.classList.remove('btn-primary');
        
        // Show user-friendly error message
        const errorMessage = error.message || 'Unknown error occurred';
        alert(`Error generating PDF: ${errorMessage}\n\nPlease try again or check the console for more details.`);
        
        // Reset button after error display
        setTimeout(() => {
            generateBtn.classList.remove('btn-danger');
            generateBtn.classList.add('btn-primary');
            resetButton();
        }, 3000);
        
    }
}

// Get print settings from modal
function getPrintSettings() {
    return {
        paperSize: document.getElementById('paperSize').value,
        orientation: document.getElementById('orientation').value,
        title: document.getElementById('mapTitle').value || 'Map Print',
        includeLegend: document.getElementById('includeLegend').checked,
        includeScaleBar: document.getElementById('includeScaleBar').checked
    };
}

// Get current map state
function getCurrentMapState() {
    const view = mapObj.getView();
    const extent = view.calculateExtent(mapObj.getSize());
    
    return {
        center: view.getCenter(),
        zoom: view.getZoom(),
        resolution: view.getResolution(),
        extent: extent,
        projection: view.getProjection().getCode(),
        size: mapObj.getSize()
    };
}

// Create PDF document
function createPDFDocument(settings) {
    const { jsPDF } = window.jspdf;
    
    // Define paper sizes in mm
    const paperSizes = {
        a4: { width: 210, height: 297 },
        a3: { width: 297, height: 420 },
        letter: { width: 216, height: 279 }
    };
    
    const size = paperSizes[settings.paperSize];
    
    return new jsPDF({
        orientation: settings.orientation,
        unit: 'mm',
        format: [size.width, size.height]
    });
}

// Add title to PDF
function addTitleToPDF(pdf, settings) {
    const pageWidth = pdf.internal.pageSize.getWidth();
    
    pdf.setFontSize(16);
    pdf.setFont(undefined, 'bold');
    
    // Center the title
    const titleWidth = pdf.getTextWidth(settings.title);
    const titleX = (pageWidth - titleWidth) / 2;
    
    pdf.text(settings.title, titleX, 15);
    
    // Add generation date
    pdf.setFontSize(10);
    pdf.setFont(undefined, 'normal');
    const dateText = `Generated on: ${new Date().toLocaleString()}`;
    const dateWidth = pdf.getTextWidth(dateText);
    const dateX = (pageWidth - dateWidth) / 2;
    
    pdf.text(dateText, dateX, 22);
}

// Calculate map area on PDF
function calculateMapArea(pdf, settings) {
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    
    const margin = 20;
    const titleHeight = 30;
    const footerHeight = 20;
    
    return {
        x: margin,
        y: titleHeight,
        width: pageWidth - (2 * margin),
        height: pageHeight - titleHeight - footerHeight - margin
    };
}

// Enhanced base map to PDF function with proper scale controls
async function addBaseMapToPDF(pdf, mapArea, mapState, settings) {
    try {
        // Create a temporary canvas for base map
        const canvas = document.createElement('canvas');
        
        // Set canvas size based on map area (convert mm to pixels for better resolution)
        const dpi = 96;
        const mmToPixels = dpi / 25.4;
        
        canvas.width = Math.round(mapArea.width * mmToPixels * 2);
        canvas.height = Math.round(mapArea.height * mmToPixels * 2);
        
        // Create temporary map container
        const tempMapDiv = document.createElement('div');
        tempMapDiv.style.width = canvas.width + 'px';
        tempMapDiv.style.height = canvas.height + 'px';
        tempMapDiv.style.position = 'absolute';
        tempMapDiv.style.left = '-9999px';
        tempMapDiv.style.top = '-9999px';
        tempMapDiv.style.visibility = 'hidden';
        document.body.appendChild(tempMapDiv);
        
        // Create base layer with crossOrigin
        let tempBaseLayer;
        if (typeof baseLayer !== 'undefined' && baseLayer) {
            const baseLayerSource = baseLayer.getSource();
            if (baseLayerSource instanceof ol.source.OSM) {
                tempBaseLayer = new ol.layer.Tile({
                    source: new ol.source.OSM({
                        crossOrigin: 'anonymous'
                    })
                });
            } else if (baseLayerSource instanceof ol.source.XYZ) {
                tempBaseLayer = new ol.layer.Tile({
                    source: new ol.source.XYZ({
                        url: baseLayerSource.getUrls()[0],
                        crossOrigin: 'anonymous'
                    })
                });
            } else {
                tempBaseLayer = new ol.layer.Tile({
                    source: new ol.source.OSM({
                        crossOrigin: 'anonymous'
                    })
                });
            }
        } else {
            tempBaseLayer = new ol.layer.Tile({
                source: new ol.source.OSM({
                    crossOrigin: 'anonymous'
                })
            });
        }
        
        // Create temporary map with same view
        const tempMap = new ol.Map({
            target: tempMapDiv,
            layers: [tempBaseLayer],
            view: new ol.View({
                projection: mapState.projection,
                center: mapState.center,
                zoom: mapState.zoom,
                rotation: mapObj.getView().getRotation()
            }),
            controls: [] // Start with no controls, we'll add them selectively
        });
        
        // Add scale controls to the PDF map
        const scaleLineControl = new ol.control.ScaleLine({
            bar: true,
            text: true,
            minWidth: 100,
            units: 'metric',
            className: 'ol-scale-line-pdf'
        });
        
        const canvasScaleLineControl = new ol.control.CanvasScaleLine({
            strokeStyle: 'black',
            fillStyle: 'white',
            font: '12px Arial',
            textAlign: 'center',
            units: 'metric'
        });
        
        tempMap.addControl(scaleLineControl);
        tempMap.addControl(new ol.control.ZoomSlider());
        // tempMap.addControl(canvasScaleLineControl);
        
        // Wait for map to render completely
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                console.warn('Base map rendering timeout');
                resolve();
            }, 8000); // Increased timeout
            
            let renderCount = 0;
            const maxRenders = 3;
            
            const onRenderComplete = () => {
                renderCount++;
                if (renderCount >= maxRenders) {
                    clearTimeout(timeout);
                    tempMap.un('rendercomplete', onRenderComplete);
                    setTimeout(resolve, 1000); // Extra delay for scale controls
                }
            };
            
            tempMap.on('rendercomplete', onRenderComplete);
            
            // Force initial render
            tempMap.renderSync();
            
            // Trigger additional renders to ensure scale controls are drawn
            setTimeout(() => tempMap.renderSync(), 500);
            setTimeout(() => tempMap.renderSync(), 1000);
        });
        
        // Get map canvas and add to PDF
        const mapCanvas = tempMapDiv.querySelector('canvas');
        if (mapCanvas) {
            try {
                const imgData = mapCanvas.toDataURL('image/png', 0.9);
                pdf.addImage(imgData, 'PNG', mapArea.x, mapArea.y, mapArea.width, mapArea.height);
                console.log('Base map with scale controls added to PDF successfully');
            } catch (canvasError) {
                console.error('Error converting canvas to image:', canvasError);
                // Add a placeholder rectangle if canvas conversion fails
                pdf.setFillColor(240, 240, 240);
                pdf.rect(mapArea.x, mapArea.y, mapArea.width, mapArea.height, 'F');
                pdf.setTextColor(100, 100, 100);
                pdf.setFontSize(12);
                pdf.text('Base map could not be rendered', mapArea.x + 10, mapArea.y + 20);
            }
        } else {
            console.warn('No canvas found in temporary map');
            pdf.setFillColor(240, 240, 240);
            pdf.rect(mapArea.x, mapArea.y, mapArea.width, mapArea.height, 'F');
        }
        
        // Clean up
        document.body.removeChild(tempMapDiv);
        tempMap.setTarget(null);
        
    } catch (error) {
        console.error('Error adding base map to PDF:', error);
        // Add error placeholder
        pdf.setFillColor(255, 200, 200);
        pdf.rect(mapArea.x, mapArea.y, mapArea.width, mapArea.height, 'F');
        pdf.setTextColor(200, 0, 0);
        pdf.setFontSize(12);
        pdf.text('Error loading base map', mapArea.x + 10, mapArea.y + 20);
    }
}

// Enhanced addLayersToPDF function
async function addLayersToPDF(pdf, mapArea, mapState, settings) {
    console.log('Selected layers for PDF:', Array.from(printSelectedLayers));
    
    const selectedLayers = Array.from(printSelectedLayers).filter(name => name !== 'basemap');
    
    if (selectedLayers.length === 0) {
        console.log('No overlay layers selected for PDF');
        return;
    }
    
    // Get actual layer objects from the map
    const mapLayers = mapObj.getLayers().getArray();
    
    for (const layerName of selectedLayers) {
        const layer = mapLayers.find(l => {
            const name = l.get('name') || l.get('title');
            return name === layerName;
        });
        
        if (!layer) {
            console.warn(`Layer ${layerName} not found in map`);
            continue;
        }
        
        try {
            await addSingleLayerToPDF(pdf, layer, mapArea, mapState, settings);
        } catch (error) {
            console.error(`Error adding layer ${layerName} to PDF:`, error);
        }
    }
}

// Function to add a single layer to PDF
async function addSingleLayerToPDF(pdf, layer, mapArea, mapState, settings) {
    if (layer instanceof ol.layer.Tile && layer.getSource() instanceof ol.source.TileWMS) {
        await addWMSLayerToPDF(pdf, layer, mapArea, mapState, settings);
    } else if (layer instanceof ol.layer.Vector) {
        await addVectorLayerToPDF(pdf, layer, mapArea, mapState, settings);
    } else {
        console.log(`Layer type not supported for PDF: ${layer.constructor.name}`);
    }
}

// Add WMS layer to PDF
async function addWMSLayerToPDF(pdf, layer, mapArea, mapState, settings) {
    const source = layer.getSource();
    const params = source.getParams();
    
    const dpi = 96;
    const mmToPixels = dpi / 25.4;
    const width = Math.round(mapArea.width * mmToPixels);
    const height = Math.round(mapArea.height * mmToPixels);
    
    const wmsUrl = source.getUrls()[0] || source.getUrl();
    const requestParams = {
        SERVICE: 'WMS',
        VERSION: '1.1.1',
        REQUEST: 'GetMap',
        LAYERS: params.LAYERS,
        STYLES: params.STYLES || '',
        FORMAT: 'image/png',
        TRANSPARENT: 'true',
        SRS: mapState.projection,
        BBOX: mapState.extent.join(','),
        WIDTH: width,
        HEIGHT: height
    };
    
    const urlParams = new URLSearchParams(requestParams);
    const fullUrl = `${wmsUrl}?${urlParams.toString()}`;
    
    try {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        await new Promise((resolve, reject) => {
            img.onload = () => resolve();
            img.onerror = () => reject(new Error('Failed to load WMS image'));
            img.src = fullUrl;
            
            setTimeout(() => reject(new Error('WMS request timeout')), 10000);
        });
        
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        
        const imgData = canvas.toDataURL('image/png');
        pdf.addImage(imgData, 'PNG', mapArea.x, mapArea.y, mapArea.width, mapArea.height);
        
        console.log(`WMS layer added to PDF: ${layer.get('name')}`);
        
    } catch (error) {
        console.error(`Error loading WMS layer for PDF:`, error);
        pdf.setTextColor(150, 150, 150);
        pdf.setFontSize(8);
        pdf.text(`Layer "${layer.get('name')}" could not be loaded`, mapArea.x + 5, mapArea.y + 15);
    }
}

// Add legend to PDF
function addLegendToPDF(pdf, settings) {
    const pageWidth = pdf.internal.pageSize.getWidth();
    const legendX = pageWidth - 50;
    let legendY = 40;
    
    pdf.setFontSize(12);
    pdf.setFont(undefined, 'bold');
    pdf.text('Legend', legendX, legendY);
    
    legendY += 8;
    pdf.setFontSize(10);
    pdf.setFont(undefined, 'normal');
    
    const selectedLayers = Array.from(printSelectedLayers);
    selectedLayers.forEach((layerName, index) => {
        if (layerName !== 'basemap') {
            pdf.setFillColor(100 + (index * 50) % 200, 100, 150);
            pdf.rect(legendX, legendY - 2, 3, 3, 'F');
            pdf.text(layerName.substring(0, 20), legendX + 5, legendY);
            legendY += 6;
        }
    });
}

// Enhanced scale bar to PDF
function addScaleBarToPDF(pdf, mapState, settings) {
    const scaleBarX = 25;
    const scaleBarY = pdf.internal.pageSize.getHeight() - 30;
    
    // Calculate scale more accurately
    const resolution = mapState.resolution;
    const projection = ol.proj.get(mapState.projection);
    const pointResolution = ol.proj.getPointResolution(projection, resolution, mapState.center);
    const scale = Math.round(pointResolution * 96 * 39.37);
    
    // Draw enhanced scale bar
    pdf.setLineWidth(2);
    pdf.setDrawColor(0, 0, 0);
    
    // Main scale bar line
    pdf.line(scaleBarX, scaleBarY, scaleBarX + 30, scaleBarY);
    
    // End markers
    pdf.line(scaleBarX, scaleBarY - 3, scaleBarX, scaleBarY + 3);
    pdf.line(scaleBarX + 30, scaleBarY - 3, scaleBarX + 30, scaleBarY + 3);
    
    // Scale segments (every 10mm)
    for (let i = 10; i <= 20; i += 10) {
        pdf.line(scaleBarX + i, scaleBarY - 1, scaleBarX + i, scaleBarY + 1);
    }
    
    pdf.setFontSize(8);
    pdf.setFont(undefined, 'bold');
    pdf.text(`Scale 1:${scale.toLocaleString()}`, scaleBarX, scaleBarY + 8);
    
    // Add distance markers (approximate)
    const distance = Math.round((pointResolution * 30) / 1000); // Convert to km
    pdf.setFontSize(7);
    pdf.setFont(undefined, 'normal');
    pdf.text('0', scaleBarX - 2, scaleBarY - 5);
    pdf.text(`${distance}km`, scaleBarX + 25, scaleBarY - 5);
}

// Add map info to PDF
function addMapInfoToPDF(pdf, mapState, settings) {
    const pageHeight = pdf.internal.pageSize.getHeight();
    let infoY = pageHeight - 15;
    
    pdf.setFontSize(8);
    pdf.setFont(undefined, 'normal');
    
    const center = mapState.center;
    const infoText = `Center: ${center[1].toFixed(4)}, ${center[0].toFixed(4)} | Zoom: ${mapState.zoom.toFixed(2)} | Projection: ${mapState.projection}`;
    
    pdf.text(infoText, 20, infoY);
}

// Add Vector layer to PDF (simplified)
async function addVectorLayerToPDF(pdf, layer, mapArea, mapState, settings) {
    console.log(`Vector layer rendering not implemented yet: ${layer.get('name')}`);
    pdf.setTextColor(100, 100, 100);
    pdf.setFontSize(8);
    pdf.text(`Vector layer: ${layer.get('name')}`, mapArea.x + 5, mapArea.y + 25);
}

// Fixed map preview function with improved loading state management
function createMapPreview() {
    const previewDiv = document.getElementById('previewMapDiv');
    const loadingDiv = document.getElementById('previewLoading');
    
    if (!previewDiv || !loadingDiv) {
        console.warn('Preview elements not found');
        return;
    }
    
    // Show loading state with CSS class
    loadingDiv.style.display = 'flex';
    loadingDiv.style.visibility = 'visible';
    loadingDiv.classList.add('show');
    
    // Clear existing preview map
    previewDiv.innerHTML = '';
    
    // Function to hide loading with proper cleanup
    const hideLoading = () => {
        if (loadingDiv) {
            loadingDiv.classList.remove('show');
            loadingDiv.style.display = 'none';
            loadingDiv.style.visibility = 'hidden';
        }
    };
    
    // Set timeout to prevent infinite loading
    const loadingTimeout = setTimeout(() => {
        console.warn('Preview loading timeout - hiding spinner');
        hideLoading();
    }, 8000); // 8 second timeout
    
    setTimeout(() => {
        try {
            // Create base layer for preview
            let previewBaseLayer;
            if (typeof baseLayer !== 'undefined' && baseLayer) {
                const baseLayerSource = baseLayer.getSource();
                if (baseLayerSource instanceof ol.source.OSM) {
                    previewBaseLayer = new ol.layer.Tile({
                        source: new ol.source.OSM()
                    });
                } else if (baseLayerSource instanceof ol.source.XYZ) {
                    previewBaseLayer = new ol.layer.Tile({
                        source: new ol.source.XYZ({
                            url: baseLayerSource.getUrls()[0]
                        })
                    });
                } else {
                    previewBaseLayer = new ol.layer.Tile({
                        source: new ol.source.OSM()
                    });
                }
            } else {
                previewBaseLayer = new ol.layer.Tile({
                    source: new ol.source.OSM()
                });
            }
            
            // Get selected overlay layers only
            const selectedLayerNames = Array.from(printSelectedLayers).filter(name => name !== 'basemap');
            const overlayLayers = mapObj.getLayers().getArray()
                .filter(layer => {
                    const layerName = layer.get('name') || layer.get('title');
                    return selectedLayerNames.includes(layerName) && layer.getVisible();
                })
                .map(layer => {
                    // Clone the layer for preview
                    if (layer instanceof ol.layer.Tile) {
                        return new ol.layer.Tile({
                            source: layer.getSource(),
                            opacity: layer.getOpacity()
                        });
                    }
                    return layer;
                });
            
            // Create preview map
            const previewMap = new ol.Map({
                target: previewDiv,
                layers: [previewBaseLayer, ...overlayLayers],
                view: new ol.View({
                    projection: mapObj.getView().getProjection(),
                    center: mapObj.getView().getCenter(),
                    zoom: mapObj.getView().getZoom(),
                    rotation: mapObj.getView().getRotation()
                }),
                controls: []
            });
            
            // Add scale controls to preview
            previewMap.addControl(new ol.control.ScaleLine({
                bar: true,
                text: true,
                minWidth: 80,
                units: 'metric'
            }));
            
            previewMap.addControl(new ol.control.CanvasScaleLine({
                strokeStyle: 'black',
                fillStyle: 'white',
                font: '10px Arial'
            }));
            
            // Improved loading completion handler
            let isLoadingComplete = false;
            let renderCount = 0;
            const maxRenderCount = 3; // Allow up to 3 renders
            
            const completeLoading = () => {
                if (!isLoadingComplete) {
                    isLoadingComplete = true;
                    clearTimeout(loadingTimeout);
                    hideLoading();
                    console.log('Preview map loaded successfully');
                }
            };
            
            const handleRenderComplete = () => {
                renderCount++;
                console.log(`Preview render complete: ${renderCount}/${maxRenderCount}`);
                
                // Complete loading after sufficient renders or timeout
                if (renderCount >= maxRenderCount) {
                    previewMap.un('rendercomplete', handleRenderComplete);
                    setTimeout(completeLoading, 1000); // Small delay to ensure rendering
                }
            };
            
            // Handle loading errors
            const handleLoadError = (event) => {
                console.warn('Preview map load error:', event);
                if (!isLoadingComplete) {
                    completeLoading();
                }
            };
            
            // Attach event listeners
            previewMap.on('rendercomplete', handleRenderComplete);
            previewMap.on('error', handleLoadError);
            
            // Force initial render
            previewMap.renderSync();
            
            // Backup completion trigger
            setTimeout(() => {
                if (!isLoadingComplete) {
                    console.log('Backup loading completion triggered');
                    completeLoading();
                }
            }, 6000);
            
        } catch (error) {
            console.error('Error creating map preview:', error);
            clearTimeout(loadingTimeout);
            hideLoading();
            
            // Show error message in preview area
            if (previewDiv) {
                previewDiv.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-danger"><i class="fa-solid fa-exclamation-triangle me-2"></i>Preview unavailable</div>';
            }
        }
    }, 200); // Slight delay to ensure DOM is ready
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Initialize print modal events
    initializePrintModalEvents();
    
    // Add event listener for custPrint button
    const custPrintBtn = document.getElementById('custPrint');
    if (custPrintBtn) {
        custPrintBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('customPrintModal'));
            modal.show();
        });
    }
});
let layersData = [];
let printSelectedLayers = new Set();  // ✅ initialize print selection set

document.addEventListener('DOMContentLoaded', async () => {
    getAllTheLayers();
});

async function getAllTheLayers() {
    try {
        let api_res = await fetch("/api/getLayers/", {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        let json_res = await api_res.json();
        console.log(json_res);

        if (json_res) {
            let layers = json_res;
            layersData = layers;
            let layerDiv = document.getElementById('accordionLayerDiv');

            layers.forEach((layer, index) => {
                let layerAccordionItem = document.createElement('div');
                layerAccordionItem.classList.add('accordion-item', 'mb-0');
                
                // Check if layer should be shown by default
                const isDefaultLayer = layer.layer_name === 'district_boundary' || layer.layer_name === 'state_boundary';
                const checkedAttr = isDefaultLayer ? 'checked' : '';
                const expandedAttr = isDefaultLayer ? 'false' : 'false';
                const collapseClass = isDefaultLayer ? '' : '';
                const buttonClass = isDefaultLayer ? 'accordion-button collapsed' : 'accordion-button collapsed';

                layerAccordionItem.innerHTML = `
                    <h2 class="accordion-header position-relative">
                        <button class="${buttonClass} d-flex justify-content-between align-items-center" 
                                type="button" data-bs-toggle="collapse" 
                                data-bs-target="#collapse${layer.uuid}" 
                                aria-expanded="${expandedAttr}" 
                                aria-controls="collapse${layer.uuid}"
                                id="accordion-btn-${layer.uuid}">
                              <span class="layer_title_span">${layer.title}</span>
                        </button>
                        <div class="d-flex align-items-center accordion_layer_checkbox ">
                            <input class="form-check-input" type="checkbox" 
                                   id="${layer.uuid}" 
                                   onchange="toggleLayer(this.checked, ${index})" 
                                   onclick="event.stopPropagation();" ${checkedAttr}>
                        </div>
                        <button class="layer-zoom-btn" 
                                id="zoom-btn-${layer.uuid}"
                                title="Zoom to layer"
                                onclick="event.stopPropagation(); zoomToLayer('${layer.workspace}', '${layer.layer_name}')">
                            <i class="fa-solid fa-magnifying-glass srchIcn"></i>
                        </button>
                    </h2>
                    <div id="collapse${layer.uuid}" class="accordion-collapse collapse ${collapseClass}" 
                         data-bs-parent="#accordionLayerDiv">
                        <div class="accordion-body accSpcng">
                            <div class="mb-1">
                                <label for="opacity${layer.layer_name}" class="form-label">Opacity</label>
                                <div class="d-flex align-items-center">
                                    <input type="range" class="form-range me-3" 
                                           id="opacity${layer.uuid}" 
                                           min="0" max="100" value="100" 
                                           onchange="changeOpacity(this.value, ${index})">
                                    <span id="opacityValue${layer.uuid}" class="badge bg-secondary">100%</span>
                                </div>
                            </div>
                            <!-- Legend Image -->
                            <div class="mb-2">
                                <label class="form-label">Legend</label><br>
                                <img src="${geoserverURL}/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=${layer.workspace}:${layer.layer_name}" 
                                    alt="Legend for ${layer.layer_name}" class="img-fluid border">
                            </div>
                        </div>
                    </div>
                `;

                layerDiv.appendChild(layerAccordionItem);
                
                // Auto-load default layers
                if (isDefaultLayer) {
                    addLayerToMap(layer);
                    const accordionBtn = document.getElementById(`accordion-btn-${layer.uuid}`);
                    const zoomBtn = document.getElementById(`zoom-btn-${layer.uuid}`);
                    accordionBtn.classList.add('show');
                    zoomBtn.classList.add('show');
                    addLayerToPrintSelection(`${layer.id}_${layer.layer_name}_${layer.workspace}`);
                }
            });
        }
    } catch (error) {
        console.log(error);
    }
}

// Add layer to print selection
function addLayerToPrintSelection(layerName) {
    printSelectedLayers.add(layerName);
    console.log(`Layer ${layerName} added to print selection`);
}

// Remove layer from print selection
function removeLayerFromPrintSelection(layerName) {
    printSelectedLayers.delete(layerName);
    console.log(`Layer ${layerName} removed from print selection`);
}

function toggleLayer(value, layerIndex) {
    let layer = layersData[layerIndex];
    const accordionBtn = document.getElementById(`accordion-btn-${layer.uuid}`);
    const zoomBtn = document.getElementById(`zoom-btn-${layer.uuid}`);

    if (value) {
        addLayerToMap(layer);
        accordionBtn.classList.add('show');
        zoomBtn.classList.add('show');
        addLayerToPrintSelection(`${layer.id}_${layer.layer_name}_${layer.workspace}`);
    } else {
        removeLayerFromMap(`${layer.id}_${layer.layer_name}_${layer.workspace}`);
        accordionBtn.classList.remove('show');
        zoomBtn.classList.remove('show');

        // collapse if open
        let collapseElement = document.getElementById(`collapse${layer.uuid}`);
        if (collapseElement && collapseElement.classList.contains('show')) {
            let accordion = new bootstrap.Collapse(collapseElement, { hide: true });
        }
        removeLayerFromPrintSelection(`${layer.id}_${layer.layer_name}_${layer.workspace}`);
    }
}

function changeOpacity(value, layerIndex) {
    let layer = layersData[layerIndex];
    console.log(value, layer);
    document.getElementById(`opacityValue${layer.uuid}`).innerText = `${value}%`;
    changeLayerOpacity(`${layer.id}_${layer.layer_name}_${layer.workspace}`, value / 100);
}

async function zoomToLayer(workspace, layerName) {
    const url = `${geoserverURL}/${workspace}/wms?service=WMS&version=1.3.0&request=GetCapabilities`;

    try {
        const response = await fetch(url);
        const text = await response.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, "application/xml");
        const layers = xml.getElementsByTagName("Layer");

        for (let i = 0; i < layers.length; i++) {
            const name = layers[i].getElementsByTagName("Name")[0];
            if (name && name.textContent === `${layerName}`) {
                const bbox = layers[i].getElementsByTagName("EX_GeographicBoundingBox")[0];
                if (bbox) {
                    const west = parseFloat(bbox.getElementsByTagName("westBoundLongitude")[0].textContent);
                    const east = parseFloat(bbox.getElementsByTagName("eastBoundLongitude")[0].textContent);
                    const south = parseFloat(bbox.getElementsByTagName("southBoundLatitude")[0].textContent);
                    const north = parseFloat(bbox.getElementsByTagName("northBoundLatitude")[0].textContent);

                    const extent = [west, south, east, north];
                    console.log("extent :", extent);

                    mapObj.getView().fit(extent, {
                        padding: [50, 50, 50, 50],
                        duration: 1000
                    });
                    return;
                }
            }
        }
        alert("Bounding box not found for the selected layer.");
    } catch (error) {
        console.error("Error fetching GetCapabilities:", error);
        alert("Failed to zoom to layer.");
    }
}

// Get all selected layers for printing
function getSelectedLayersForPrint() {
    return Array.from(printSelectedLayers);
}

// Clear all selected layers
function clearPrintSelection() {
    printSelectedLayers.clear();
    console.log('Print selection cleared');
}

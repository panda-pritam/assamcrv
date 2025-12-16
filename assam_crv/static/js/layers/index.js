let layerPanelOpen = false;
let toggleLayerPanelBtn = document.getElementById('toggleLayerPanelBtn');
let layerDiv = document.getElementById('layerDiv');
let LayerDivCloseButton = document.getElementById('LayerDivCloseButton');

// base map
let isBaseMapDivOpen = false;
let baseMapTogglerBtn = document.getElementById('baseMapTogglerBtn');
let baseMapOptionsDiv = document.getElementById('baseMapOptionsDiv');
let baseMapDivCloseButton = document.getElementById('baseMapDivCloseButton');

// measurement
let isMeasurementDivOpen = false;
let measurementTogglerBtn = document.getElementById('measurementTogglerBtn');
let measurementOptionsDiv = document.getElementById('measurementOptionsDiv');
let measurementDivCloseButton = document.getElementById('measurementDivCloseButton');


document.addEventListener("DOMContentLoaded", () => {
     colorChange('map');
     toggleLayerPanelBtn.addEventListener('click', toggleVisibility);
     LayerDivCloseButton.addEventListener('click', toggleVisibility);

     // base map
     baseMapTogglerBtn.addEventListener('click', toggleBaseMapVisibility);
     baseMapDivCloseButton.addEventListener('click', toggleBaseMapVisibility);

     // measurement
     measurementTogglerBtn.addEventListener('click', toggleMeasurementVisibility);
     measurementDivCloseButton.addEventListener('click', toggleMeasurementVisibility);

     var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
     tooltipTriggerList.forEach(function (tooltipTriggerEl) {
          new bootstrap.Tooltip(tooltipTriggerEl);
     });

     initializeSelect2('Layer_district', "Select District")
     initializeSelect2('layer_village', "Select Village")

     loadDistrictsAndVillages('Layer_district', 'layer_village')

     // Add change event handlers to read attributes
     $('#Layer_district').on('change', function () {
          const selectedOption = this.options[this.selectedIndex];
          const lat = selectedOption?.getAttribute('data-lat') || "26.2006";
          const lng = selectedOption?.getAttribute('data-lng') || "92.9376";

          console.log('District selected:', { id: this.value, lat, lng });
          zoomToLatLon(lat, lng, 12)
          reloadLayersWithFilter()
     });

     $('#layer_village').on('change', function () {
          const selectedOption = this.options[this.selectedIndex];
          const lat = selectedOption.getAttribute('data-lat') || "26.2006";
          const lng = selectedOption.getAttribute('data-lng') || "92.9376";
          console.log('Village selected:', { id: this.value, lat, lng });
          zoomToLatLon(lat, lng, 14)
          reloadLayersWithFilter()
     });
});

function toggleVisibility() {
     // Close other panels
     if (isBaseMapDivOpen) {
          toggleBaseMapVisibility();
     }
     if (isMeasurementDivOpen) {
          toggleMeasurementVisibility();
     }
     
     if (!layerPanelOpen) {
          layerDiv.classList.add('show');
          toggleLayerPanelBtn.style.display = 'none';
          layerPanelOpen = true;
     } else {
          layerDiv.classList.remove('show');
          setTimeout(() => {
               toggleLayerPanelBtn.style.display = 'block';
          }, 300); // match transition duration
          layerPanelOpen = false;
     }
}

function toggleBaseMapVisibility() {
     // Close other panels
     if (isMeasurementDivOpen) {
          toggleMeasurementVisibility();
     }
     if (layerPanelOpen) {
          toggleVisibility();
     }
     
     if (!isBaseMapDivOpen) {
          baseMapOptionsDiv.classList.add('show');
          baseMapTogglerBtn.style.display = 'none';
          isBaseMapDivOpen = true;
     } else {
          baseMapOptionsDiv.classList.remove('show');
          setTimeout(() => {
               baseMapTogglerBtn.style.display = 'flex';
          }, 300); // match transition duration
          isBaseMapDivOpen = false;
     }
}

function toggleMeasurementVisibility() {
    
     
     if (!isMeasurementDivOpen) {
          measurementOptionsDiv.style.display = 'block';
          setTimeout(() => {
               // measurementOptionsDiv.classList.add('show');
               measurementOptionsDiv.style.display = 'block';
          }, 10);
          measurementTogglerBtn.style.display = 'none';
          isMeasurementDivOpen = true;
     } else {
          measurementOptionsDiv.classList.remove('show');
          setTimeout(() => {
               measurementOptionsDiv.style.display = 'none';
               measurementTogglerBtn.style.display = 'flex';
          }, 10);
          isMeasurementDivOpen = false;
     }
}

// Loader functions
function showLoader() {
    if (document.getElementById('loader')) {
        document.getElementById('loader').classList.remove('d-none');
    }
}

function hideLoader() {
    if (document.getElementById('loader')) {
        document.getElementById('loader').classList.add('d-none');
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    colorChange('vdmp_dashboard');

    // Initialize Select2 dropdowns

    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('village', gettext('Select Villages'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('circle', gettext('Select Circle'));
    initializeSelect2('status', gettext('Select Status'));
    // Load districts and villages using common function
    // loadDistrictsAndVillages('district', 'village');





    // Get user location data from hidden elements
    const userDistrictId = document.getElementById('userDistrictId')?.value || '';
    const userCircleId = document.getElementById('userCircleId')?.value || '';
    const userGramPanchayatId = document.getElementById('userGramPanchayatId')?.value || '';
    const userVillageId = document.getElementById('userVillageId')?.value || '';

    await setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village', userDistrictId, userCircleId, userGramPanchayatId, userVillageId);

    // Helper to get current filter values
    function getFilters() {
        return {
            district_id: $('#district').val() || '',
            village_id: $('#village').val() || '',
            circle_id: $('#circle').val() || "",
            gram_panchayat_id: $('#gram_panchayat').val() || "",

        };
    }

    // Load initial data
    await loadvdmpsummary(getFilters());
    await vdmp_updateSummaryText();

    // Add event listeners for filter changes
    $('#district').on('change', async () => {
        await loadvdmpsummary(getFilters());
        await vdmp_updateSummaryText();
    });
    $('#village').on('change', async () => {
        await loadvdmpsummary(getFilters());
        await vdmp_updateSummaryText();
        // toggleDownloadButton();
    });
    $('#circle').on('change', async () => {
        await loadvdmpsummary(getFilters());
        await vdmp_updateSummaryText();
    });
    $('#gram_panchayat').on('change', async () => {
        await loadvdmpsummary(getFilters());
        await vdmp_updateSummaryText();
    });

    // Upload and delete button handlers
    $('#uploadnewdata').on('click', handleUpload);
    $('#deletedata').on('click', handleDelete);

    // Download report event listener
    $('#download_report_VDMP_Dashboard').on('click', downloadReport);

    // async function downloadReport() {
    //     const button = $('#download_report_VDMP_Dashboard');
    //     const originalContent = button.html();
    //     $('#loaderOverlay').show();

    //     // Show loader
    //     button.html('<span class="spinner-border spinner-border-sm me-2"></span>Generating...');
    //     button.prop('disabled', true);

    //     const village_id = $('#village').val() || '';
    //     const url = `/api/download_report?village_id=${village_id}`;

    //     // Create an AbortController
    //     const controller = new AbortController();
    //     const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 10 minutes

    //     try {
    //         const response = await fetch(url, {
    //             method: 'GET',
    //             headers: {
    //                 'X-CSRFToken': getCSRFToken()
    //             },
    //             credentials: 'include',
    //             signal: controller.signal // attach signal to fetch
    //         });

    //         if (response.ok) {
    //             const blob = await response.blob();
    //             const pdfUrl = URL.createObjectURL(blob);
    //             window.open(pdfUrl, '_blank');
    //         } else {
    //             throw new Error('Failed to generate report');
    //         }
    //     } catch (error) {
    //         if (error.name === 'AbortError') {
    //             alert('Request timed out after 10 minutes. Please try again.');
    //         } else {
    //             console.error('Error downloading report:', error);
    //             alert('Error generating report. Please try again.');
    //         }
    //     } finally {
    //         clearTimeout(timeoutId); // clear the timeout
    //         $('#loaderOverlay').hide();
    //         button.html(originalContent);
    //         button.prop('disabled', false);
    //     }
    // }

function downloadReport() {
    const village_id = $('#village').val() || '';
    const url = `/api/download_report?village_id=${village_id}`;

    // Show loader
    $('#loaderOverlay').show();

    // Open PDF in new tab
    const newTab = window.open(url, '_blank');

    if (!newTab) {
        alert('Please allow popups for this website to download the report.');
        $('#loaderOverlay').hide();
    }
        $('#loaderOverlay').hide();

}


    // -----------------------------------------------------------------------------------------------

});



async function loadvdmpsummary(params = {}) {
    try {
        showLoader();
        let url = '/api/get_household_summary_data';
        const query = new URLSearchParams(params).toString();
        if (query) {
            url += `?${query}`;
        }
        const response = await fetch(url);
        const data = await response.json();
        updateVillageSummary(data);
    } catch (error) {
        console.error('Error loading village summary data:', error);
    } finally {
        hideLoader();
    }
}

async function handleUpload() {
    const dataType = document.getElementById('dataType').value;
    const fileInput = document.getElementById('fileInput');
    const button = document.getElementById('uploadnewdata');

    if (!dataType || !fileInput.files[0]) {
        alert('Please select data type and file');
        return;
    }

    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
    button.disabled = true;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('data_type', dataType);

    try {
        const response = await fetch('/api/upload_data_vdmp/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const result = await response.json();
        if (response.ok) {
            alert(`Success! ${result.records_created} records created`);
            fileInput.value = '';
            document.getElementById('dataType').value = '';
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        alert('Upload failed');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

async function handleDelete() {
    const dataType = document.getElementById('deletedataType').value;
    const villageId = document.getElementById('village').value;
    const button = document.getElementById('deletedata');

    if (!dataType || !villageId) {
        alert('Please select data type and village');
        return;
    }

    if (!confirm('Are you sure? This action cannot be undone.')) {
        return;
    }

    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deleting...';
    button.disabled = true;

    const formData = new FormData();
    formData.append('data_type', dataType);
    formData.append('village_id', villageId);

    try {
        const response = await fetch('/api/delete_vdmp_data/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const result = await response.json();
        if (response.ok) {
            alert(result.message);
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        alert('Delete failed');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

/**
 * VDMP Dashboard Data Update Function
 * 
 * Updates all dashboard elements with data received from the API.
 * Handles multiple data categories and applies appropriate formatting.
 * 
 * Data Processing Steps:
 * 1. Update demographic summary elements
 * 2. Handle special cases (lactating women)
 * 3. Update asset summary with formatted values
 * 4. Update hazard data with unit conversions
 * 5. Update vulnerability metrics with appropriate units
 * 
 * @param {Object} data - Summary data from get_household_summary_data API
 */
function updateVillageSummary(data) {
    // STEP 1: Define core demographic and facility data fields
    // These fields are updated directly with numeric values and thousand separators
    const keys = [
        // Demographic Summary
        'male_population',           // Male population count
        'female_population',         // Female population count
        'total_population',          // Total population (male + female)
        'population_bl_six',         // Children below 6 years
        'senior_citizens',           // Senior citizens count
        'total_disabled',            // Disabled persons count
        'total_households',          // Total household count

        // Vulnerable Populations
        'priority_households',       // Priority households for assistance
        'bpl_households',           // Below Poverty Line households
        'pregnant_lactating',       // Pregnant women count

        // Livestock Assets
        'big_cattles',              // Large livestock count
        'small_cattles',            // Small livestock count

        // Critical Facilities
        'school',                   // School facilities count
        'religous_places',          // Religious places count
        'anganwadi',               // Anganwadi centers count

        // Housing Types
        'kachcha_houses',          // Traditional/temporary houses
        'semi_pucca_houses',       // Semi-permanent houses
        'pucca_houses' ,           // Permanent/concrete houses
        'bridge_count',
        'river_erosion_length_km',
        'poultry_animals',
        'commercial_buildings',
        'transformer_count'
    ];

    // STEP 2: Update all basic numeric fields with thousand separators
    keys.forEach(key => {
        const el = document.getElementById(key);
        if (el) {
            const value = data[key] ?? 0;
            el.textContent = value.toLocaleString();  // Format with commas
        }
    });

    // STEP 3: Handle special case - lactating women (separate display element)
    const lactatingEl = document.getElementById('lactating_women');
    if (lactatingEl && data.lactating_women !== undefined) {
        lactatingEl.textContent = (data.lactating_women ?? 0).toLocaleString();
    }

    // STEP 4: Update Asset Summary section with specialized formatting
    // Maps API data to asset display elements with appropriate units
    const assetFields = {
        'total_road_length': (val) => `${val} km`,              // Road length in kilometers
        'big_cattles_asset': (val) => val.toLocaleString(),     // Livestock count
        'small_cattles_asset': (val) => val.toLocaleString(),   // Livestock count
        
        'kachcha_houses_asset': (val) => val.toLocaleString(),  // House count
        'semi_pucca_houses_asset': (val) => val.toLocaleString(), // House count
        'pucca_houses_asset': (val) => val.toLocaleString(),    // House count
        'anganwadi_asset': (val) => val.toLocaleString(),       // Facility count
        'school_asset': (val) => val.toLocaleString(),          // Facility count
        'religous_places_asset': (val) => val.toLocaleString(),  // Facility count\
        'commercial_buildings': (val) => val.toLocaleString(),
        'industrial_buildings': (val) => val.toLocaleString(),
        'overhead_water_tank': (val) => val.toLocaleString(),
        'transformer': (val) => val.toLocaleString(),
        'sluice_gate': (val) => val.toLocaleString(),
    };

    // Update asset elements by mapping field IDs to data keys
    Object.entries(assetFields).forEach(([fieldId, formatter]) => {
        const el = document.getElementById(fieldId);
        if (el) {
            const dataKey = fieldId.replace('_asset', '');  // Remove '_asset' suffix
            const value = data[dataKey] ?? 0;
            el.textContent = formatter(value);
        }
    });

    // STEP 5: Update Hazard & Vulnerability section - Flood depth data
    // Displays flood statistics with feet units (converted from meters in API)
    const hazardFields = {
        'avg_flood_depth': (val) => `${val} feet`,  // Average flood depth
        'max_flood_depth': (val) => `${val} feet`   // Maximum flood depth
    };

    Object.entries(hazardFields).forEach(([fieldId, formatter]) => {
        const el = document.getElementById(fieldId);
        if (el) {
            const value = data[fieldId] ?? 0;
            el.textContent = formatter(value);
        }
    });

    // STEP 6: Update Vulnerable Assets section with mixed units
    // Houses are counted, roads are measured in kilometers
    const vulnerabilityFields = {
        'flood_vulnerable_houses': (val) => val.toLocaleString(),    // House count
        'erosion_vulnerable_houses': (val) => val.toLocaleString(),  // House count
        'flood_vulnerable_roads': (val) => `${val} km`,              // Road length in km
        'erosion_vulnerable_roads': (val) => `${val} km`             // Road length in km
    };

    Object.entries(vulnerabilityFields).forEach(([fieldId, formatter]) => {
        const el = document.getElementById(fieldId);
        if (el) {
            const value = data[fieldId] ?? 0;
            el.textContent = formatter(value);
        }
    });
}


function toggleDownloadButton() {
    const villageSelect = $('#village').val();
    const downloadContainer = $('#download_report_container');
    if (villageSelect && villageSelect !== '') {
        downloadContainer.removeClass('d-none');
    } else {
        downloadContainer.addClass('d-none');
    }
}


async function vdmp_updateSummaryText() {
    console.log("vdmp_updateSummaryText called");
    const districtId = $('#district').val();
    const circleId = $('#circle').val();
    const gramPanchayatId = $('#gram_panchayat').val();
    const villageId = $('#village').val();

    let summaryText = '';
    const downloadContainer = $('#download_report_container');

    try {
        // Build API URL
        let url = '/api/count_of_villages_with_survey';
        const params = new URLSearchParams();

        if (villageId) {
            params.append('village_id', villageId);
        } else if (gramPanchayatId) {
            params.append('gram_panchayat_id', gramPanchayatId);
        } else if (circleId) {
            params.append('circle_id', circleId);
        } else if (districtId) {
            params.append('district_id', districtId);
        }

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        // Call API
        const response = await fetch(url);
        const data = await response.json();

        // ✅ Toggle download button based on has_data
        if (villageId) {
            if (data.has_data) {
                summaryText = `Summary: District: <strong>${data.district_val}</strong> Village: <strong>${data.village_val}</strong>`;
                downloadContainer.removeClass('d-none'); // show button
            } else {
                summaryText = `Summary: <strong>${data.district_val}</strong> : This village has no data`;
                downloadContainer.addClass('d-none'); // hide button
            }
        } else {
            summaryText = `Summary: District: <strong>${data.district_val}</strong> | Villages : <strong>${data.village_val}</strong>`;
            downloadContainer.addClass('d-none'); // hide when not village-level
        }

    } catch (error) {
        console.error('Error fetching summary:', error);
        summaryText = '⚠️ Failed to load summary';
        $('#download_report_container').addClass('d-none'); // hide on error
    }

    // Update UI
    const summaryElement = document.querySelector('.summary-line span');
    if (summaryElement) {
        summaryElement.innerHTML = summaryText;
    }
}

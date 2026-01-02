let districtsTable, circlesTable, gramPanchayatsTable, villagesTable;
let editingId = null;
let entityType = null;

document.addEventListener('DOMContentLoaded', async function () {

    colorChange('village_profile','village_profile_admin');
    // Show the first tab by default
    showTab('district');

    // Initialize Select2 for filters
    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('circle', gettext('Select Circle'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));

    // Setup location selectors
    setupLocationSelectors('district', 'circle', 'gram_panchayat');

    // Define columns for each table
    const districtColumns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("Code"), width: "10%" },
        { title: gettext("District") },
        { title: gettext("District (Assamese)") },
        { title: gettext("District (Bengali)") },
        { title: gettext("Latitude") },
        { title: gettext("Longitude ") },
        { title: gettext("Actions"), width: "10%" }
    ];
    
    const circleColumns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("District"), width: "20%" },
        { title: gettext("Circle"), width: "25%" },
        { title: gettext("Circle (Assamese)"), width: "20%" },
        { title: gettext("Circle (Bengali)"), width: "20%" },
        { title: gettext("Actions"), width: "10%" }
    ];
    
    const gpColumns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("District"), width: "15%" },
        { title: gettext("Circle"), width: "15%" },
        { title: gettext("Gram Panchayat"), width: "20%" },
        { title: gettext("Gram Panchayat (Assamese)"), width: "15%" },
        { title: gettext("Gram Panchayat (Bengali)"), width: "15%" },
        { title: gettext("Actions"), width: "10%" }
    ];
    
    const villageColumns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("Code"), width: "5%" },
        { title: gettext("District"), width: "12%" },
        { title: gettext("Circle"), width: "12%" },
        { title: gettext("Gram Panchayat"), width: "12%" },
        { title: gettext("Village"), width: "12%" },
        { title: gettext("Village (Assamese)"), width: "12%" },
        { title: gettext("Village (Bengali)"), width: "12%" },
        { title: gettext("Latitude"), width: "25%" },
        { title: gettext("Longitude "), width: "25%" },
        { title: gettext("Actions"), width: "10%" }
    ];

    // Initialize DataTables using the utility function
    districtsTable = initializeDataTable('districts_table', districtColumns, {}, true);
    circlesTable = initializeDataTable('circles_table', circleColumns, {}, true);
    gramPanchayatsTable = initializeDataTable('gram_panchayats_table', gpColumns, {}, true);
    villagesTable = initializeDataTable('villages_table', villageColumns, {}, true);

    // Load initial data
    loadDistricts();
    loadGramPanchayats();
    loadCircles();
    loadVillages();
    updateSummaryText(true);
       // Listeners
       $('#district, #circle, #gram_panchayat, #village').on('change', () => {
       
        updateSummaryText(true);
    });
    // Set up event listeners for filters
    $('#district').on('change', function() {
        const districtId = $(this).val();
        if (districtId) {
            loadCircles({ district_id: districtId });
            loadGramPanchayats({ district_id: districtId });
            loadVillages({ district_id: districtId });
        }else{
            loadGramPanchayats();
            loadCircles();
            loadVillages();
        }
    });

    $('#circle').on('change', function() {
        const circleId = $(this).val();
        if (circleId) {
            loadGramPanchayats({ circle_id: circleId });
            loadVillages({ circle_id: circleId });
        }else{
            loadGramPanchayats();
            loadVillages();
        }
    });

    $('#gram_panchayat').on('change', function() {
        const gpId = $(this).val();
        if (gpId) {
            loadVillages({ gram_panchayat_id: gpId });
        }else{
            loadVillages();
        }
    });

    // Form submissions
    $('#districtForm').on('submit', function(e) {
        e.preventDefault();
        saveDistrict();
    });

    $('#circleForm').on('submit', function(e) {
        e.preventDefault();
        saveCircle();
    });

    $('#gramPanchayatForm').on('submit', function(e) {
        e.preventDefault();
        saveGramPanchayat();
    });

    $('#villageForm').on('submit', function(e) {
        e.preventDefault();
        saveVillage();
    });

    // We've replaced these click handlers with direct function calls through the action buttons
    // The edit functions are now defined separately: editDistrict, editCircle, editGramPanchayat, editVillage

    // CSV Upload form submission
    $('#csvUploadForm').on('submit', function(e) {
        e.preventDefault();
        uploadCsvFile();
    });

    // Reset modals on close
    $('#districtModal').on('hidden.bs.modal', function() {
        resetModal('district');
    });

    $('#circleModal').on('hidden.bs.modal', function() {
        resetModal('circle');
    });

    $('#gramPanchayatModal').on('hidden.bs.modal', function() {
        resetModal('gram_panchayat');
    });

    $('#villageModal').on('hidden.bs.modal', function() {
        resetModal('village');
    });

    $('#csvUploadModal').on('hidden.bs.modal', function() {
        resetCsvUploadModal();
    });

    // Load districts for dropdowns
    loadDistrictsForDropdown();
});

// CSV Upload Functions
function resetCsvUploadModal() {
    $('#csvUploadForm')[0].reset();
    $('#uploadCsvBtn').prop('disabled', false).text(gettext('Upload'));
}

function uploadCsvFile() {
    const fileInput = document.getElementById('csvFile');
    const updateExisting = document.getElementById('updateExisting').checked;
    
    if (!fileInput.files[0]) {
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: gettext('Please select a CSV file')
        });
        return;
    }

    // Check file type - only allow CSV files
    const fileName = fileInput.files[0].name;
    const fileExtension = fileName.split('.').pop().toLowerCase();
    
    if (fileExtension !== 'csv') {
        Swal.fire({
            icon: 'error',
            title: gettext('Invalid File Type'),
            text: gettext('Only CSV files are allowed. Please convert your .xlsx or .xls file to CSV format and try again.')
        });
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('update_existing', updateExisting);
    formData.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val());

    // Show loading state
    $('#uploadCsvBtn').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> ' + gettext('Uploading...'));

    fetch('/en/api/add_district_crlcle_gp_vill_by_csv', {
        method: 'POST',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            Swal.fire({
                icon: 'success',
                title: gettext('Success'),
                text: data.message
            }).then(() => {
                forceCloseModal('csvUploadModal');
                // Reload all tables
                loadDistricts();
                loadCircles();
                loadGramPanchayats();
                loadVillages();
            });
        } else {
            throw new Error(data.error || gettext('Upload failed'));
        }
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: error.message || gettext('Failed to upload CSV file')
        });
    })
    .finally(() => {
        $('#uploadCsvBtn').prop('disabled', false).text(gettext('Upload'));
    });
}

// Modal preparation functions
function prepareDistrictModal() {
    resetModal('district');
}

function prepareCircleModal() {
    resetModal('circle');
    loadDistrictsForDropdown('#circleDistrict');
}

function prepareGramPanchayatModal() {
    resetModal('gram_panchayat');
    initializeSelect2('district', gettext('Select Districts'));
    loadDistrictsForDropdown('#gpDistrict');
    
    // Set up district change event for GP modal
    $('#gpDistrict').off('change').on('change', function() {
        const districtId = $(this).val();
        if (districtId) {
            loadCirclesForDropdown('#gpCircle', districtId);
        }
    });
}

function prepareVillageModal() {
    resetModal('village');
    loadDistrictsForDropdown('#villageDistrict');
    
    // Set up district change event for village modal
    $('#villageDistrict').off('change').on('change', function() {
        const districtId = $(this).val();
        if (districtId) {
            loadCirclesForDropdown('#villageCircle', districtId);
        }
    });
    
    // Set up circle change event for village modal
    $('#villageCircle').off('change').on('change', function() {
        const circleId = $(this).val();
        if (circleId) {
            loadGramPanchayatsForDropdown('#villageGP', circleId);
        }
    });
}

// Reset modal function
function resetModal(type) {
    editingId = null;
    entityType = null;
    
    switch(type) {
        case 'district':
            $('#districtForm')[0].reset();
            $('#districtId').val('');
            $('#districtModalLabel').text(gettext('Add District'));
            $('#saveDistrictBtn').text(gettext('Save'));
            break;
        case 'circle':
            $('#circleForm')[0].reset();
            $('#circleId').val('');
            $('#circleDistrictGroup').show();
            $('#circleDistrict').prop('required', true);
            $('#circleDistrictText').parent().hide();
            $('#circleModalLabel').text(gettext('Add Circle'));
            $('#saveCircleBtn').text(gettext('Save'));
            break;
        case 'gram_panchayat':
            $('#gramPanchayatForm')[0].reset();
            $('#gramPanchayatId').val('');
            $('#gpDistrictGroup').show();
            $('#gpCircleGroup').show();
            $('#gpDistrict').prop('required', true);
            $('#gpCircle').prop('required', true);
            $('#gpDistrictText').parent().hide();
            $('#gpCircleText').parent().hide();
            $('#gramPanchayatModalLabel').text(gettext('Add Gram Panchayat'));
            $('#saveGramPanchayatBtn').text(gettext('Save'));
            break;
        case 'village':
            $('#villageForm')[0].reset();
            $('#villageId').val('');
            $('#villageGeojson').val('');
            $('#villageDistrictGroup').show();
            $('#villageCircleGroup').show();
            $('#villageGPGroup').show();
            $('#villageDistrict').prop('required', true);
            $('#villageCircle').prop('required', true);
            $('#villageGP').prop('required', true);
            $('#villageDistrictText').parent().hide();
            $('#villageCircleText').parent().hide();
            $('#villageGPText').parent().hide();
            $('#villageModalLabel').text(gettext('Add Village'));
            $('#saveVillageBtn').text(gettext('Save'));
            break;
    }
}

// Data loading functions
async function loadDistricts() {
    try {
        const response = await fetch('/api/get_all_districts');
        const data = await response.json();
        
        // Define row mapper function
        const rowMapper = (district, index) => [
            index + 1,
            district.code || '',
            district?.name || '',
            district?.name_as || '',
            district?.name_bn || '',
            district?.latitude || '-',
            district?.longitude || '-',
          
        ];
        
        // Define actions mapper function
        const actionsMapper = (district) => {
            return generateActionButtons(
                district.id, 
                `editDistrict`, 
                `confirmDeleteDistrict`
            );
        };
        
        // Use the utility function to populate the table
        populateDataTable(districtsTable, data, rowMapper, true, actionsMapper);
        
        // Add data attributes to edit buttons for district data
        $('#districts_table tbody').find('.fa-pen-to-square').each(function(index) {
            const district = data[index];
            $(this).parent().attr({
                'data-id': district.id,
                'data-code': district.code || '',
                'data-name': district.name || '',
                'data-name-as': district.name_as || '',
                'data-name-bn': district.name_bn || '',
                'data-bs-toggle': 'modal',
                'data-bs-target': '#districtModal',
                'class': 'table_edit_Btn'
            });
        });
        
        // Adjust columns for responsive display
        adjustDataTableColumns('districts_table');
    } catch (error) {
        console.error('Error loading districts:', error);
        showErrorAlert(gettext('Failed to load districts'));
    }
}

// Function to handle district edit button click
function editDistrict(id) {
    const button = $(`button[onclick="editDistrict(${id})"]`);
    const district = {
        id: id,
        code: button.attr('data-code') || '',
        name: button.attr('data-name') || '',
        name_as: button.attr('data-name-as') || '',
        name_bn: button.attr('data-name-bn') || ''
    };
    
    editingId = id;
    entityType = 'district';
    
    $('#districtId').val(id);
    $('#districtCode').val(district.code);
    $('#districtName').val(district.name);
    $('#districtNameAs').val(district.name_as);
    $('#districtNameBn').val(district.name_bn);
    
    $('#districtModalLabel').text(gettext('Edit District'));
    $('#saveDistrictBtn').text(gettext('Update'));
    
    $('#districtModal').modal('show');
}

async function loadCircles(params = {}) {
    try {
        let url = '/api/get_all_circles';
        const query = new URLSearchParams(params).toString();
        if (query) url += `?${query}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Define row mapper function
        const rowMapper = (circle, index) => [
            index + 1,
            circle.district_name || '',
            circle.name || '',
            circle.name_as || '',
            circle.name_bn || ''
        ];
        
        // Define actions mapper function
        const actionsMapper = (circle) => {
            return generateActionButtons(
                circle.id, 
                `editCircle`, 
                `confirmDeleteCircle`
            );
        };
        
        // Use the utility function to populate the table
        populateDataTable(circlesTable, data, rowMapper, true, actionsMapper);
        
        // Add data attributes to edit buttons
        $('#circles_table tbody').find('.fa-pen-to-square').each(function(index) {
            const circle = data[index];
            $(this).parent().attr({
                'data-id': circle.id,
                'data-district-id': circle.district,
                'data-district-name': circle.district_name || '',
                'data-name': circle.name || '',
                'data-name-as': circle.name_as || '',
                'data-name-bn': circle.name_bn || ''
            });
        });
        
        // Adjust columns for responsive display
        adjustDataTableColumns('circles_table');
    } catch (error) {
        console.error('Error loading circles:', error);
        showErrorAlert(gettext('Failed to load circles'));
    }
}

// Function to handle circle edit button click
function editCircle(id) {
    const button = $(`button[onclick="editCircle(${id})"]`);
    const circle = {
        id: id,
        district_id: button.attr('data-district-id'),
        district_name: button.attr('data-district-name') || '',
        name: button.attr('data-name') || '',
        name_as: button.attr('data-name-as') || '',
        name_bn: button.attr('data-name-bn') || ''
    };
    
    editingId = id;
    entityType = 'circle';
    
    $('#circleId').val(id);
    $('#circleDistrictId').val(circle.district_id);
    $('#circleName').val(circle.name);
    $('#circleNameAs').val(circle.name_as);
    $('#circleNameBn').val(circle.name_bn);
    
    // Hide dropdown and show text instead
    $('#circleDistrictGroup').hide();
    $('#circleDistrict').prop('required', false);
    $('#circleDistrictText').text(circle.district_name).parent().show();
    
    $('#circleModalLabel').text(gettext('Edit Circle'));
    $('#saveCircleBtn').text(gettext('Update'));
    
    $('#circleModal').modal('show');
}

async function loadGramPanchayats(params = {}) {
    try {
        let url = '/api/get_all_gram_panchayats';
        const query = new URLSearchParams(params).toString();
        if (query) url += `?${query}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Define row mapper function
        const rowMapper = (gp, index) => [
            index + 1,
            gp.district_name || '',
            gp.circle_name || '',
            gp.name || '',
            gp.name_as || '',
            gp.name_bn || ''
        ];
        
        // Define actions mapper function
        const actionsMapper = (gp) => {
            return generateActionButtons(
                gp.id, 
                `editGramPanchayat`, 
                `confirmDeleteGramPanchayat`
            );
        };
        
        // Use the utility function to populate the table
        populateDataTable(gramPanchayatsTable, data, rowMapper, true, actionsMapper);
        
        // Add data attributes to edit buttons
        $('#gram_panchayats_table tbody').find('.fa-pen-to-square').each(function(index) {
            const gp = data[index];
            $(this).parent().attr({
                'data-id': gp.id,
                'data-district-id': gp.district_id,
                'data-district-name': gp.district_name || '',
                'data-circle-id': gp.circle,
                'data-circle-name': gp.circle_name || '',
                'data-name': gp.name || '',
                'data-name-as': gp.name_as || '',
                'data-name-bn': gp.name_bn || ''
            });
        });
        
        // Adjust columns for responsive display
        adjustDataTableColumns('gram_panchayats_table');
    } catch (error) {
        console.error('Error loading gram panchayats:', error);
        showErrorAlert(gettext('Failed to load gram panchayats'));
    }
}

// Function to handle gram panchayat edit button click
function editGramPanchayat(id) {
    const button = $(`button[onclick="editGramPanchayat(${id})"]`);
    const gp = {
        id: id,
        district_id: button.attr('data-district-id'),
        district_name: button.attr('data-district-name') || '',
        circle_id: button.attr('data-circle-id'),
        circle_name: button.attr('data-circle-name') || '',
        name: button.attr('data-name') || '',
        name_as: button.attr('data-name-as') || '',
        name_bn: button.attr('data-name-bn') || ''
    };
    
    editingId = id;
    entityType = 'gram_panchayat';

    
    
    $('#gramPanchayatId').val(id);
    $('#gpDistrictId').val(gp.district_id);
    $('#gpCircleId').val(gp.circle_id);
    $('#gpName').val(gp.name);
    $('#gpNameAs').val(gp.name_as);
    $('#gpNameBn').val(gp.name_bn);
    
    // Hide dropdowns and show text instead
    $('#gpDistrictGroup').hide();
    $('#gpCircleGroup').hide();
    $('#gpDistrict').prop('required', false);
    $('#gpCircle').prop('required', false);
    $('#gpDistrictText').text(gp.district_name).parent().show();
    $('#gpCircleText').text(gp.circle_name).parent().show();
    
    $('#gramPanchayatModalLabel').text(gettext('Edit Gram Panchayat'));
    $('#saveGramPanchayatBtn').text(gettext('Update'));
    
    $('#gramPanchayatModal').modal('show');
}

async function loadVillages(params = {}) {
    try {
        let url = '/api/get_all_villages';
        const query = new URLSearchParams(params).toString();
        if (query) url += `?${query}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Define row mapper function
        const rowMapper = (village, index) => [
            index + 1,
            village.code || '',
            village.district_name || '',
            village.circle_name || '',
            village.gram_panchayat_name || '',
            village.name || '',
            village.name_as || '',
            village.name_bn || '',
            village.latitude || '-',
            village.longitude || '-'
        ];
        
        // Define actions mapper function
        const actionsMapper = (village) => {
            return generateActionButtons(
                village.id, 
                `editVillage`, 
                `confirmDeleteVillage`
            );
        };
        
        // Use the utility function to populate the table
        populateDataTable(villagesTable, data, rowMapper, true, actionsMapper);
        
        // Add data attributes to edit buttons
        $('#villages_table tbody').find('.fa-pen-to-square').each(function(index) {
            const village = data[index];
            $(this).parent().attr({
                'data-id': village.id,
                'data-district-id': village.district_id,
                'data-district-name': village.district_name || '',
                'data-circle-id': village.circle_id,
                'data-circle-name': village.circle_name || '',
                'data-gp-id': village.gram_panchayat,
                'data-gp-name': village.gram_panchayat_name || '',
                'data-code': village.code || '',
                'data-name': village.name || '',
                'data-name-as': village.name_as || '',
                'data-name-bn': village.name_bn || ''
            });
        });
        
        // Adjust columns for responsive display
        adjustDataTableColumns('villages_table');
    } catch (error) {
        console.error('Error loading villages:', error);
        showErrorAlert(gettext('Failed to load villages'));
    }
}

// Function to handle village edit button click
function editVillage(id) {
    editingId = id;
    entityType = 'village';
    
    // Fetch village data from API
    fetch(`/api/get_village_by_id/${id}`)
        .then(response => response.json())
        .then(village => {
            if (village.error) {
                showErrorAlert(village.error);
                return;
            }
            
            $('#villageId').val(id);
            $('#villageDistrictId').val(village.gram_panchayat_district_id || '');
            $('#villageCircleId').val(village.gram_panchayat_circle_id || '');
            $('#villageGPId').val(village.gram_panchayat);
            $('#villageCode').val(village.code || '');
            $('#villageName').val(village.name || '');
            $('#villageNameAs').val(village.name_as || '');
            $('#villageNameBn').val(village.name_bn || '');
            
            // Hide dropdowns and show text instead
            $('#villageDistrictGroup').hide();
            $('#villageCircleGroup').hide();
            $('#villageGPGroup').hide();
            $('#villageDistrict').prop('required', false);
            $('#villageCircle').prop('required', false);
            $('#villageGP').prop('required', false);
            $('#villageDistrictText').text(village.district_name).parent().show();
            $('#villageCircleText').text(village.circle_name).parent().show();
            $('#villageGPText').text(village.gram_panchayat_name).parent().show();
            
            $('#villageModalLabel').text(gettext('Edit Village'));
            $('#saveVillageBtn').text(gettext('Update'));
            
            $('#villageModal').modal('show');
        })
        .catch(error => {
            console.error('Error fetching village data:', error);
            showErrorAlert(gettext('Failed to load village data'));
        });
}

// Dropdown loading functions
async function loadDistrictsForDropdown(selector = '#district') {
    try {
        const response = await fetch('/api/get_all_districts');
        const data = await response.json();
        
        const $select = $(selector);
        $select.find('option:not(:first)').remove();
        
        data.forEach(district => {
            $select.append(`<option value="${district.id}">${district.name}</option>`);
        });
    } catch (error) {
        console.error('Error loading districts for dropdown:', error);
    }
}

async function loadCirclesForDropdown(selector, districtId) {
    try {
        const response = await fetch(`/api/get_all_circles?district_id=${districtId}`);
        const data = await response.json();
        
        const $select = $(selector);
        $select.find('option:not(:first)').remove();
        
        data.forEach(circle => {
            $select.append(`<option value="${circle.id}">${circle.name}</option>`);
        });
    } catch (error) {
        console.error('Error loading circles for dropdown:', error);
    }
}

async function loadGramPanchayatsForDropdown(selector, circleId) {
    try {
        const response = await fetch(`/api/get_all_gram_panchayats?circle_id=${circleId}`);
        const data = await response.json();
        
        const $select = $(selector);
        $select.find('option:not(:first)').remove();
        
        data.forEach(gp => {
            $select.append(`<option value="${gp.id}">${gp.name}</option>`);
        });
    } catch (error) {
        console.error('Error loading gram panchayats for dropdown:', error);
    }
}

function forceCloseModal(modalId) {
    $(`#${modalId}`).modal('hide');
    $('.modal-backdrop').remove();
    $('body').removeClass('modal-open');
}

// Save District
async function saveDistrict() {
    const formData = {
        name: $('#districtName').val(),
        name_as: $('#districtNameAs').val(),
        name_bn: $('#districtNameBn').val(),
        code: $('#districtCode').val()
    };

    const url = '/en/api/' + (editingId ? `${editingId}/update_district` : 'create_district');
    const method = editingId ? 'PATCH' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            forceCloseModal('districtModal');
            showSuccessAlert(editingId ? gettext('District updated successfully') : gettext('District created successfully'));
            loadDistricts();
            loadDistrictsForDropdown();
        } else {
            showErrorAlert(result.message || gettext('Failed to save district'));
        }
    } catch (error) {
        console.error('Error saving district:', error);
        showErrorAlert(gettext('An error occurred while saving the district'));
    }
}

// Save Circle
async function saveCircle() {
    const formData = {
        name: $('#circleName').val(),
        name_as: $('#circleNameAs').val(),
        name_bn: $('#circleNameBn').val(),
        district: editingId ? $('#circleDistrictId').val() : $('#circleDistrict').val()
    };

    const url = editingId ? `/en/api/${editingId}/update_circle` : '/en/api/create_circle';
    const method = editingId ? 'PATCH' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            forceCloseModal('circleModal');
            showSuccessAlert(editingId ? gettext('Circle updated successfully') : gettext('Circle created successfully'));
            loadCircles();
        } else {
            showErrorAlert(result.message || gettext('Failed to save circle'));
        }
    } catch (error) {
        console.error('Error saving circle:', error);
        showErrorAlert(gettext('An error occurred while saving the circle'));
    }
}

// Save Gram Panchayat
async function saveGramPanchayat() {
    const formData = {
        name: $('#gpName').val(),
        name_as: $('#gpNameAs').val(),
        name_bn: $('#gpNameBn').val(),
        circle: editingId ? $('#gpCircleId').val() : $('#gpCircle').val()
    };

    const url = editingId ? `/en/api/${editingId}/update_gram_panchayat` : '/en/api/create_gram_panchayat';
    const method = editingId ? 'PATCH' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            forceCloseModal('gramPanchayatModal');
            showSuccessAlert(editingId ? gettext('Gram Panchayat updated successfully') : gettext('Gram Panchayat created successfully'));
            loadGramPanchayats();
        } else {
            showErrorAlert(result.message || gettext('Failed to save gram panchayat'));
        }
    } catch (error) {
        console.error('Error saving gram panchayat:', error);
        showErrorAlert(gettext('An error occurred while saving the gram panchayat'));
    }
}

// Save Village
async function saveVillage() {
    const formData = new FormData();
    
    // Add text fields
    formData.append('name', $('#villageName').val());
    formData.append('name_as', $('#villageNameAs').val());
    formData.append('name_bn', $('#villageNameBn').val());
    formData.append('code', $('#villageCode').val());
    formData.append('gram_panchayat', editingId ? $('#villageGPId').val() : $('#villageGP').val());
    
    // Add file if selected
    const fileInput = document.getElementById('villageGeojson');
    if (fileInput.files[0]) {
        formData.append('geojson_file', fileInput.files[0]);
    }
    
    formData.append('csrfmiddlewaretoken', getCSRFToken());

    const url = editingId ? `/en/api/${editingId}/update_village` : '/en/api/create_village';
    const method = editingId ? 'PATCH' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            forceCloseModal('villageModal');
            showSuccessAlert(editingId ? gettext('Village updated successfully') : gettext('Village created successfully'));
            loadVillages();
        } else {
            showErrorAlert(result.message || gettext('Failed to save village'));
        }
    } catch (error) {
        console.error('Error saving village:', error);
        showErrorAlert(gettext('An error occurred while saving the village'));
    }
}

// Delete confirmation functions
function confirmDeleteDistrict(id) {
    confirmDelete(id, 'district', gettext('Are you sure you want to delete this district?'), 
        gettext('This will also delete all circles, gram panchayats, and villages associated with this district.'));
}

function confirmDeleteCircle(id) {
    confirmDelete(id, 'circle', gettext('Are you sure you want to delete this circle?'), 
        gettext('This will also delete all gram panchayats and villages associated with this circle.'));
}

function confirmDeleteGramPanchayat(id) {
    confirmDelete(id, 'gram_panchayat', gettext('Are you sure you want to delete this gram panchayat?'), 
        gettext('This will also delete all villages associated with this gram panchayat.'));
}

function confirmDeleteVillage(id) {
    confirmDelete(id, 'village', gettext('Are you sure you want to delete this village?'));
}

function confirmDelete(id, type, title, text = '') {
    Swal.fire({
        title: title,
        text: text,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: gettext('Yes, delete it!'),
        cancelButtonText: gettext('Cancel')
    }).then((result) => {
        if (result.isConfirmed) {
            deleteEntity(id, type);
        }
    });
}

// Delete function
async function deleteEntity(id, type) {
    let url;
    let reloadFunction;

    switch(type) {
        case 'district':
            url = `/en/api/${id}/delete_district`;
            reloadFunction = () => loadDistricts();  // Fix: wrap in function
            break;
        case 'circle':
            url = `/en/api/${id}/delete_circle`;
            reloadFunction = () => loadCircles();
            break;
        case 'gram_panchayat':
            url = `/en/api/${id}/delete_gram_panchayat`;
            reloadFunction = () => loadGramPanchayats();
            break;
        case 'village':
            url = `/en/api/${id}/delete_village`;
            reloadFunction = () => loadVillages();
            break;
        default:
            showErrorAlert(gettext('Invalid entity type'));
            return;
    }

    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
        });

        if (response.status === 204) {
            showSuccessAlert(gettext('Deleted successfully'));
            reloadFunction();  // Call the function here

            if (type === 'district') {
                loadDistrictsForDropdown();
            }
        } else {
            try {
                const result = await response.json();
                showErrorAlert(result.message || gettext('Failed to delete'));
            } catch {
                showErrorAlert(gettext('Failed to delete'));
            }
        }
    } catch (error) {
        console.error(`Error deleting ${type}:`, error);
        showErrorAlert(gettext(`An error occurred while deleting the ${type}`));
    }
}


function showSuccessAlert(message) {
    Swal.fire({
        icon: 'success',
        title: gettext('Success'),
        text: message,
        confirmButtonColor: '#245FAE'
    }).then(() => {
        window.location.reload();
    });
}

function showErrorAlert(message) {
    Swal.fire({
        icon: 'error',
        title: gettext('Error'),
        text: message,
        confirmButtonColor: '#dc3545'
    });
}

// Add window resize handler to adjust all DataTables
$(window).on('resize', function() {
    adjustAllDataTables();
});

// Adjust tables when sidebar is toggled
$('.sidebar-toggle').on('click', function() {
    setTimeout(adjustAllDataTables, 300);
});

// Adjust tables after they're fully loaded
$(window).on('load', function() {
    setTimeout(function() {
        adjustDataTableColumns('districts_table');
        adjustDataTableColumns('circles_table');
        adjustDataTableColumns('gram_panchayats_table');
        adjustDataTableColumns('villages_table');
    }, 500);
});

// Adjust tables when tab is changed
$('.nav-link').on('click', function() {
    setTimeout(function() {
        adjustAllDataTables();
    }, 100);
});

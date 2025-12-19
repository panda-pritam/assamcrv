// No need for loadVDMPActivities function as data will be loaded from context

let isAdministrator = null;
let vdmp_progress_table=null
// Function to handle adding a new VDMP activity
async function addVDMPActivity() {
    const name = document.getElementById('add_activity_name').value;
    const name_bn = document.getElementById('add_activity_name_bn').value;
    const name_as = document.getElementById('add_activity_name_as').value;
    
    if (!name) {
        Swal.fire({
            icon: 'error',
            title: gettext('Validation Error'),
            text: gettext('Activity name is required!')
        });
        return;
    }
    
    try {
        const response = await fetch('/en/api/create_vdmp_activity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                name,
                name_bn,
                name_as,
                is_active: true
            })
        });
        
        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: gettext('Success'),
                text: gettext('VDMP Activity added successfully!')
            }).then(() => {
                // Close modal and reload page
                $('#addVDMPActivityModal').modal('hide');
                window.location.reload();
            });
        } else {
            const errorData = await response.json();
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('Failed to add VDMP Activity: ') + JSON.stringify(errorData)
            });
        }
    } catch (error) {
        console.error('Error adding VDMP activity:', error);
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: gettext('An unexpected error occurred. Please try again.')
        });
    }
}

// Function to populate edit modal with activity data
function editVDMPActivity(id, name, name_bn, name_as, is_active) {
    document.getElementById('edit_activity_id').value = id;
    document.getElementById('edit_activity_name').value = name;
    document.getElementById('edit_activity_name_bn').value = name_bn || '';
    document.getElementById('edit_activity_name_as').value = name_as || '';
    document.getElementById('edit_activity_is_active').checked = is_active;
    
    $('#editVDMPActivityModal').modal('show');
}

// Function to update VDMP activity
async function updateVDMPActivity() {
    const id = document.getElementById('edit_activity_id').value;
    const name = document.getElementById('edit_activity_name').value;
    const name_bn = document.getElementById('edit_activity_name_bn').value;
    const name_as = document.getElementById('edit_activity_name_as').value;
    const is_active = document.getElementById('edit_activity_is_active').checked;
    
    if (!name) {
        Swal.fire({
            icon: 'error',
            title: gettext('Validation Error'),
            text: gettext('Activity name is required!')
        });
        return;
    }
    
    // Confirm before updating
    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext("Do you want to update this VDMP Activity?"),
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#d33',
        confirmButtonText: gettext('Yes, update it!')
    });
    
    if (!result.isConfirmed) {
        return;
    }
    
    try {
        const response = await fetch(`/api/update_vdmp_activity/${id}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                name,
                name_bn,
                name_as,
                is_active
            })
        });
        
        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: gettext('Success'),
                text: gettext('VDMP Activity updated successfully!')
            }).then(() => {
                // Close modal and reload page
                $('#editVDMPActivityModal').modal('hide');
                window.location.reload();
            });
        } else {
            const errorData = await response.json();
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('Failed to update VDMP Activity: ') + JSON.stringify(errorData)
            });
        }
    } catch (error) {
        console.error('Error updating VDMP activity:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'An unexpected error occurred. Please try again.'
        });
    }
}

// Function to confirm deletion of VDMP activity
function confirmDeleteVDMPActivity(id) {
    Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext("You won't be able to revert this!"),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#d33',
        confirmButtonText: gettext('Yes, delete it!')
    }).then((result) => {
        if (result.isConfirmed) {
            deleteVDMPActivity(id);
        }
    });
}

async function deleteVDMPActivity(id) {
    try {
        const response = await fetch(`/api/delete_vdmp_activity/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: gettext('Deleted!'),
                text: gettext('VDMP Activity has been deleted.')
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('Failed to delete VDMP Activity.')
            });
        }
    } catch (error) {
        console.error('Error deleting VDMP activity:', error);
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: gettext('An unexpected error occurred. Please try again.')
        });
    }
}

function editVDMPProgress(id) {
    const item = vdmpProgressData.find(item => item.id === id);

    if (item) {
        $('#edit_vdmp_progress_id').val(id);
        $('#edit_vdmp_progress_status').val(item.status || '');
        $('#editVDMPProgressModal').modal('show');
    } else {
        console.error('Item not found with ID:', id);
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: gettext('Could not find the selected item.')
        });
    }
}

async function updateVDMPProgress() {
    const id = $('#edit_vdmp_progress_id').val();
    const status = $('#edit_vdmp_progress_status').val();

    if (!status) {
        Swal.fire({
            icon: 'error',
            title: gettext('Validation Error'),
            text: gettext('Status is required!')
        });
        return;
    }

    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you want to update this VDMP Activity Status?'),
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#d33',
        confirmButtonText: gettext('Yes, update it!')
    });

    if (!result.isConfirmed) return;

    // Show loader with processing message
    Swal.fire({
        title: gettext('Processing...'),
        text: gettext('It will take a bit of time, we are processing the data for the selected village'),
        icon: 'info',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    try {
        const response = await fetch(`/api/update_vdmp_activity_status/${id}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: gettext('Success'),
                text: gettext('VDMP Activity Status updated successfully!')
            }).then(() => {
                $('#editVDMPProgressModal').modal('hide');
                
                const districtId = $('#district').val();
                const villageId = $('#village').val();
                const circle_id = $('#circle').val();
                const gram_panchayat_id = $('#gram_panchayat').val();
                const status = $('#VDMP_status').val();
                const activity = $('#VDMP_Activities').val();
                getVDMPProgressData(villageId, districtId, circle_id, gram_panchayat_id, status, activity);
            });
        } else {
            const errorData = await response.json();
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('Failed to update VDMP Activity Status: ') + JSON.stringify(errorData)
            });
        }
    } catch (error) {
        console.error('Error updating VDMP activity status:', error);
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: gettext('An unexpected error occurred. Please try again.')
        });
    }
}


function deleteVDMPProgress(id) {
    Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext("You won't be able to revert this!"),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#d33',
        confirmButtonText: gettext('Yes, delete it!')
    }).then((result) => {
        if (result.isConfirmed) {
            confirmDeleteVDMPProgress(id);
        }
    });
}

async function confirmDeleteVDMPProgress(id) {
    try {
        const response = await fetch(`/api/delete_vdmp_activity_status/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            Swal.fire({
                icon: 'success',
                title: gettext('Deleted!'),
                text: gettext('VDMP Activity Status has been deleted.')
            }).then(() => {
                const districtId = $('#district').val();
                const villageId = $('#village').val();
                const circle_id = $('#circle').val();
                const gram_panchayat_id = $('#gram_panchayat').val();
                const status = $('#VDMP_status').val();
                const activity = $('#VDMP_Activities').val();
                getVDMPProgressData(villageId, districtId, circle_id, gram_panchayat_id, status, activity);
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('Failed to delete VDMP Activity Status.')
            });
        }
    } catch (error) {
        console.error('Error deleting VDMP activity status:', error);
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: gettext('An unexpected error occurred. Please try again.')
        });
    }
}


// Initialize the page
document.addEventListener('DOMContentLoaded', function() {

     colorChange("vdmp_progress",'vdmp_progress_admin');
     $('#vdmp_progress_activity_master').DataTable({
        "pageLength": 10,
        "ordering": true,
        "searching": true,
        "info": true,
        "paging": true
    });

    // Check if URL contains administrator
    isAdministrator = window.location.href.includes('administrator');

    // Load VDMP activity status data
    getVDMPProgressData();
    
    // Show add button when master tab is active
    const masterTab = document.getElementById('master-tab');
    if (masterTab) {
        masterTab.addEventListener('click', function() {
            document.getElementById('add_vdmp_activity').classList.remove('d-none');
            document.getElementById('add_vdmp_activity').classList.add('d-flex');
        });
    }
    
    // Hide add button when village tab is active
    const villageTab = document.getElementById('village-tab');
    if (villageTab) {
        villageTab.addEventListener('click', function() {
            document.getElementById('add_vdmp_activity').classList.add('d-none');
            document.getElementById('add_vdmp_activity').classList.remove('d-flex');
            // Refresh VDMP activity status data when switching to village tab
            getVDMPProgressData();
        });
    }
    
    // Add event listener for add button
    const addButton = document.getElementById('add_vdmp_activity');
    if (addButton) {
        addButton.addEventListener('click', function() {
            $('#addVDMPActivityModal').modal('show');
        });
    }

    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('village', gettext('Select Villages'));
    initializeSelect2('circle', gettext('Select Circle'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('VDMP_status', gettext('Select Status'));
    initializeSelect2('VDMP_Activities', gettext('Select VDMP Activities'));
    updateSummaryText(true)


    // Setup location selectors
    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');
    
    // Add event listeners for filter changes
    $('#district').on('change', handleFilterChange);
    $('#village').on('change', handleFilterChange);
    $('#circle').on('change', handleFilterChange);
    $('#gram_panchayat').on('change', handleFilterChange);
    $('#VDMP_status').on('change', handleFilterChange);
    $('#VDMP_Activities').on('change', handleFilterChange);
    
    const table_id = "vdmp_progress_table";
        const columns = [
            { title: gettext("S. No."), width: "5%" },
            { title: gettext("District") },
            { title: gettext("Village") },
            { title: gettext("Activity Name") },
            { title: gettext("Status") },
            // { title: gettext("Is Active"), width: "5%" }
        ];
       
           if (isAdministrator) {
        columns.push({ title: gettext("Actions"), width: "150px" });
    }
        vdmp_progress_table=initializeDataTable(table_id, columns, {}, isAdministrator);

       
     getActivitiesList();

      // Add event listener for VDMP upload button
    const uploadVDMPButton = document.getElementById('uploadVDMPMaster');
    if (uploadVDMPButton) {
        uploadVDMPButton.addEventListener('click', handleVDMPUpload);
    }
});

async function handleFilterChange() {
    const districtId = $('#district').val();
    const villageId = $('#village').val();
    const circle_id = $('#circle').val();
    const gram_panchayat_id = $('#gram_panchayat').val();
    const status = $('#VDMP_status').val();
    const activity = $('#VDMP_Activities').val();
    updateSummaryText(true);
    await getVDMPProgressData(villageId, districtId, circle_id, gram_panchayat_id,status,activity);
}

// Store VDMP progress data globally for reference
let vdmpProgressData = [];

async function getVDMPProgressData(village = null, district = null, circle_id = null, gram_panchayat_id = null,status=null,activity=null) {
    try {
        showVDMPTableLoader();
        
        let url = '/api/admin_get_vdmp_activity_status';
        const params = new URLSearchParams();
        
        if (village) params.append('village_id', village);
        if (district) params.append('district_id', district);
        if (circle_id) params.append('circle_id', circle_id);
        if (gram_panchayat_id) params.append('gram_panchayat_id', gram_panchayat_id);
        if(activity) params.append('activity_id', activity)
        if(status) params.append('status', status)
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url, {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        const data = await response.json();
       
        if(data)
        {
            console.log('VDMP Activity Status Data:', data);
        
            // Sort data by order field
            data.sort((a, b) => (a.order || 0) - (b.order || 0));
        
            // Store data globally for reference in edit/delete functions
            vdmpProgressData = data;
            populateVDMPProgressTable(data);    
        }
       
    } catch (error) {
        console.error('Error fetching VDMP activity status:', error);
        hideVDMPTableLoader();
    }
}

function populateVDMPProgressTable(data) {
    const isAdministrator = window.location.href.includes('administrator');

    // Clear loader first
    if (vdmp_progress_table) {
        vdmp_progress_table.clear();
    }

    const rowMapper = (item, index) => [
        index + 1,
        item.district_name || '',
        item.village_name || '',
        item.activity_name || '',
        item.status || '',
        // item.is_active ? 'Yes' : 'No'
    ];

    const actionsMapper = (item) => {
        return generateActionButtons(item.id, 'editVDMPProgress', 'deleteVDMPProgress');
    };

    populateDataTable(vdmp_progress_table, data, rowMapper, isAdministrator, actionsMapper);
}


async function getActivitiesList(){
    try {
        let api_res=await fetch("/api/dropdown_vdmp_activity")
        let json_res=await api_res.json()
        // console.log("List-> ",json_res)
        if(json_res)
        {
            let option=`<option value="">${gettext('Select VDMP Activities')}</option>`
            json_res.map((item)=>{
                option+=`<option value="${item.id}">${item.name}</option>`
            })
            $("#VDMP_Activities").html(option)
        }
    } catch (error) {
        console.log(error)
    }

}


async function handleVDMPUpload() {
    const fileInput = document.getElementById('vdmpMasterFile');
    const button = document.getElementById('uploadVDMPMaster');
    const modal = bootstrap.Modal.getInstance(document.getElementById('uploadVDMPMasterModal'));
    
    if (!fileInput.files[0]) {
        Swal.fire('Error', 'Please select a file', 'error');
        return;
    }
    
    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to upload and update the data?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#6c757d',
        confirmButtonText: gettext('Yes, upload it!'),
        cancelButtonText: gettext('Cancel')
    });
    
    if (!result.isConfirmed) return;
    
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
    button.disabled = true;
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('data_type', 'vdmp_activity_master');
    
    try {
        const response = await fetch('/en/administrator/api/upload_master_data/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            Swal.fire('Success', `Upload completed! Created: ${result.records_created}, Updated: ${result.records_updated}`, 'success');
            modal.hide();
            fileInput.value = '';
            location.reload();
        } else {
            Swal.fire('Error', result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'Upload failed', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function showVDMPTableLoader() {
    if (vdmp_progress_table) {
        vdmp_progress_table.clear();
        vdmp_progress_table.row.add([
            '<div class="text-center" colspan="6"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading VDMP progress data...</div>',
            '', '', '', '', ''
        ]).draw();
    }
}

function hideVDMPTableLoader() {
    // Loader is hidden when table populates
}
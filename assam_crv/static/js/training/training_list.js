/* Variable to track if the current user is an administrator */
let isAdministrator = null;

/* Initialize the page when DOM content is fully loaded */
document.addEventListener('DOMContentLoaded', async function () {
    /* Set the active navigation item */
    colorChange(gettext('training_activities'),gettext('training_activities_admin'));

    /* Initialize each dropdown with select2 for better UX */
    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('village', gettext('Select Villages'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('circle', gettext('Select Circle'));
    initializeSelect2('status', gettext('Select Status'));

    /* Setup cascading location selectors (district -> circle -> gram_panchayat -> village) */
    setupLocationSelectors('district','circle','gram_panchayat','village');
    
    /* Check if the current user is an administrator based on URL */
    isAdministrator = window.location.href.includes('administrator');

    /* Add Actions column to the table if user is an administrator */
    if (isAdministrator) {
        $('#training_activities_table thead tr').append(`<th>${gettext('Actions')}</th>`);
    }

    /* Define the columns for the DataTable */
    const columns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("District") },
        { title: gettext("Village") },
        { title: gettext("Activity") },
        { title: gettext("Status") },
        { title: gettext("Date") },
        { title: gettext("Remarks"), width: "15%" }
    ];

    await updateSummaryText(true);

    if (isAdministrator) {
        columns.push({ title: gettext("Actions"), width: "150px" });
    }

    /* Initialize the DataTable with the defined columns */
    trainingTable = initializeDataTable('training_activities_table', columns, {}, isAdministrator);

    const tbody = document.getElementById('training_activities_body');

    /* Helper function to collect all filter values */
    function getFilters() {
        return {
            district_id: $('#district').val() || '',
            village_id: $('#village').val() || '',
            circle_id: $('#circle').val() || "",
            gram_panchayat_id: $('#gram_panchayat').val() || "",
            status: $('#status').val() || ''
        };
    }

    /* Load initial data with default filters */
    await loadTrainingActivityData(getFilters());

    /* Set up event handlers for all filter changes to reload data */
    $('#district').on('change', async () => {
        await loadTrainingActivityData(getFilters());
        await updateSummaryText(true);
    });
    $('#village').on('change', async () => {
        await loadTrainingActivityData(getFilters());
        await updateSummaryText(true);
    });
    $('#status').on('change', async () => {
        await loadTrainingActivityData(getFilters());
        await updateSummaryText(true);
    });
    $('#circle').on('change', async () => {
        await loadTrainingActivityData(getFilters());
        await updateSummaryText(true);
    });
    $('#gram_panchayat').on('change', async () => {
        await loadTrainingActivityData(getFilters());
        await updateSummaryText(true);
    });
});

/* Function to fetch training activity data from the API based on filters */
async function loadTrainingActivityData(params = {}) {
    try {
        // Show table loader
        showTrainingTableLoader();
        
        let url = `${isAdministrator ? '/api/administrator/get_training_activity_status' : '/api/get_training_activity_status'}`;
        const query = new URLSearchParams(params).toString();
        if (query) url += `?${query}`;

        const fetchOptions = {};
        if (isAdministrator) fetchOptions.headers = { 'X-CSRFToken': getCSRFToken() };

        const response = await fetch(url, fetchOptions);
        const data = await response.json();

        populateTrainingTable(data, isAdministrator);
    } catch (error) {
        console.error(gettext('Error loading training activity data:'), error);
        hideTrainingTableLoader();
        const tbody = document.getElementById('training_activities_body');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-danger">${gettext('Failed to load data.')}</td></tr>`;
        }
    }
}

/* Reference to the DataTable instance */
let trainingTable;

/* Function to populate the training table with fetched data */
function populateTrainingTable(data, isAdministrator) {
    originalTrainingData = data;

    // Clear loader first
    if (trainingTable) {
        trainingTable.clear();
    }

    const rowMapper = (item, index) => [
        index + 1,
        item.district_name || '',
        item.village_name || '',
        item.activity_name || '',
        item.status === 'Scheduled' ? 'To be Scheduled' : (item.status || ''),
        item.status === 'Scheduled' ? (item.implemented_date || '-') : (item.implemented_date || ''),
        item.remarks || ''
    ];

    const actionsMapper = (item) => {
        return generateActionButtons(item.id, 'editTrainingStatus', 'deleteTrainingStatus');
    };

    populateDataTable(trainingTable, data, rowMapper, isAdministrator, actionsMapper);
}

function showTrainingTableLoader() {
    if (trainingTable) {
        trainingTable.clear();
        const loaderRow = [
            '<div class="text-center"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading training data...</div>',
            '', '', '', '', '', ''
        ];
        
        // Add empty column for Actions if administrator
        if (isAdministrator) {
            loaderRow.push('');
        }
        
        trainingTable.row.add(loaderRow).draw();
    }
}

function hideTrainingTableLoader() {
    // Loader is hidden when table populates
}

/* Store the original data for reference in edit/delete operations */
let originalTrainingData = [];

/* Function to handle editing of training status */
function editTrainingStatus(id) {
    const item = originalTrainingData.find(data => data.id === id);
    if (!item) {
        console.error(gettext('Training status not found for ID:'), id);
        return;
    }

    loadDistrictsAndVillages('district_data', 'village_data');

    setTimeout(() => {
        $('#addActivityStatusId').val(item.id);
        $('#activity_data').val(item.activity_id).prop('disabled', true);
        $('#district_data').val(item.district_id).prop('disabled', true);
        $('#district_data').trigger('change');
        setTimeout(() => {
            $('#village_data').val(item.village_id).prop('disabled', true);
        }, 800);

        $('#status_val').val(item.status);
        $('#implemented_date').val(item.implemented_date || '');
        $('#remark').val(item.remarks || '');
    }, 200);

    $('#addActivityStatusModalLabel').text(gettext('Edit Training Activity Status'));
    $('#activityStatusSubmitBtn').text(gettext('Update'));

    $('#addActivityStatusModal').modal('show');

    $('#activityStatusSubmitBtn').off('click').on('click', function(e) {
        e.preventDefault();
        updateTrainingActivityStatus();
    });
}

/* Function to handle deletion of training status with confirmation */
function deleteTrainingStatus(id) {
    Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to delete this training activity status?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#245FAE',
        confirmButtonText: gettext('Yes, delete it!'),
        cancelButtonText: gettext('Cancel')
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/delete_training_activity_status/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    Swal.fire({
                        icon: 'success',
                        title: gettext('Deleted!'),
                        text: data.message,
                        confirmButtonColor: '#245FAE'
                    }).then(() => reloadTrainingTable());
                } else throw new Error(data.error || 'Unknown error');
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: gettext('Error'),
                    text: error.message,
                    confirmButtonColor: '#245FAE'
                });
            });
        }
    });
}

/* Function to confirm and handle deletion of training activity */
function confirmDelete(activityId) {
    Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to delete this training activity?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#245FAE',
        confirmButtonText: gettext('Yes, delete it!'),
        cancelButtonText: gettext('Cancel')
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/delete_training_activity/${activityId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    Swal.fire({
                        icon: 'success',
                        title: gettext('Deleted!'),
                        text: data.message,
                        confirmButtonColor: '#245FAE'
                    }).then(() => location.reload());
                } else throw new Error(data.error || 'Unknown error');
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: gettext('Error'),
                    text: error.message,
                    confirmButtonColor: '#245FAE'
                });
            });
        }
    });
}

/* Function to update training activity status with confirmation */
function updateTrainingActivityStatus() {
    Swal.fire({
        title: gettext('Update Status'),
        text: gettext('Do you really want to update this training status?'),
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#dc3545',
        confirmButtonText: gettext('Yes, update it!'),
        cancelButtonText: gettext('Cancel')
    }).then((result) => {
        if (result.isConfirmed) {
            const id = $('#addActivityStatusId').val();
            const data = {
                activity: $('#activity_data').val(),
                village: $('#village_data').val() || null,
                status: $('#status_val').val(),
                implemented_date: $('#implemented_date').val() || null,
                remarks: $('#remark').val().trim()
            };

            fetch(`/en/api/update_training_activity_status/${id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: gettext('Success'),
                        text: gettext('Status updated successfully!'),
                        confirmButtonColor: '#245FAE'
                    }).then(() => {
                        $('#addActivityStatusModal').modal('hide');
                        reloadTrainingTable();
                    });
                } else {
                    return response.json().then(err => {
                        throw new Error(err.error || gettext('Failed to update status!'));
                    });
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: gettext('Error'),
                    text: error.message,
                    confirmButtonColor: '#245FAE'
                });
            });
        }
    });
}

/* Function to reload the training table with current filters */
function reloadTrainingTable() {
    const filters = {
        district_id: $('#district').val() || '',
        village_id: $('#village').val() || '',
        status: $('#status').val() || ''
    };
    loadTrainingActivityData(filters);
    adjustDataTableColumns('training_activities_table');
}

/* Adjust table columns when sidebar is toggled for better responsiveness */
document.getElementById('sideBarToggler').addEventListener('click', () => {
    adjustDataTableColumns('training_activities_table');
    adjustDataTableColumns('training_activities_table_master');
});

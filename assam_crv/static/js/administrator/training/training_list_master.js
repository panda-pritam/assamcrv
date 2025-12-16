/* This JS is for the training activities master list in the administrator section
   It handles CRUD operations for training activities and their statuses
*/

/* Helper function to show SweetAlert notifications with consistent styling */
function showSwal(type, title, message, reload = false) {
    Swal.fire({
        icon: type,
        title: gettext(title),
        text: gettext(message),
        confirmButtonColor: type === 'success' ? '#6f42c1' : '#dc3545'
    }).then(() => {
        if (reload) location.reload();
    });
}

/* Generic function to handle API requests with proper error handling and success messages */
async function sendRequest(url, method, data, successMsg, errorMsg) {
    try {
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const result = await response.json();
            throw result;
        }

        showSwal('success', gettext('Success'), successMsg, true);
    } catch (error) {
        console.error('Error:', error);
        const msg = typeof error === 'object' ? Object.values(error).flat().join(', ') : errorMsg;
        showSwal('error', gettext('Error'), msg);
    }
}

/* Initialize the page when DOM is fully loaded */
document.addEventListener('DOMContentLoaded', async () => {
    /* Set the active navigation item */
    colorChange("training_activities",'training_activities_admin');
        const uploadBtn = document.getElementById('uploadTrainingMaster');
    const fileInput = document.getElementById('trainingMasterFile');
    
    /* Initialize DataTables for better table functionality */
    [ '#training_activities_table_master'].forEach(id => {
        $(id).DataTable({ paging: true, searching: true, ordering: true, autoWidth: false, responsive: true });
    });


    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', handleUpload);
    }
    updateSummaryText(true)
});

/* Training Activity Form Submission and event handlers */
$(document).ready(function () {

    /* Handle the submission of the add activity form */
    $('#addActivityForm').on('submit', function (e) {
        e.preventDefault();

        const data = {
            name: $('#addActivityNameEn').val().trim(),
            name_bn: $('#addActivityNameBn').val().trim(),
            name_as: $('#addActivityNameAs').val().trim()
        };

        sendRequest(
            '/en/api/create_training_activity',
            'POST',
            data,
            gettext('Activity added successfully!'),
            gettext('Failed to add activity.'),
            '#addActivityModal',
            '#addActivityForm'
        );
    });


    /* Handle edit button clicks to populate the edit form */
    $('.table_edit_Btn').on('click', function () {
        $('#editActivityId').val($(this).data('id'));
        $('#editActivityNameEn').val($(this).data('nameEn'));
        $('#editActivityNameBn').val($(this).data('nameBn'));
        $('#editActivityNameAs').val($(this).data('nameAs'));
    });

    /* Handle the submission of the edit activity form */
    $('#editActivityForm').on('submit', function (e) {
        e.preventDefault();
        
        Swal.fire({
            title: gettext('Are you sure?'),
            text: gettext('Do you really want to update this activity?'),
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#6f42c1',
            cancelButtonColor: '#6c757d',
            confirmButtonText: gettext('Yes, update it!'),
            cancelButtonText: gettext('Cancel')
        }).then((result) => {
            if (result.isConfirmed) {
                const id = $('#editActivityId').val();
                const data = {
                    name: $('#editActivityNameEn').val().trim(),
                    name_bn: $('#editActivityNameBn').val().trim(),
                    name_as: $('#editActivityNameAs').val().trim()
                };
                sendRequest(`/en/api/update_training_activity/${id}/`, 'PATCH', data, gettext('Activity updated successfully!'), gettext('Failed to update activity!'));
            }
        });
    });

    /* Handle clicks on edit status buttons to populate the status edit modal */
    $(document).on('click', '.btn-edit-status', function () {
        const el = $(this);
        const id = el.data('id');

        $('#addActivityStatusId').val(id);
        $('#activity_data').val(el.data('activity')).prop('disabled', true);
        $('#district_data').val(el.data('district')).prop('disabled', true).trigger('change');

        setTimeout(() => {
            $('#village_data').val(el.data('village')).prop('disabled', true);
        }, 300);

        $('#status_val').val(el.data('status'));
        $('#implemented_date').val(el.data('implemented-date'));
        $('#remark').val(el.data('remark'));

        $('#addActivityStatusModalLabel').text(gettext('Edit Training Activity Status'));
        $('#activityStatusSubmitBtn').text(gettext('Update'));
        $('#addActivityStatusModal').modal('show');
    });

    /* Reset the activity status form when the modal is closed */
    $('#addActivityStatusModal').on('hidden.bs.modal', function () {
        $('#addActivityStatusForm')[0].reset();
        $('#addActivityStatusId').val('');
        $('#addActivityStatusModalLabel').text(gettext('Add Training Activity Status'));
        $('#activityStatusSubmitBtn').text(gettext('Add'));
        $('#village_data, #district_data, #activity_data').prop('disabled', false);
    });

    /* Handle the submission of the activity status form (both add and edit modes) */
    $('#addActivityStatusForm').on('submit', async function (e) {
        e.preventDefault();

        const id = $('#addActivityStatusId').val();
        const isEditMode = !!id;

        const data = {
            activity: $('#activity_data').val(),
            village: $('#village_data').val(),
            status: $('#status_val').val(),
            implemented_date: $('#implemented_date').val(),
            remarks: $('#remark').val().trim()
        };

        const url = isEditMode
            ? `/en/api/update_training_activity_status/${id}/`
            : `/en/api/create_training_activity_status`;

        const method = isEditMode ? 'PATCH' : 'POST';

        if (isEditMode) {
            Swal.fire({
                title: gettext('Are you sure?'),
                text: gettext('Do you really want to update this status?'),
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#6f42c1',
                cancelButtonColor: '#6c757d',
                confirmButtonText: gettext('Yes, update it!'),
                cancelButtonText: gettext('Cancel')
            }).then((result) => {
                if (result.isConfirmed) {
                    sendRequest(url, method, data, gettext('Status updated!'), gettext('Failed to save status.'));
                }
            });
        } else {
            sendRequest(url, method, data, gettext('Status added!'), gettext('Failed to save status.'));
        }
    });
});


async function handleUpload() {
    const fileInput = document.getElementById('trainingMasterFile');
    const button = document.getElementById('uploadTrainingMaster');
    const modal = bootstrap.Modal.getInstance(document.getElementById('uploadTrainingMasterModal'));
    
    if (!fileInput.files[0]) {
        Swal.fire('Error', 'Please select a file', 'error');
        return;
    }
    
    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to upload and update the data?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#6f42c1',
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
    formData.append('data_type', 'training_activity_master');
    
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
        Swal.fire('Error', 'Upload failed', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}
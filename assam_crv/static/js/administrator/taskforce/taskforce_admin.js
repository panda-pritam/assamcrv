let taskForceTable;
let taskForceData = [];

$(document).ready(function () {
    colorChange('task_force_admin', 'task_force_admin')
    initializeTaskForceTable();
    initializeSelect2('district');
    initializeSelect2('circle');
    initializeSelect2('gram_panchayat');
    initializeSelect2('village');
    initializeSelect2('team_type');
    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');
    loadTaskForceData();
    setupEventListeners();
    updateSummaryText();
    setupLocationSelectors('add_district', 'add_circle', 'add_gram_panchayat', 'add_village');

});

function initializeTaskForceTable() {
    const columns = [
        { title: gettext("Sr. No")},
        { title: gettext("Name") },
        { title: gettext("Father's Name") },
        { title: gettext("Gender")},
        { title: gettext("Phone Number") },
        { title: gettext("Position/Responsibility") },
        { title: gettext("District Name") },
        // { title: gettext("Circle Name") },
        // { title: gettext("Gram Panchayat") },
        { title: gettext("Village Name") },
        { title: gettext("Team Type") },
        { title: gettext("Occupation") },
        { title: gettext("Actions")  }
    ];

    taskForceTable = initializeDataTable('taskforce_table', columns, {}, true);
}

function setupEventListeners() {
    $('#district, #circle, #gram_panchayat, #village, #team_type').change(loadTaskForceData);

    $('#uploadTaskForce').click(uploadTaskForceFile);
    $('#addTaskForceModal').on('shown.bs.modal', function () {
    });
}



async function loadTaskForceData() {
    try {
        const params = new URLSearchParams();
        updateSummaryText()

        const districtId = $('#district').val();
        const circleId = $('#circle').val();
        const gpId = $('#gram_panchayat').val();
        const villageId = $('#village').val();
        const teamType = $('#team_type').val();

        if (districtId) params.append('district_id', districtId);
        if (circleId) params.append('circle_id', circleId);
        if (gpId) params.append('gram_panchayat_id', gpId);
        if (villageId) params.append('village_id', villageId);
        if (teamType) params.append('team_type', teamType);

        const response = await fetch(`/en/api/taskforce/?${params.toString()}`);
        const data = await response.json();

        taskForceData = data;
        populateTaskForceTable(data);
    } catch (error) {
        console.error('Error loading task force data:', error);
        showMessage('Error loading task force data', 'error');
    }
}

function populateTaskForceTable(data) {
    const rowMapper = (item, index) => [
        index + 1,
        item.fullname || '',
        item.father_name || '',
        item.gender || '',
        item.mobile_number || '',
        item.position_responsibility || '',
        item.district_name || 'N/A',
        // item.circle_name || 'N/A',
        // item.gram_panchayat_name || 'N/A',
        item.village_name || 'N/A',
        item.team_type || '',
        item.occupation || 'N/A'
    ];

    const actionsMapper = (item) => {
        return generateActionButtons(item.id, 'editTaskForceMember', 'deleteTaskForceMember');
    };

    populateDataTable(taskForceTable, data, rowMapper, true, actionsMapper);
}

async function addTaskForceMember() {
    const teamType = $('#add_team_type').val();
    if (!teamType) {
        showMessage('Please select a team type first', 'error');
        return;
    }

    const formData = {
        village: $('#add_village').val(),
        fullname: $('#add_fullname').val(),
        father_name: $('#add_father_name').val(),
        gender: $('#add_gender').val(),
        mobile_number: $('#add_mobile_number').val(),
        position_responsibility: $('#add_position_responsibility').val(),
        occupation: $('#add_occupation').val(),
        team_type: teamType
    };

    if (!formData.village || !formData.fullname || !formData.father_name ||
        !formData.gender || !formData.mobile_number || !formData.position_responsibility) {
        showMessage('Please fill all required fields', 'error');
        return;
    }

    try {
        const response = await fetch('/en/api/taskforce/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            $('#addTaskForceModal').modal('hide');
            $('#add_taskforce_form')[0].reset();
            $('#add_team_type').val('');
            await loadTaskForceData();
            showMessage('Task force member added successfully', 'success');
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Error adding task force member', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error adding task force member', 'error');
    }
}

async function editTaskForceMember(id) {
    try {
        const response = await fetch(`/en/api/taskforce/${id}/`);
        const member = await response.json();

        $('#edit_member_id').val(member.id);
        $('#edit_fullname').val(member.fullname);
        $('#edit_father_name').val(member.father_name);
        $('#edit_gender').val(member.gender);
        $('#edit_mobile_number').val(member.mobile_number);
        $('#edit_position_responsibility').val(member.position_responsibility);
        $('#edit_team_type').val(member.team_type);
        $('#edit_occupation').val(member.occupation || '');

        // Load and set location data
        await loadEditLocationData(member);

        $('#editTaskForceModal').modal('show');
    } catch (error) {
        console.error('Error loading member data:', error);
        showMessage('Error loading member data', 'error');
    }
}

async function loadEditLocationData(member) {
    try {
        setupLocationSelectors('edit_district', 'edit_circle', 'edit_gram_panchayat', 'edit_village');

        // Set values after a short delay to ensure dropdowns are loaded
        setTimeout(() => {
            $('#edit_district').val(member.district_id).trigger('change');
            setTimeout(() => {
                $('#edit_circle').val(member.circle_id).trigger('change');
                setTimeout(() => {
                    $('#edit_gram_panchayat').val(member.gram_panchayat_id).trigger('change');
                    setTimeout(() => {
                        $('#edit_village').val(member.village);
                    }, 500);
                }, 500);
            }, 500);
        }, 500);

    } catch (error) {
        console.error('Error loading location data:', error);
    }
}

async function updateTaskForceMember() {
    const memberId = $('#edit_member_id').val();
    const formData = {
        village: $('#edit_village').val(),
        fullname: $('#edit_fullname').val(),
        father_name: $('#edit_father_name').val(),
        gender: $('#edit_gender').val(),
        mobile_number: $('#edit_mobile_number').val(),
        position_responsibility: $('#edit_position_responsibility').val(),
        occupation: $('#edit_occupation').val(),
        team_type: $('#edit_team_type').val()
    };

    if (!formData.village || !formData.fullname || !formData.father_name ||
        !formData.gender || !formData.mobile_number || !formData.position_responsibility || !formData.team_type) {
        showMessage('Please fill all required fields', 'error');
        return;
    }

    try {
        const response = await fetch(`/en/api/taskforce/${memberId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            $('#editTaskForceModal').modal('hide');
            await loadTaskForceData();
            showMessage('Task force member updated successfully', 'success');
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Error updating task force member', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error updating task force member', 'error');
    }
}

async function deleteTaskForceMember(id) {
    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to delete this task force member?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#dc3545',
        confirmButtonText: gettext('Yes, delete it!')
    });

    if (!result.isConfirmed) return;

    try {
        const response = await fetch(`/en/api/taskforce/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            showMessage('Task force member deleted successfully', 'success');
            await loadTaskForceData();
        } else {
            showMessage('Error deleting task force member', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error deleting task force member', 'error');
    }
}

async function uploadTaskForceFile() {
    const teamType = $('#upload_team_type').val();
    const fileInput = $('#taskforceFile')[0];

    if (!teamType) {
        showMessage('Please select a team type', 'error');
        return;
    }

    if (!fileInput.files.length) {
        showMessage('Please select a file to upload', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('team_type', teamType);

    try {
        const response = await fetch('/en/api/taskforce/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            // $('#uploadTaskForceModal').modal('hide');

            const modalEl = document.getElementById('uploadTaskForceModal');
            const modal = bootstrap.Modal.getInstance(modalEl); // don't new Modal()
            if (modal) {
                modal.hide();
            }
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('padding-right');
            $('#taskforceFile').val('');
            $('#upload_team_type').val('');
            await loadTaskForceData();
            showMessage(`Successfully uploaded ${result.created_count} task force members`, 'success');

           
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Error uploading file', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error uploading file', 'error');
    }
}

function showMessage(message, type) {
    if (type === 'success') {
        Swal.fire({
            title: gettext('Success!'),
            text: message,
            icon: 'success',
            confirmButtonColor: '#245FAE'
        });
        setTimeout(()=>{
            window.location.reload();
        },1500)
    } else if (type === 'error') {
        Swal.fire({
            title: gettext('Error!'),
            text: message,
            icon: 'error',
            confirmButtonColor: '#245FAE'
        });
    } else {
        Swal.fire({
            title: gettext('Info'),
            text: message,
            icon: 'info',
            confirmButtonColor: '#245FAE'
        });
    }
}

// Sidebar toggle adjustment
document.getElementById('sideBarToggler').addEventListener('click', () => {
    adjustDataTableColumns('taskforce_table');
});
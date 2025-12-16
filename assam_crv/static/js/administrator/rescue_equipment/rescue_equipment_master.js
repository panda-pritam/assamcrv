/*This JS is for the rescue eqp marter list in this we have created the table by bring the data from the django context as there are not much data and filtering needed

This has a functions related to CRUD in the master table
*/
document.addEventListener('DOMContentLoaded', () => {
        const uploadBtn = document.getElementById('uploadRescueMaster');
    const fileInput = document.getElementById('rescueMasterFile');
    $('#rescue_equipment_table_master').DataTable({
        "pageLength": 10,
        "ordering": true,
        "searching": true,
        "info": true,
        "paging": true
    });

     if (uploadBtn) {
        uploadBtn.addEventListener('click', handleUpload);
    }
    updateSummaryText(true)
});

colorChange('rescue_equipment','rescue_equipment_admin');



function submitEquipmentForm() {
    const submitBtn = document.querySelector('#addEquipmentModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> ' + gettext('Saving...');
    submitBtn.disabled = true;
    
    const formData = {
        name: document.getElementById('name').value,
        name_bn: document.getElementById('name_bn').value,
        name_as: document.getElementById('name_as').value,
        task_force: document.getElementById('task_force').value,
        task_force_bn: document.getElementById('task_force_bn').value,
        task_force_as: document.getElementById('task_force_as').value,
        specification: document.getElementById('specification').value,
        specification_bn: document.getElementById('specification_bn').value,
        specification_as: document.getElementById('specification_as').value
    };

    
    
    fetch('/en/api/create_rescue_equipment/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            return response.json().then(err => Promise.reject(err));
        }
    })
    .then(data => {
        Swal.fire({
            icon: 'success',
            title: gettext('Success'),
            text: data.message,
            confirmButtonColor: '#245FAE'
        }).then(() => location.reload());
    })
    .catch(error => {
        let errorMessage = gettext('Unknown error');
        if (error.name && error.name[0]) {
            errorMessage = error.name[0];
        } else if (error.error) {
            errorMessage = error.error;
        } else if (typeof error === 'string') {
            errorMessage = error;
        }
        
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: errorMessage,
            confirmButtonColor: '#245FAE'
        });
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

function editEquipment(id, name, name_bn, name_as, task_force, task_force_bn, task_force_as, specification, specification_bn, specification_as) {
    // console.log('Editing equipment with ID:', id);
    // console.log(id, name, name_bn, name_as, task_force, task_force_bn, task_force_as, specification, specification_bn, specification_as);
    
    
     document.getElementById('editEquipmentId').value = id;
            document.getElementById('editName').value = name;
            document.getElementById('editNameBn').value = name_bn;
            document.getElementById('editNameAs').value = name_as;
            document.getElementById('editEquipTaskForce').value = task_force;
            document.getElementById('editEquipTaskForceBn').value = task_force_bn;
            document.getElementById('editEquipTaskForceAs').value = task_force_as;
            document.getElementById('editEquipSpecification').value = specification;
            document.getElementById('editEquipSpecificationBn').value = specification_bn;
            document.getElementById('editEquipSpecificationAs').value = specification_as;
            
            const editModal = new bootstrap.Modal(document.getElementById('editEquipmentModal'));
            editModal.show();
}

function submitEditEquipmentForm() {
    Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you want to update this equipment?'),
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#dc3545',
        confirmButtonText: gettext('Yes, update it!'),
        cancelButtonText: gettext('Cancel')
    }).then((result) => {
        if (result.isConfirmed) {
            const submitBtn = document.querySelector('#editEquipmentModal .btn-primary');
            const originalText = submitBtn.innerHTML;
            const equipmentId = document.getElementById('editEquipmentId').value;
            
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> ' + gettext('Updating...');
            submitBtn.disabled = true;
            
            const formData = {
                name: document.getElementById('editName').value,
                name_bn: document.getElementById('editNameBn').value,
                name_as: document.getElementById('editNameAs').value,
                task_force: document.getElementById('editEquipTaskForce').value,
                task_force_bn: document.getElementById('editEquipTaskForceBn').value,
                task_force_as: document.getElementById('editEquipTaskForceAs').value,
                specification: document.getElementById('editEquipSpecification').value,
                specification_bn: document.getElementById('editEquipSpecificationBn').value,
                specification_as: document.getElementById('editEquipSpecificationAs').value
            };
            
            fetch(`/en/api/update_rescue_equipment/${equipmentId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    return response.json().then(err => Promise.reject(err));
                }
            })
            .then(data => {
                Swal.fire({
                    icon: 'success',
                    title: gettext('Success'),
                    text: data.message,
                    confirmButtonColor: '#245FAE'
                }).then(() => location.reload());
            })
            .catch(error => {
                let errorMessage = gettext('Unknown error');
                if (error.name && error.name[0]) {
                    errorMessage = error.name[0];
                } else if (error.error) {
                    errorMessage = error.error;
                } else if (typeof error === 'string') {
                    errorMessage = error;
                }
                
                Swal.fire({
                    icon: 'error',
                    title: gettext('Error'),
                    text: errorMessage,
                    confirmButtonColor: '#245FAE'
                });
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        }
    });
}

function confirmDelete(equipmentId) {
    Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to delete this equipment?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#245FAE',
        confirmButtonText: gettext('Yes, delete it!'),
        cancelButtonText: gettext('Cancel')
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/en/api/delete_rescue_equipment/${equipmentId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
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
                } else {
                    throw new Error(data.error || gettext('Unknown error'));
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

async function handleUpload() {
    const fileInput = document.getElementById('rescueMasterFile');
    const button = document.getElementById('uploadRescueMaster');
    const modal = bootstrap.Modal.getInstance(document.getElementById('uploadRescueMasterModal'));
    
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
    formData.append('data_type', 'rescue_equipment_master');
    
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
let fieldImagesTable;
let fieldImagesData = [];

$(document).ready(function () {
    colorChange('field_images_admin', 'field_images_admin');
    initializeFieldImagesTable();
    initializeSelect2('district',"Select District");
    initializeSelect2('circle',"Select Circle");
    initializeSelect2('gram_panchayat', "Select Gram-panchayat");
    initializeSelect2('village',"Select Village");
    initializeSelect2('category',"Select Category");
    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');
    setupLocationSelectors('add_district', 'add_circle', 'add_gram_panchayat', 'add_village');
    loadFieldImagesData();
    setupEventListeners();
    updateSummaryText();
});

function initializeFieldImagesTable() {
    const columns = [
        { title: gettext("Sr. No"), width: "5%" },
        { 
            title: gettext("Image"), 
            width: "15%",
            render: function(data, type, row) {
                if (!data) return '';
                return `<img src="${data}" 
                            class="img-thumbnail preview-clickable" 
                            style="max-height: 100px; cursor: pointer;" 
                            data-image="${data}">`;
            }
            
        },
        { title: gettext("Category") },
        { title: gettext("Name") },
        { title: gettext("Upload Date") },
        { title: gettext("District Name") },
        { title: gettext("Village Name") },
        { title: gettext("Uploaded By") },
        { 
            title: gettext("Actions"), 
            width: "150px",
            orderable: false
        }
    ];

    fieldImagesTable = initializeDataTable('field_images_table', columns, {}, true);
}

function setupEventListeners() {
    // 🔹 When any filter changes, reload the data
    $('#district, #circle, #gram_panchayat, #village, #category').on('change', function () {
        updateSummaryText()
        
        loadFieldImagesData();
    });

    // // 🔹 When Add Image modal opens, initialize its location selectors
    // $('#addFieldImageModal').on('shown.bs.modal', function () {
    //     setupLocationSelectors('add_district', 'add_circle', 'add_gram_panchayat', 'add_village');
    // });

    // 🔹 When Edit Image modal opens, initialize its location selectors
    $('#editFieldImageModal').on('shown.bs.modal', function () {
        setupLocationSelectors('edit_district', 'edit_circle', 'edit_gram_panchayat', 'edit_village');
    });
}



// Update your loadFieldImagesData function to handle all filters
async function loadFieldImagesData() {
    try {
        // showLoading(); // Show loading indicator
        
        const params = new URLSearchParams();

        // Get all filter values
        const districtId = $('#district').val();
        const circleId = $('#circle').val();
        const gpId = $('#gram_panchayat').val();
        const villageId = $('#village').val();
        const category = $('#category').val();

        // Add filters to params only if they have values
        if (districtId) params.append('district_id', districtId);
        if (circleId) params.append('circle_id', circleId);
        if (gpId) params.append('gram_panchayat_id', gpId);
        if (villageId) params.append('village_id', villageId);
        if (category) params.append('category', category);

        console.log(params.toString())

        const response = await fetch(`/en/api/field-images/?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        fieldImagesData = data;
        populateFieldImagesTable(data);
        
    } catch (error) {
        console.error('Error loading field images data:', error);
        showMessage('Error loading field images data', 'error');
    } finally {
        // hideLoading(); // Hide loading indicator
    }
}

function populateFieldImagesTable(data) {
    const rowMapper = (item, index) => [
        index + 1,
        item.image_url || '',
        item.category || '',
        item.name || 'N/A',
        new Date(item.upload_datetime).toLocaleDateString(),
        item.district_name || 'N/A',
        item.village_name || 'N/A',
        item.uploaded_by_name || 'N/A'
    ];

    const actionsMapper = (item) => {
        return generateActionButtons(item.id, 'editFieldImage', 'deleteFieldImage');
    };

    populateDataTable(fieldImagesTable, data, rowMapper, true, actionsMapper);
}

// async function addFieldImage() {
//     const formData = new FormData();
//     const village = $('#add_village').val();
//     const category = $('#add_category').val();
//     const name = $('#add_name').val();
//     const imageFile = $('#add_image')[0].files[0];

//     if (!village || !category || !imageFile) {
//         showMessage('Please fill all required fields', 'error');
//         return;
//     }

//     formData.append('village', village);
//     formData.append('category', category);
//     formData.append('image', imageFile);
//     if (name) formData.append('name', name);

//     try {
//         const response = await fetch('/en/api/field-images/', {
//             method: 'POST',
//             headers: {
//                 'X-CSRFToken': getCSRFToken()
//             },
//             body: formData
//         });

//         if (response.ok) {
//             // $('#addFieldImageModal').modal('hide');
//             // $('#add_field_image_form')[0].reset();

//            closeModel('addFieldImageModal')
//             await loadFieldImagesData();
//             showMessage('Field image added successfully', 'success');
//         } else {
//             const error = await response.json();
//             showMessage(error.detail || 'Error adding field image', 'error');
//         }
//     } catch (error) {
//         console.error('Error:', error);
//         showMessage('Error adding field image', 'error');
//     }
// }


async function addFieldImage() {
    const formData = new FormData();
    const village = $('#add_village').val();
    const category = $('#add_category').val();
    const name1 = $('#add_name1').val();
    const name2 = $('#add_name2').val();
    const imageFile1 = $('#add_image1')[0].files[0];
    const imageFile2 = $('#add_image2')[0].files[0];

    if (!village || !category || !imageFile1) {
        showMessage('Please fill all required fields (Village, Category, and at least Image 1)', 'error');
        return;
    }

    formData.append('village', village);
    formData.append('category', category);
    formData.append('image1', imageFile1);
    if (name1) formData.append('name1', name1);
    
    if (imageFile2) {
        formData.append('image2', imageFile2);
        if (name2) formData.append('name2', name2);
    }

    try {
        const response = await fetch('/en/api/field-images/bulk-upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });

        if (response.ok) {
            await loadFieldImagesData();
            const uploadedCount = imageFile2 ? 2 : 1;
            showMessage(`${uploadedCount} field image(s) added successfully`, 'success');
            setTimeout(()=>{
                window.location.reload();
            },1500)
        } else {
            const error = await response.json();

            if (error.non_field_errors && error.non_field_errors.length > 0) {
                showMessage(error.non_field_errors[0], 'error');
            } else if (error.detail) {
                showMessage(error.detail, 'error');
            } else {
                showMessage('Error adding field images', 'error');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error adding field images', 'error');
    }
}

async function editFieldImage(id) {
    try {
        const response = await fetch(`/en/api/field-images/${id}/`);
        const image = await response.json();

        $('#edit_image_id').val(image.id);
        $('#edit_name').val(image.name || '');
        $('#edit_category').val(image.category);

        // Show current image
        if (image.image_url) {
            $('#current_image').attr('src', image.image_url);
            $('#current_image_container').show();
        } else {
            $('#current_image_container').hide();
        }

        // Initialize location selectors
        setupLocationSelectors('edit_district', 'edit_circle', 'edit_gram_panchayat', 'edit_village');

        // Set location values in sequence after a small delay
        setTimeout(() => {
            $('#edit_district').val(image.district_id).trigger('change');
            
            setTimeout(() => {
                $('#edit_circle').val(image.circle_id).trigger('change');
                
                setTimeout(() => {
                    $('#edit_gram_panchayat').val(image.gram_panchayat_id).trigger('change');
                    
                    setTimeout(() => {
                        $('#edit_village').val(image.village);
                        $('#editFieldImageModal').modal('show');
                    }, 500);
                }, 500);
            }, 500);
        }, 100);

    } catch (error) {
        console.error('Error loading image data:', error);
        showMessage('Error loading image data', 'error');
    }
}

async function loadEditLocationData(image) {
    try {
        setupLocationSelectors('edit_district', 'edit_circle', 'edit_gram_panchayat', 'edit_village');

        // Set values after a short delay to ensure dropdowns are loaded
        setTimeout(() => {
            $('#edit_district').val(image.district_id).trigger('change');
            setTimeout(() => {
                $('#edit_circle').val(image.circle_id).trigger('change');
                setTimeout(() => {
                    $('#edit_gram_panchayat').val(image.gram_panchayat_id).trigger('change');
                    setTimeout(() => {
                        $('#edit_village').val(image.village);
                    }, 500);
                }, 500);
            }, 500);
        }, 500);

    } catch (error) {
        console.error('Error loading location data:', error);
    }
}

async function updateFieldImage() {
    const imageId = $('#edit_image_id').val();
    const formData = new FormData();

    const village = $('#edit_village').val();
    const category = $('#edit_category').val();
    const name = $('#edit_name').val();
    const imageFile = $('#edit_image')[0].files[0];

    if (!village || !category) {
        showMessage('Please fill all required fields', 'error');
        return;
    }

    formData.append('village', village);
    formData.append('category', category);
    if (name) formData.append('name', name);
    if (imageFile) formData.append('image', imageFile);

    try {
        const response = await fetch(`/en/api/field-images/${imageId}/`, {
            method: 'PUT',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });

        if (response.ok) {
            // $('#editFieldImageModal').modal('hide');
            closeModel('editFieldImageModal')
            await loadFieldImagesData();
            // window.location.reload()
            
            showMessage('Field image updated successfully', 'success');
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Error updating field image', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error updating field image', 'error');
    }
}

async function deleteFieldImage(id) {
    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to delete this field image?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#dc3545',
        confirmButtonText: gettext('Yes, delete it!')
    });

    if (!result.isConfirmed) return;

    try {
        const response = await fetch(`/en/api/field-images/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            showMessage('Field image deleted successfully', 'success');
            await loadFieldImagesData();
        } else {
            showMessage('Error deleting field image', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error deleting field image', 'error');
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
document.getElementById('sideBarToggler')?.addEventListener('click', () => {
    adjustDataTableColumns('field_images_table');
});


// Handle image click for preview
$('#field_images_table').on('click', '.preview-clickable', function () {
    const imageUrl = $(this).data('image');
    $('#preview_image').attr('src', imageUrl);
    $('#imagePreviewModal').modal('show');
});


// function closeModel(id)
// {
//     // $(`#${id}`).modal('hide');
//     const modalEl = document.getElementById(id);
//     const modal = bootstrap.Modal.getInstance(modalEl); // don't new Modal()
//     if (modal) {
//         modal.hide();
//     }
//     document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
//     // document.body.classList.remove('modal-open');
// //     document.body.style.removeProperty('padding-right');
// }


// function closeModel(id) {
//     $(`#${id}`).modal('hide');

//     // 🔹 Instead of removing the backdrop, just remove the "show" class
//     document.querySelectorAll('.modal-backdrop').forEach(el => {
//         el.classList.remove('show'); // fade stays, show goes away
//     });
// }

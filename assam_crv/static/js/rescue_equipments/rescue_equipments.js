let isAdministrator = null;


document.addEventListener('DOMContentLoaded', async function () {
    colorChange('rescue_equipment',"rescue_equipment_admin");

    // initializing each dropdown with select2
    initializeSelect2('rescue_equipment_district_select', gettext('Select Districts'));
    initializeSelect2('rescue_equipment_village_select', gettext('Select Villages'));
    initializeSelect2('rescue_equipment_circle', gettext('Select Circle'));
    initializeSelect2('rescue_equipment_gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('equipment', gettext('Select Equipment'));

    // This function will add the locations options in the select
    setupLocationSelectors('rescue_equipment_district_select','rescue_equipment_circle','rescue_equipment_gram_panchayat','rescue_equipment_village_select')
    
    /*
        if the this table is opening for the admin in the admin route then in url we will have the '/administrator/'if it is then we will add the actions column separately 
        to avoid conflict this js file is used in both the places so we have to check if the url contains the '/administrator/' or not
        if it contains then we will add the actions column
    */
    isAdministrator = window.location.href.includes('administrator');


    if (isAdministrator) {
        $('#rescue_equipment_table thead tr').append(`<th>${gettext('Actions')}</th>`);
    }

    const table_id = "rescue_equipment_table";
    // This the columns array we want in this we can add the width of the specific column
    const columns = [
        { title: gettext("S. No."), width: "5%" },
        { title: gettext("District") },
        { title: gettext("Village") },
        { title: gettext("Task Force") },
        { title: gettext("Equipment Name") },
        { title: gettext("Specification"), width: "30%" },
        { title: gettext("Count"), width: "10%" }
    ];

    if (isAdministrator) {
        columns.push({ title: gettext("Actions"), width: "150px" });
    }

    // initialize the data table and store the reference 
    rescueEquipmentTable = initializeDataTable(table_id, columns, {}, isAdministrator);

    // Load chart and summary functionality

    await getRescueList();
    await updateSummaryText(true);

    //adding onchange event handler to get filter data (escue analysis data)
    $('#rescue_equipment_district_select').on('change', handleFilterChange);
    $('#rescue_equipment_village_select').on('change', handleFilterChange);
    $('#rescue_equipment_circle').on('change', handleFilterChange);
    $('#rescue_equipment_gram_panchayat').on('change', handleFilterChange);
    $('#equipment').on('change', handleFilterChange);

    //function to get the list of Rescue equipment for the dropdown
    getRescueequipment();
});

let rescueEquipmentTable;


//this function will call each time whenever the district, village, circle , gram panchyat change, equipment changes and it will call getRescueList() to get the filtered list
async function handleFilterChange() {
    showSummaryLoader();

    const districtId = $('#rescue_equipment_district_select').val();
    const villageId = $('#rescue_equipment_village_select').val();
    const circle_id=$('#rescue_equipment_circle').val();
    const gram_panchayat_id=$('#rescue_equipment_gram_panchayat').val();
    const equipment_id=$('#equipment').val();
    
    await loadRescueEquipmentChartData();
    await getRescueList(villageId, districtId,circle_id,gram_panchayat_id,equipment_id);
    await updateSummaryText(true);
}

async function getRescueList(village = null, district = null,circle_id=null,gram_panchayat_id=null,equipment_id=null) {
    console.log("getRescueList called");
        try {
        // Show table loader
        showTableLoader();
        
        let url = `${isAdministrator?'/api/admin_get_rescue_equipment_status':'/api/get_rescue_equipment_status'}`;
        const params = new URLSearchParams();
        
        if (village) params.append('village_id', village);
        if (district) params.append('district_id', district);
        if (circle_id) params.append('circle_id', circle_id);
        if (gram_panchayat_id) params.append('gram_panchayat_id', gram_panchayat_id);
        if (equipment_id) params.append('equipment_id', equipment_id);
        
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const fetchOptions = {};
        if (isAdministrator) {
            fetchOptions.headers = {
                'X-CSRFToken': getCSRFToken()
            };
        }
        
        let api_res = await fetch(url, fetchOptions);
        let json_res = await api_res.json();

        console.log(json_res);
        
        if (json_res && json_res) {
            rescueEquipmentData = json_res;
            populateRescueEquipmentTable(json_res);
        }
    } catch (error) {
        console.log(error);
        hideTableLoader();
    }
}

function showTableLoader() {
    if (rescueEquipmentTable) {
        rescueEquipmentTable.clear();
        const loaderRow = [
            '<div class="text-center"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading data...</div>',
            '', '', '', '', '', ''
        ];
        
        // Add empty column for Actions if administrator
        if (isAdministrator) {
            loaderRow.push('');
        }
        
        rescueEquipmentTable.row.add(loaderRow).draw();
    }
}

function hideTableLoader() {
    // Loader is hidden when table populates
}

// Action functions for edit and delete
function editRescueEquipment(id) {
    // Find the item data by id
    const item = rescueEquipmentData.find(item => item.id === id);
    if (item) {
        $('#editStatusId').val(id);
        $('#editEquipmentName').val(item.equipment_name || '');
        $('#editTaskForce').val(item.equipment_task_force || '');
        $('#editVillageName').val(item.village_name || '');
        $('#editDistrictName').val(item.district_name || '');
        $('#editSpecification').val(item.equipment_specification || '');
        $('#editCount').val(item.count || 0);
        
        // Format date
        if (item.last_update) {
            const date = new Date(item.last_update);
            $('#editLastUpdate').val(date.toLocaleString());
        }
    }
    // Manually trigger modal
    $('#editRescueStatusModal').modal('show');
}

function deleteRescueEquipment(id) {
    $('#deleteRecordId').val(id);
    // Manually trigger modal
    $('#deleteConfirmModal').modal('show');
}

async function submitEditRescueStatus() {
    const result = await Swal.fire({
        title: gettext('Are you sure?'),
        text: gettext('Do you really want to update this data?'),
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#245FAE',
        cancelButtonColor: '#dc3545',
        confirmButtonText: gettext('Yes, update it!')
    });

    if (!result.isConfirmed) return;

    const id = $('#editStatusId').val();
    const count = $('#editCount').val();

    try {
        const response = await fetch(`/api/update_rescue_equipment_status/${id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ count: parseInt(count) })
        });

        const apiResult = await response.json();

        if (response.ok) {
            $('#editRescueStatusModal').modal('hide');
            await getRescueList();
            Swal.fire(gettext('Updated!'), gettext('Equipment status updated successfully!'), 'success');
        } else {
            Swal.fire(gettext('Error!'), apiResult.error || gettext('Failed to update'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire(gettext('Error!'), gettext('Failed to update equipment status'), 'error');
    }
}

async function confirmDeleteRecord() {
    const id = $('#deleteRecordId').val();

    try {
        const response = await fetch(`/api/delete_rescue_equipment_status/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const result = await response.json();

        if (response.ok) {
            $('#deleteConfirmModal').modal('hide');
            await getRescueList();
            Swal.fire(gettext('Deleted!'), gettext('Equipment status deleted successfully!'), 'success');
        } else {
            Swal.fire(gettext('Error!'), result.error || gettext('Failed to delete'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire(gettext('Error!'), gettext('Failed to delete equipment status'), 'error');
    }
}

let rescueEquipmentData = [];

function populateRescueEquipmentTable(data) {
    const isAdministrator = window.location.href.includes('administrator');
    
    // Clear loader first
    if (rescueEquipmentTable) {
        rescueEquipmentTable.clear();
    }
    
    const rowMapper = (item, index) => [
        index + 1,
        item.district_name || '',
        item.village_name || '',
        item.equipment_task_force || '',
        item.equipment_name || '',
        item.equipment_specification || '',
        item.count || 0
    ];
    
    const actionsMapper = (item) => {
        return generateActionButtons(item.id, 'editRescueEquipment', 'deleteRescueEquipment');
    };
    
    populateDataTable(rescueEquipmentTable, data, rowMapper, isAdministrator, actionsMapper);
}


// Function to reload table data
function reloadRescueEquipmentTable() {
    rescueEquipmentTable.ajax.reload(null, false);
    adjustDataTableColumns('rescue_equipment_table');
}

// This function is for the adjustment of the tables when user open or close the side nav bar 
document.getElementById('sideBarToggler').addEventListener('click',()=>{
      adjustDataTableColumns('rescue_equipment_table_master')
    adjustDataTableColumns('rescue_equipment_table')
})

async function getRescueequipment(){
    try {
        let api_res=await fetch('/api/dropdown_rescue_equipment/');
        let json_res=await api_res.json();
        if(json_res && json_res.length>0){
            let option=`<option value="">Select Equipment</option>`
            json_res.map((item)=>{
                option+=`<option value="${item.id}">${item.name}</option>`
            })
            $("#equipment").html(option)
        }
    } catch (error) {
        console.log("error",error)
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadEquipmentsDropdown(); // chart checkboxes
    await getRescueequipment();     // table select (all selected)
    await loadRescueEquipmentChartData(); // chart loads correctly
});

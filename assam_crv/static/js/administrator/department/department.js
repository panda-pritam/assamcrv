let departmentTable;
let departmentData = [];
let isAdministrator = null;
let allModules = [];

// Move selected permissions
function moveSelected(fromId, toId) {
  const from = document.getElementById(fromId);
  const to = document.getElementById(toId);

  Array.from(from.selectedOptions).forEach(option => {
    option.selected = false;
    to.appendChild(option);
  });
}

// Clear selections
function clearPermissionSelections() {
  document.getElementById('availablePermissions').selectedIndex = -1;
  document.getElementById('chosenPermissions').selectedIndex = -1;
}

// Load modules from JSON script block
function loadModules() {
  const jsonScript = document.getElementById('modules-json');
  if (jsonScript && jsonScript.textContent) {
    try {
      allModules = JSON.parse(jsonScript.textContent);
      console.log("✅ Loaded modules:", allModules);
    } catch (err) {
      console.error("Error parsing modules JSON:", err);
    }
  }
}

// Reset and populate permission select boxes
function resetPermissionSelects() {
  const available = document.getElementById('availablePermissions');
  const chosen = document.getElementById('chosenPermissions');
  available.innerHTML = '';
  chosen.innerHTML = '';

  allModules.forEach(mod => {
    const opt = document.createElement('option');
    opt.value = mod.id;
    opt.textContent = mod.name;
    available.appendChild(opt);
  });
}

// Move specific module IDs to chosenPermissions
function preselectPermissions(moduleIds) {
  const available = document.getElementById('availablePermissions');
  const chosen = document.getElementById('chosenPermissions');

  const optionsToMove = [];

  Array.from(available.options).forEach(opt => {
    if (moduleIds.includes(parseInt(opt.value))) {
      optionsToMove.push(opt);
    }
  });

  optionsToMove.forEach(opt => chosen.appendChild(opt));
}

// CSRF Token getter
function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Get department list
async function getDepartmentList() {
  try {
    let res = await fetch("/api/departments/");
    let data = await res.json();
    if (data) {
      departmentData = data;
      populateDepartmentTable(data);
    }
  } catch (err) {
    console.error("Failed to fetch departments:", err);
  }
}

// Render data in table
function populateDepartmentTable(data) {
  const rowMapper = (item, index) => [
    index + 1,
    item.name || '',
    item.name_bn || '-',
    item.name_as || '-',
    item.details || '-'
  ];

  const actionsMapper = (item) => {
    return generateActionButtons(item.id, 'editDepartment', 'deleteDepartment');
  };

  populateDataTable(departmentTable, data, rowMapper, isAdministrator, actionsMapper);
}

// Edit department handler
function editDepartment(id) {
  const item = departmentData.find(dep => dep.id === id);
  if (!item) return;

  document.getElementById('departmentId').value = item.id;
  document.getElementById('departmentName').value = item.name || '';
  document.getElementById('departmentNameBn').value = item.name_bn || '';
  document.getElementById('departmentNameAs').value = item.name_as || '';
  document.getElementById('departmentDetails').value = item.details || '';
  document.getElementById('departmentModalLabel').textContent = gettext('Edit Department');
  document.getElementById('submitBtn').textContent = gettext('Update');

  resetPermissionSelects(); // ✅ repopulate availablePermissions

  const moduleIds = (item.module_permissions || item.permissions || []).map(id => parseInt(id));
  preselectPermissions(moduleIds); // ✅ only move assigned ones to chosen

  $('#departmentModal').modal('show');
}

// Delete confirmation handler
function deleteDepartment(id) {
  Swal.fire({
    title: gettext('Are you sure?'),
    text: gettext('Do you really want to delete this department?'),
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#245FAE',
    cancelButtonColor: '#dc3545',
    confirmButtonText: gettext('Yes, delete it!')
  }).then(async (result) => {
    if (result.isConfirmed) {
      await confirmDeleteDepartment(id);
    }
  });
}

// Confirm deletion
async function confirmDeleteDepartment(id) {
  try {
    const response = await fetch(`/en/api/departments/${id}/delete/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });

    if (response.status === 204) {
      await reloadDepartmentsAndPermissions();
      Swal.fire(gettext('Deleted!'), gettext('Department deleted successfully!'), 'success');
    } else {
      const result = await response.json();
      Swal.fire(gettext('Error!'), result.error || gettext('Failed to delete'), 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    Swal.fire(gettext('Error!'), gettext('Failed to delete department.'), 'error');
  }
}

// Save department
async function saveDepartment() {
  const confirm = await Swal.fire({
    title: gettext('Are you sure?'),
    text: gettext('Do you really want to save this department?'),
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#245FAE',
    cancelButtonColor: '#dc3545',
    confirmButtonText: gettext('Yes, save it!')
  });

  if (!confirm.isConfirmed) return;

  const form = document.getElementById('departmentForm');
  const formData = new FormData(form);
  const id = formData.get("department_id");

  const permissionSelect = document.getElementById('chosenPermissions');
  const selectedModules = Array.from(permissionSelect.options).map(opt => opt.value);

  formData.delete('permissions[]');
  formData.delete('permissions');
  selectedModules.forEach(val => formData.append('permissions', val));

  const url = id ? `/en/api/departments/${id}/update/` : '/en/api/departments/create/';
  const method = id ? 'PATCH' : 'POST';

  try {
    const response = await fetch(url, {
      method,
      body: formData,
      headers: {
        'X-CSRFToken': getCSRFToken()
      }
    });

    const data = await response.json();

    if (response.ok) {
      $('#departmentModal').modal('hide');
      resetForm();
      await reloadDepartmentsAndPermissions();
      Swal.fire(gettext('Success!'), gettext('Department saved successfully!'), 'success');
    } else {
      Swal.fire(gettext('Error!'), data.error || gettext('Something went wrong.'), 'error');
    }
  } catch (error) {
    console.error('Save error:', error);
    Swal.fire(gettext('Error!'), gettext('Failed to save department.'), 'error');
  }
}

// Reset modal form
function resetForm() {
  document.getElementById('departmentForm').reset();
  document.getElementById('departmentId').value = '';
  clearPermissionSelections();
}

// Reload departments and re-render
async function reloadDepartmentsAndPermissions() {
  await getDepartmentList();
  resetPermissionSelects(); // ✅ no call to moveUsedPermissionsToChosen
}

// Open modal
window.openModal = function () {
  resetForm();
  resetPermissionSelects(); // ✅ ensures availablePermissions is reset
  document.getElementById('departmentModalLabel').textContent = gettext('Add New Department');
  document.getElementById('submitBtn').textContent = gettext('Submit');
  $('#departmentModal').modal('show');
};

// DOM Ready
document.addEventListener('DOMContentLoaded', async function () {
  isAdministrator = window.location.href.includes('administrator');
colorChange('departments','departments');

  loadModules();
  if (!allModules.length) {
    console.warn(gettext("⚠️ No modules loaded. Cannot proceed with permission assignment."));
    return;
  }

  resetPermissionSelects();

  if (isAdministrator) {
    $('#departments_table thead tr').append(`<th>${gettext('Actions')}</th>`);
  }

  const table_id = "departments_table";
  const columns = [
    { title: gettext("Sr. No"), width: "5%" },
    { title: gettext("Name"), width: "20%" },
    { title: gettext("Name (Bengali)"), width: "15%" },
    { title: gettext("Name (Assamese)"), width: "15%" },
    { title: gettext("Details"), width: "25%" }
  ];
  if (isAdministrator) columns.push({ title: gettext("Actions"), width: "20%" });

  departmentTable = initializeDataTable(table_id, columns, {}, isAdministrator);

  await reloadDepartmentsAndPermissions();

  document.getElementById('departmentForm').addEventListener('submit', function (e) {
    e.preventDefault();
    saveDepartment();
  });

  const departmentModal = document.getElementById('departmentModal');
  departmentModal.addEventListener('hidden.bs.modal', function () {
    clearPermissionSelections();
    resetPermissionSelects();
  });
});

// Sidebar toggler
document.getElementById('sideBarToggler')?.addEventListener('click', () => {
  adjustDataTableColumns('departments_table');
});

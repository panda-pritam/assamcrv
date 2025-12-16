

let table;

document.addEventListener('DOMContentLoaded', async function () {
    colorChange('users','users');

    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('circle', gettext('Select Circle'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('village', gettext('Select Villages'));

    setupLocationSelectors('district_val', 'circle_val', 'gram_panchayat_val', 'village_val');
    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');

    // Initialize table using common utility
    const columns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("Department") },
        { title: gettext("Role") },
        { title: gettext("Username") },
        { title: gettext("District") },
        { title: gettext("Circle") },
        { title: gettext("Gram Panchayat") },
        { title: gettext("Village") },
        { title: gettext("Actions"), width: "10%" }
    ];
    table = initializeDataTable('users_data_table', columns, {}, true);

    // Initial load
    await loadUsersData(getFilters());
    updateSummaryText(true)

    // Listeners
    $('#district, #circle, #gram_panchayat, #village').on('change', () => {
        loadUsersData(getFilters());
        updateSummaryText(true);
    });

    function getFilters() {
        const filters = {
            district_id: $('#district').val(),
            circle_id: $('#circle').val(),
            gram_panchayat_id: $('#gram_panchayat').val(),
            village_id: $('#village').val(),
        };

        return Object.fromEntries(
            Object.entries(filters).filter(([_, val]) => val && val !== '')
        );
    }

    async function loadUsersData(params = {}) {
        try {
            let url = '/api/users_list/';
            const query = new URLSearchParams(params).toString();
            if (query) url += `?${query}`;

            const response = await fetch(url);
            const data = await response.json();
            console.log('API Response:', data);

            // Use common utility function to populate table
            populateDataTable(table, data, userRowMapper, true, userActionsMapper);
        } catch (error) {
            console.error('Error loading user data:', error);
            table.clear().draw();
        }
    }

    // Row mapper function for user data
    function userRowMapper(item, index) {
        return [
            index + 1,
            item.department_name || '',
            item.role_name || '',
            item.username || '',
            item.district_name || '',
            item.circle_name || '',
            item.gram_panchayat_name || '',
            item.village_name || ''
        ];
    }

    // Actions mapper function for user data
    function userActionsMapper(item) {
        return `
            <button type="button"
                class="table_edit_Btn btn-view-details"
                data-id="${item.id}"
                data-username="${item.username}"
                data-role-id="${item.role}"
                data-district-id="${item.district || ''}"
                data-circle-id="${item.circle || ''}"
                data-gram-panchayat-id="${item.gram_panchayat || ''}"
                data-village-id="${item.village || ''}"
                data-first-name="${item.first_name || ''}"
                data-last-name="${item.last_name || ''}"
                data-email="${item.email || ''}"
                data-mobile="${item.mobile || ''}"
                data-is-active="${item.is_active || ''}"
                data-department-id="${item.department || ''}"
                data-bs-toggle="modal"
                data-bs-target="#registerUserModal">
                <i class="fa-solid fa-eye"></i>
            </button>
            <button type="button"
                class="table_edit_Btn btn-edit-user"
                data-id="${item.id}"
                data-username="${item.username}"
                data-role-id="${item.role}"
                data-district-id="${item.district || ''}"
                data-circle-id="${item.circle || ''}"
                data-gram-panchayat-id="${item.gram_panchayat || ''}"
                data-village-id="${item.village || ''}"
                data-first-name="${item.first_name || ''}"
                data-last-name="${item.last_name || ''}"
                data-email="${item.email || ''}"
                data-mobile="${item.mobile || ''}"
                data-is-active="${item.is_active || ''}"
                data-department-id="${item.department || ''}"
                data-bs-toggle="modal"
                data-bs-target="#registerUserModal">
                <i class="fa-solid fa-pen-to-square"></i>
            </button>
            <button type="button" class="table_Delete_Btn" onclick="confirmstatusDelete(${item.id})">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
    }

    $('#role').on('change', function () {
        const selectedOption = $(this).find('option:selected');
        const roleName = selectedOption.data('role-name');
        role_change(roleName);
    });

    function role_change(role) {
        // Hide all first
        document.getElementById('district_div').style.display = 'none';
        document.getElementById('circle_div').style.display = 'none';
        document.getElementById('gram_panchayat_div').style.display = 'none';
        document.getElementById('village_div').style.display = 'none';

        // Show based on role
        if (role === 'DDMA') {
            document.getElementById('district_div').style.display = 'block';
            document.getElementById('district_val').value = '';

        } else if (role === 'Circle Officer') {
            document.getElementById('district_div').style.display = 'block';
            document.getElementById('circle_div').style.display = 'block';
            document.getElementById('district_val').value = '';
            document.getElementById('circle_val').value = '';
        } else if (role === 'Gram Panchayat Officer') {
            document.getElementById('district_div').style.display = 'block';
            document.getElementById('circle_div').style.display = 'block';
            document.getElementById('gram_panchayat_div').style.display = 'block';
            document.getElementById('district_val').value = '';
            document.getElementById('circle_val').value = '';
            document.getElementById('gram_panchayat_val').value = '';
        } else if (role === 'Village Officer') {
            document.getElementById('district_div').style.display = 'block';
            document.getElementById('circle_div').style.display = 'block';
            document.getElementById('gram_panchayat_div').style.display = 'block';
            document.getElementById('village_div').style.display = 'block';
            document.getElementById('district_val').value = '';
            document.getElementById('circle_val').value = '';
            document.getElementById('gram_panchayat_val').value = '';
            document.getElementById('village_val').value = '';
        }
    }

    let editingUserId = null;

    // Handle Edit
    $(document).on('click', '.btn-edit-user', function () {
        const userData = extractUserData($(this));
        fillUserForm(userData);
        setFormReadOnly(false);
        editingUserId = userData.id;
        $('#registerUserModalLabel').text(gettext('Edit User'));
        $('#registerUserBtn').show().text(gettext('Update'));
    });

    // Handle View
    $(document).on('click', '.btn-view-details', function () {
        const userData = extractUserData($(this));
        fillUserForm(userData);
        setFormReadOnly(true);
        editingUserId = null;
        $('#registerUserModalLabel').text(gettext('View User Details'));
        $('#registerUserBtn').hide();
    });

    // Reset on Modal Close
    $('#registerUserModal').on('hidden.bs.modal', function () {
        $('#registerUserForm')[0].reset();
        $('#role').val('').trigger('change');
        editingUserId = null;
        setFormReadOnly(false);
        $('#registerUserBtn').show().text(gettext('Register'));
        $('#registerUserModalLabel').text(gettext('Register New User'));
    });

    $('#registerUserForm').on('submit', async function (e) {
        e.preventDefault();

        const formData = {};
        const getValue = (id) => $(`#${id}`).val();

        // Always-required fields
        const requiredFields = ['username', 'first_name', 'last_name', 'email', 'role', 'department'];
        requiredFields.forEach(field => {
            const value = getValue(field);
            if (value) formData[field] = value;
        });

        // Optional fields
        const optionalFields = ['mobile', 'district_val', 'circle_val', 'gram_panchayat_val', 'village_val' ];
        optionalFields.forEach(field => {
            const value = getValue(field);
            if (value) {
                // use cleaned key names
                const key = field.replace('_val', '');
                formData[key] = value;
            }
        });

        // Password condition (only if adding or edited with new value)
        const passwordValue = $('#password').val();
        if (!editingUserId || (passwordValue && passwordValue !== '********')) {
            formData.password = passwordValue;
        }

        const url = editingUserId
            ? `/en/api/users/${editingUserId}/update/`
            : '/en/api/register_user/';
        const method = editingUserId ? 'PATCH' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: editingUserId ? gettext('User Updated') : gettext('User Registered'),
                    text: editingUserId
                        ? gettext('The user has been updated successfully.')
                        : gettext('The user has been registered successfully.'),
                    confirmButtonColor: '#245FAE'
                }).then(() => {
                    $('#registerUserModal').modal('hide');
                    $('#registerUserForm')[0].reset();
                    loadUsersData(); // Refresh table
                    window.location.reload();
                });
            } else {
                const errorMsg = Object.values(result).flat().join(', ');
                Swal.fire({
                    icon: 'error',
                    title: gettext('Operation Failed'),
                    text: errorMsg || gettext('Please check the form data.'),
                    confirmButtonColor: '#dc3545'
                });
            }
        } catch (error) {
            console.error('Request failed', error);
            Swal.fire({
                icon: 'error',
                title: gettext('Server Error'),
                text: gettext('An unexpected error occurred. Try again later.'),
                confirmButtonColor: '#dc3545'
            });
        }
    });



    // Helpers

    function extractUserData($btn) {
        return {
            id: $btn.data('id'),
            username: $btn.data('username'),
            role: $btn.data('role-id'),
            district: $btn.data('district-id'),
            circle: $btn.data('circle-id'),
            gram_panchayat: $btn.data('gram-panchayat-id'),
            village: $btn.data('village-id'),
            first_name: $btn.data('first-name'),
            last_name: $btn.data('last-name'),
            email: $btn.data('email'),
            mobile: $btn.data('mobile'),
            department: $btn.data('department-id'),
        };
    }

    async function fillUserForm(data) {
        $('#username').val(data.username);
        $('#password').val('********');
        $('#first_name').val(data.first_name);
        $('#last_name').val(data.last_name);
        $('#email').val(data.email);
        $('#mobile').val(data.mobile);
        $('#role').val(data.role).trigger('change');
        $('#department').val(data.department).trigger('change');

        const selectedRole = $('#role option:selected').data('role-name');
        role_change(selectedRole); // Show/hide location dropdowns

        await waitForOptionsToLoad('#district_val');
        $('#district_val').val(data.district).trigger('change');

        await waitForOptionsToLoad('#circle_val');
        $('#circle_val').val(data.circle).trigger('change');

        await waitForOptionsToLoad('#gram_panchayat_val');
        $('#gram_panchayat_val').val(data.gram_panchayat).trigger('change');

        await waitForOptionsToLoad('#village_val');
        $('#village_val').val(data.village);
    }

    function setFormReadOnly(readOnly) {
        $('#registerUserForm input, #registerUserForm select').prop('disabled', readOnly);
    }

    function waitForOptionsToLoad(selector, timeout = 3000) {
        return new Promise((resolve, reject) => {
            const start = Date.now();
            const check = () => {
                if ($(selector).children('option').length > 1) {
                    resolve();
                } else if (Date.now() - start > timeout) {
                    reject(`Timeout while waiting for ${selector}`);
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    }

});

document.getElementById('sideBarToggler').addEventListener('click',()=>{
      adjustDataTableColumns('users_data_table')
    
})
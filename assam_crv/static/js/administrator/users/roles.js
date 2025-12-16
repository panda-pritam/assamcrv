// document.addEventListener('DOMContentLoaded', function () {
//     colorChange('roles');

//     // Initialize DataTable
//     $('#roles_table').DataTable({
//         pageLength: 10,
//         lengthMenu: [5, 10, 25, 50],
//         ordering: true,
//         searching: true,
//         info: true,
//         paging: true
//     });

//     // Handle form submission
//     $('#roleForm').on('submit', function (e) {
//         e.preventDefault();

//         const roleId = $('#roleId').val();
//         const isEdit = !!roleId;

//         const url = isEdit
//             ? `/en/api/role/${roleId}/update/`
//             : `/en/api/create_role/`;

//         const method = isEdit ? 'PATCH' : 'POST';
//         const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

//         const payload = {
//             name: $('#roleName').val(),
//             name_bn: $('#roleNameBn').val(),
//             name_as: $('#roleNameAs').val(),
//             details: $('#roleDetails').val()
//         };

//         fetch(url, {
//             method: method,
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': csrfToken
//             },
//             body: JSON.stringify(payload)
//         })
//         .then(response => response.json().then(data => ({ status: response.status, data })))
//         .then(({ status, data }) => {
//             if (status === 200 || status === 201) {
//                 Swal.fire({
//                     icon: 'success',
//                     title: isEdit ? 'Role Updated' : 'Role Created',
//                     text: `Role has been ${isEdit ? 'updated' : 'created'} successfully!`,
//                 }).then(() => {
//                     $('#roleModal').modal('hide');
//                     location.reload();
//                 });
//             } else {
//                 const errorMsg = Object.values(data).flat().join(', ');
//                 Swal.fire({
//                     icon: 'error',
//                     title: 'Operation Failed',
//                     text: errorMsg || 'Please check the form input.',
//                 });
//             }
//         })
//         .catch(error => {
//             console.error('Error:', error);
//             Swal.fire({
//                 icon: 'error',
//                 title: 'Server Error',
//                 text: 'Something went wrong. Please try again later.',
//             });
//         });
//     });
// });

// // Opens modal in "Add New Role" mode
// function openModal() {
//     resetForm();
//     $('#roleModalLabel').text('Add New Role');
//     $('#submitBtn').text('Submit');
//     $('#roleModal').modal('show');
// }

// // Populates modal with data for editing
// function editRole(id, name, nameBn, nameAs, details) {
//     $('#roleId').val(id);
//     $('#roleName').val(name);
//     $('#roleNameBn').val(nameBn || '');
//     $('#roleNameAs').val(nameAs || '');
//     $('#roleDetails').val(details || '');
//     $('#roleModalLabel').text('Edit Role');
//     $('#submitBtn').text('Update');
//     $('#roleModal').modal('show');
// }

// // Clears the form and hidden field
// function resetForm() {
//     $('#roleForm')[0].reset();
//     $('#roleId').val('');
// }

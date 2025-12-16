document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    // console.log("JS LOADED")
    // Save profile changes
    document.getElementById('saveProfileBtn').addEventListener('click', function() {
        // console.log("JS LOADED saveProfileBtn")

        const firstName = document.getElementById('firstName').value;
        const lastName = document.getElementById('lastName').value;
        const email = document.getElementById('email').value;
        const mobile = document.getElementById('mobile').value;
        const username = document.getElementById('username').value;

        // Validate inputs
        if (!firstName || !lastName || !email || !mobile) {
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('All fields are required!')
            });
            return;
        }

fetch('/en/api/update-profile/', {
    method: 'PATCH',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
        username: username,
        first_name: firstName,
        last_name: lastName,
        email: email,
        mobile: mobile
    })
})
.then(async response => {
    const data = await response.json();
    if (response.status === 200) {
        Swal.fire({
            icon: 'success',
            title: gettext('Success'),
            text: gettext('Profile updated successfully!')
        }).then(() => {
            window.location.reload();
        });
    } else {
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: data.message || gettext('Failed to update profile')
        });
    }
})
.catch(error => {
    console.error('Error:', error);
    Swal.fire({
        icon: 'error',
        title: gettext('Error'),
        text: gettext('An error occurred while updating profile')
    });
});

    });

    // Change password
    document.getElementById('changePasswordBtn').addEventListener('click', function() {
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // Validate inputs
        if (!currentPassword || !newPassword || !confirmPassword) {
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('All fields are required!')
            });
            return;
        }

        if (newPassword !== confirmPassword) {
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('New password and confirm password do not match!')
            });
            return;
        }

fetch('/en/api/change-password/', {
    method: 'PATCH',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
        old_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
    })
})
.then(response =>
    response.json().then(data => ({
        status: response.status,
        body: data
    }))
)
.then(({ status, body }) => {
    if (status === 200) {
        Swal.fire({
            icon: 'success',
            title: gettext('Success'),
            text: gettext('Password changed successfully!')
        }).then(() => {
            window.location.reload();
        });
    } else {
        Swal.fire({
            icon: 'error',
            title: gettext('Error'),
            text: body.message || gettext('Failed to change password')
        });
    }
})
.catch(error => {
    console.error('Error:', error);
    Swal.fire({
        icon: 'error',
        title: gettext('Error'),
        text: gettext('An error occurred while changing password')
    });
});

    });
});
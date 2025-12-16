document.addEventListener('DOMContentLoaded', function () {

    colorChange("vdmp_dashboard", 'vdmp_dashboard_admin');

    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');

    document.getElementById("uploadnewdata").addEventListener("click", function (e) {
        e.preventDefault();

        const fileInput = document.getElementById("fileInput").files[0];
        const dataType = document.getElementById("dataType").value;
        const button = this;
        const originalText = button.innerHTML;

        if (!fileInput || !dataType) {
            Swal.fire("Error", "Please select a file and data type.", "error");
            return;
        }

        Swal.fire({
            title: "Are you sure?",
            text: "Do you want to upload this file?",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Yes, upload it!",
            cancelButtonText: "Cancel"
        }).then((result) => {
            if (result.isConfirmed) {
                button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
                button.disabled = true;

                const formData = new FormData();
                formData.append("file", fileInput);
                formData.append("data_type", dataType);

                fetch("/en/api/upload_data_vdmp", {
                    method: "POST",
                    body: formData
                })
                .then(response => response.json())
                .then(response => {
                    if (response.status === "success") {
                        const created = response.records_created || 0;
                        const updated = response.records_updated || 0;
                        const rejected = response.errors ? response.errors.length : 0;
                        const total = created + updated;
                        
                        Swal.fire({
                            title: "Upload Summary",
                            html: `<div style="text-align: left;">
                                    <p><strong>📊 Total Processed:</strong> ${total + rejected}</p>
                                    <p><strong>✅ Records Created:</strong> ${created}</p>
                                    <p><strong>🔄 Records Updated:</strong> ${updated}</p>
                                    <p><strong>❌ Records Rejected:</strong> ${rejected}</p>
                                    ${rejected > 0 ? '<p><small>Rejected records have invalid village codes or errors</small></p>' : ''}
                                   </div>`,
                            icon: rejected > 0 ? "warning" : "success"
                        });
                        document.getElementById("fileInput").value = '';
                        document.getElementById("dataType").value = '';
                    } else {
                        const errorCount = response.errors ? response.errors.length : 0;
                        Swal.fire({
                            title: "Upload Failed",
                            html: `<div style="text-align: left;">
                                    <p><strong>❌ Error:</strong> ${response.error || "Upload failed"}</p>
                                    ${errorCount > 0 ? `<p><strong>📊 Total Errors:</strong> ${errorCount}</p>` : ''}
                                   </div>`,
                            icon: "error"
                        });
                    }
                })
                .catch(error => {
                    Swal.fire({
                        title: "Upload Failed",
                        html: `<div style="text-align: left;">
                                <p><strong>❌ Error:</strong> Network or server error</p>
                                <p><small>Please check your connection and try again</small></p>
                               </div>`,
                        icon: "error"
                    });
                })
                .finally(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                });
            }
        });
    });

    const deleteDiv = document.getElementById("deletdiv");

    const radioUpload = document.getElementById("upload_data");
    const radioDelete = document.getElementById("delete_data");
    const uploadDiv=document.getElementById("uploadDiv")
    console.log("upload div -> ",uploadDiv)

    function toggleDivs() {
        if (radioUpload.checked) {
            uploadDiv.style.display = "block";
            deleteDiv.style.display = "none";
        } else if (radioDelete.checked ) {
            uploadDiv.style.display = "none";
            deleteDiv.style.display = "block";
        }
    }

    // Initial display
    toggleDivs();

    // Add change listeners
    radioUpload.addEventListener("change", toggleDivs);
    radioDelete.addEventListener("change", toggleDivs);
});

document.getElementById("deletedata").addEventListener("click", function (e) {
    e.preventDefault();

    const dataType = document.getElementById("deletedataType").value;
    const village = document.getElementById("village").value;
    const button = this;
    const originalText = button.innerHTML;

    if (!dataType || !village) {
        Swal.fire({
            icon: 'warning',
            title: 'Missing Information',
            text: 'Please select both Data Type and Village.',
        });
        return;
    }

    Swal.fire({
        title: 'Are you sure?',
        text: "Do you really want to delete the selected data?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loader in button
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deleting...';
            button.disabled = true;

            const formData = new FormData();
            formData.append("data_type", dataType);
            formData.append("village_id", village);

            fetch("/en/api/delete_vdmp_data", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                },
                body: formData,
            })
            .then((res) => res.json())
            .then((data) => {
                if (data.status === "success") {
                    Swal.fire({
                        icon: 'success',
                        title: 'Deleted!',
                        text: data.message,
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error!',
                        text: data.message || "An error occurred during deletion.",
                    });
                }
            })
            .catch(() => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error!',
                    text: 'Something went wrong. Please try again later.',
                });
            })
            .finally(() => {
                // Restore button
                button.innerHTML = originalText;
                button.disabled = false;
            });
        }
    });
});



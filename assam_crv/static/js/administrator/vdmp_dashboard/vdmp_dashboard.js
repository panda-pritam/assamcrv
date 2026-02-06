let uploadCatalog = null;
let uploadTypeToCategory = {};
let isSyncingCategory = false;
let uploadTypeFileCounts = {};
let uploadTypeSelectionLevels = {};
let uploadLocationSelectorsReady = false;

const allowedUploadTypes = new Set([
    "household",
    "transformer",
    "critical_facility",
    "commercial",
    "electric_poles",
    "villagesOfAllTheDistricts",
    "VillageRoadInfo",
    "VillageRoadInfoErosion",
    "bridge_survey",
    "risk_assesment",
    "pra_main",
    "pra_assets",
    "pra_shelter",
    "fgd_wash_summary",
    "fgd_livelihood_summary",
    "line_department",
    "photos",
    "hazard"
]);

const uploadTypeMap = {
    "household": "household",
    "transformer": "transformer",
    "critical facility": "critical_facility",
    "critical facilities": "critical_facility",
    "commercial": "commercial",
    "electric pole": "electric_poles",
    "electric poles": "electric_poles",
    "villages of all the districts": "villagesOfAllTheDistricts",
    "villages road info": "VillageRoadInfo",
    "village road erosion info.": "VillageRoadInfoErosion",
    "bridge": "bridge_survey",
    "bridge survey": "bridge_survey",
    "risk assesment": "risk_assesment",
    "pra main": "pra_main",
    "pra assests": "pra_assets",
    "pra assets": "pra_assets",
    "pra shelter": "pra_shelter",
    "fgd on wash": "fgd_wash_summary",
    "fgd wash summary": "fgd_wash_summary",
    "fgd on livelihood": "fgd_livelihood_summary",
    "fgd livelihood summary": "fgd_livelihood_summary",
    "line department": "line_department"
};

function normalizeTypeValue(value) {
    return (value || "").trim().toLowerCase().replace(/\s+/g, " ");
}

function normalizeSelectionLevel(value) {
    return (value || "").trim().toLowerCase();
}

function resolveUploadDataType(value) {
    if (allowedUploadTypes.has(value)) {
        return value;
    }
    const selectedCategory = (document.getElementById("uploadCategory")?.value || "").toLowerCase();
    if (selectedCategory === "photos") {
        return "photos";
    }
    if (selectedCategory === "hazard") {
        return "hazard";
    }
    const normalized = normalizeTypeValue(value);
    const mapped = uploadTypeMap[normalized];
    if (mapped && allowedUploadTypes.has(mapped)) {
        return mapped;
    }
    if ((uploadTypeToCategory[value] || "").toLowerCase() === "photos") {
        return "photos";
    }
    return null;
}

function populateCategorySelect(categories) {
    const select = document.getElementById("uploadCategory");
    if (!select) return;
    const placeholder = select.querySelector("option[disabled]")?.textContent || "Choose Category";
    let options = `<option value="" selected disabled>${placeholder}</option>`;
    categories.forEach((item) => {
        options += `<option value="${item.value}">${item.label}</option>`;
    });
    select.innerHTML = options;
}

function populateTypeSelect(types) {
    const select = document.getElementById("dataType");
    if (!select) return;
    const placeholder = select.querySelector("option[disabled]")?.textContent || "Choose Data Type";
    let options = `<option value="" selected disabled>${placeholder}</option>`;
    types.forEach((typeName) => {
        options += `<option value="${typeName}">${typeName}</option>`;
    });
    select.innerHTML = options;
}

function updateUploadTypesForCategory() {
    if (!uploadCatalog) return;
    const category = document.getElementById("uploadCategory")?.value;
    if (!category) {
        populateTypeSelect(uploadCatalog.types);
        setFileInputAccepts(".csv,.xlsx,.xls");
        setFileInputCount(1);
        updateUploadLocationFilters();
        return;
    }
    populateTypeSelect(uploadCatalog.mapping[category] || []);
    const normalizedCategory = (category || "").toLowerCase();
    if (normalizedCategory === "photos") {
        setFileInputAccepts("image/*");
    } else if (normalizedCategory === "hazard") {
        setFileInputAccepts(".jpg,.jpeg,.png,.tif,.tiff");
    } else {
        setFileInputAccepts(".csv,.xlsx,.xls");
    }
    setFileInputCount(1);
    updateUploadLocationFilters();
}

function getFileInputElements() {
    return [
        document.getElementById("fileInput1"),
        document.getElementById("fileInput2"),
        document.getElementById("fileInput3")
    ].filter(Boolean);
}

function getExpectedFileCount(typeName) {
    const count = uploadTypeFileCounts[typeName];
    if (!count) {
        return 1;
    }
    const parsed = parseInt(count, 10);
    if (Number.isNaN(parsed)) {
        return 1;
    }
    return Math.max(1, Math.min(3, parsed));
}

function setFileInputAccepts(acceptValue) {
    const inputs = getFileInputElements();
    inputs.forEach((input) => {
        input.setAttribute("accept", acceptValue);
    });
}

function setFileInputCount(count) {
    const inputs = getFileInputElements();
    inputs.forEach((input, index) => {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (index < count) {
            input.classList.remove("d-none");
            input.disabled = false;
            input.required = true;
            if (label) {
                label.classList.remove("d-none");
            }
        } else {
            input.classList.add("d-none");
            input.disabled = true;
            input.required = false;
            input.value = "";
            if (label) {
                label.classList.add("d-none");
            }
        }
    });
}

function updateFileInputsForType() {
    const typeSelect = document.getElementById("dataType");
    if (!typeSelect) return;
    const normalizedCategory = (uploadTypeToCategory[typeSelect.value] || "").toLowerCase();
    if (normalizedCategory === "photos") {
        setFileInputAccepts("image/*");
    } else if (normalizedCategory === "hazard") {
        setFileInputAccepts(".jpg,.jpeg,.png,.tif,.tiff");
    } else {
        setFileInputAccepts(".csv,.xlsx,.xls");
    }
    const count = getExpectedFileCount(typeSelect.value);
    setFileInputCount(count);
}

function updateUploadLocationFilters() {
    const container = document.getElementById("uploadLocationFilters");
    if (!container) return;
    const typeValue = document.getElementById("dataType")?.value || "";
    const level = normalizeSelectionLevel(uploadTypeSelectionLevels[typeValue]);
    const shouldShow = level === "village" || level === "district";
    container.classList.toggle("d-none", !shouldShow);

    if (shouldShow) {
        const districtWrap = document.getElementById("upload_district")?.closest(".col-md-6");
        const circleWrap = document.getElementById("upload_circle")?.closest(".col-md-6");
        const gpWrap = document.getElementById("upload_gram_panchayat")?.closest(".col-md-6");
        const villageWrap = document.getElementById("upload_village")?.closest(".col-md-6");

        if (districtWrap) districtWrap.classList.toggle("d-none", level !== "district" && level !== "village");
        if (circleWrap) circleWrap.classList.toggle("d-none", level !== "village");
        if (gpWrap) gpWrap.classList.toggle("d-none", level !== "village");
        if (villageWrap) villageWrap.classList.toggle("d-none", level !== "village");

        if (!uploadLocationSelectorsReady) {
            setupLocationSelectors('upload_district', 'upload_circle', 'upload_gram_panchayat', 'upload_village');
            uploadLocationSelectorsReady = true;
        }
    }
}

function syncCategoryForType() {
    if (!uploadCatalog || isSyncingCategory) return;
    const typeSelect = document.getElementById("dataType");
    const categorySelect = document.getElementById("uploadCategory");
    if (!typeSelect || !categorySelect) return;

    const selectedType = typeSelect.value;
    const mappedCategory = uploadTypeToCategory[selectedType];
    if (!mappedCategory) return;

    if (categorySelect.value !== mappedCategory) {
        isSyncingCategory = true;
        categorySelect.value = mappedCategory;
        updateUploadTypesForCategory();
        typeSelect.value = selectedType;
        updateFileInputsForType();
        updateUploadLocationFilters();
        isSyncingCategory = false;
    }
}

async function loadUploadCatalog() {
    const categorySelect = document.getElementById("uploadCategory");
    if (!categorySelect) return;
    const catalogUrl = categorySelect.dataset.catalogUrl || "/api/get_upload_data_catalog";

    try {
        const response = await fetch(catalogUrl);
        if (!response.ok) {
            throw new Error("Failed to load upload catalog");
        }
        uploadCatalog = await response.json();
        uploadTypeToCategory = {};
        Object.entries(uploadCatalog.mapping || {}).forEach(([category, types]) => {
            (types || []).forEach((typeName) => {
                if (!uploadTypeToCategory[typeName]) {
                    uploadTypeToCategory[typeName] = category;
                }
            });
        });
        uploadTypeFileCounts = uploadCatalog.type_files || {};
        uploadTypeSelectionLevels = uploadCatalog.type_levels || {};
        populateCategorySelect(uploadCatalog.categories);
        populateTypeSelect(uploadCatalog.types);
        categorySelect.addEventListener("change", updateUploadTypesForCategory);
        const typeSelect = document.getElementById("dataType");
        if (typeSelect) {
            typeSelect.addEventListener("change", syncCategoryForType);
            typeSelect.addEventListener("change", updateFileInputsForType);
            typeSelect.addEventListener("change", updateUploadLocationFilters);
        }
        setFileInputCount(1);
        updateUploadLocationFilters();
    } catch (error) {
        console.error("Error loading upload catalog:", error);
    }
}

document.addEventListener('DOMContentLoaded', function () {

    colorChange("vdmp_dashboard", 'vdmp_dashboard_admin');

    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');

    loadUploadCatalog();

    document.getElementById("uploadnewdata").addEventListener("click", async function (e) {
        e.preventDefault();

        const fileInputs = getFileInputElements();
        const rawType = document.getElementById("dataType").value;
        const dataType = resolveUploadDataType(rawType);
        const button = this;
        const originalText = button.innerHTML;
        const expectedCount = getExpectedFileCount(rawType);
        const selectedFiles = fileInputs.map((input) => input.files[0]).filter(Boolean);

        if (!rawType) {
            Swal.fire("Error", "Please select a file and data type.", "error");
            return;
        }
        if (selectedFiles.length < 1) {
            Swal.fire("Error", "Please select at least 1 file.", "error");
            return;
        }
        if (!dataType) {
            Swal.fire("Error", "Selected data type is not supported for upload.", "error");
            return;
        }

        const result = await Swal.fire({
            title: "Are you sure?",
            text: "Do you want to upload this file?",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Yes, upload it!",
            cancelButtonText: "Cancel"
        });
        if (!result.isConfirmed) {
            return;
        }

        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
        button.disabled = true;

        const apiEndpoint = dataType == "line_department"
            ? "/en/api/upload_line_department_data/"
            : "/en/api/upload_data_vdmp";

        try {
            let totalCreated = 0;
            let totalUpdated = 0;
            let totalRejected = 0;

            for (let index = 0; index < selectedFiles.length; index++) {
                const file = selectedFiles[index];
                const fileIndex = index + 1;
                const formData = new FormData();
                formData.append("file", file);
                formData.append("data_type", dataType);
                formData.append("type_name", rawType);
                formData.append("total_files", selectedFiles.length);
                formData.append("file_index", fileIndex);
                const uploadCategory = document.getElementById("uploadCategory")?.value || "";
                formData.append("upload_category", uploadCategory);
                const districtId = document.getElementById("upload_district")?.value || "";
                if (districtId) {
                    formData.append("district_id", districtId);
                }
                const villageId = document.getElementById("upload_village")?.value || "";
                if (villageId) {
                    formData.append("village_id", villageId);
                }

                const response = await fetch(apiEndpoint, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                    },
                    body: formData
                });
                const data = await response.json();

                if (data.status === "success") {
                    totalCreated += data.records_created || 0;
                    totalUpdated += data.records_updated || 0;
                    totalRejected += data.errors ? data.errors.length : 0;
                    continue;
                }

                if (data.existing_villages) {
                    const existingCount = data.total_existing || data.existing_villages.length;
                    const duplicateResult = await Swal.fire({
                        title: "Data Already Exists",
                        html: `<div style="text-align: left;">
                                <p><strong>Warning:</strong> Data already exists for <strong>${existingCount}</strong> villages</p>
                                <p>Villages: ${data.existing_villages.slice(0, 5).join(', ')}${data.existing_villages.length > 5 ? '...' : ''}</p>
                                <p>Would you like to delete existing data and re-upload?</p>
                               </div>`,
                        icon: "warning",
                        showCancelButton: true,
                        confirmButtonText: "Delete & Re-upload",
                        cancelButtonText: "Cancel"
                    });
                    if (duplicateResult.isConfirmed) {
                        await deleteAndReupload(dataType, data.existing_villages, selectedFiles, apiEndpoint, rawType, expectedCount, button, originalText);
                        return;
                    } else {
                        button.innerHTML = originalText;
                        button.disabled = false;
                        return;
                    }
                }

                const errorCount = data.errors ? data.errors.length : 0;
                Swal.fire({
                    title: "Upload Failed",
                    html: `<div style="text-align: left;">
                            <p><strong>Error:</strong> ${data.error || "Upload failed"}</p>
                            ${errorCount > 0 ? `<p><strong>Total Errors:</strong> ${errorCount}</p>` : ''}
                           </div>`,
                    icon: "error"
                });
                return;
            }

            // Show success message after all files processed
            Swal.fire({
                title: "Upload Successful",
                html: `<div style="text-align: left;">
                        <p><strong>Records Created:</strong> ${totalCreated}</p>
                        <p><strong>Records Updated:</strong> ${totalUpdated}</p>
                        <p><strong>Records Rejected:</strong> ${totalRejected}</p>
                       </div>`,
                icon: totalRejected > 0 ? "warning" : "success"
            });
            
            // Clear form inputs
            getFileInputElements().forEach((input) => {
                input.value = '';
            });
            document.getElementById("dataType").value = '';
            if (document.getElementById("uploadCategory")) {
                document.getElementById("uploadCategory").value = '';
                updateUploadTypesForCategory();
            }
        } catch (error) {
            Swal.fire({
                title: "Upload Failed",
                html: `<div style="text-align: left;">
                        <p><strong>Error:</strong> Network or server error</p>
                        <p><small>Please check your connection and try again</small></p>
                       </div>`,
                icon: "error"
            });
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
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
                // button.innerHTML = originalText;
                // button.disabled = false;

                // button.innerHTML = 'Upload';
                //  button.disabled = false;
            });
        }
    });
});

// Function to delete existing data and re-upload
async function deleteAndReupload(
    dataType,
    villagesCodes,
    files,
    apiEndpoint,
    typeName,
    totalFiles,
    button,
    originalText
) {
    console.log("-------> ", button);

    button.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2"></span>Deleting & Re-uploading...';
    button.disabled = true;

    // ✅ FORCE DOM REPAINT
    await new Promise(resolve => setTimeout(resolve, 0));

    const handleError = (error) => {
        Swal.fire({
            title: "Operation Failed",
            text: error.message || "An error occurred during delete and re-upload",
            icon: "error"
        });
        button.innerHTML = originalText;
        button.disabled = false;
    };

    try {
        const deleteResponse = await fetch("/en/api/delete_village_data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({
                data_type: dataType,
                village_codes: villagesCodes
            })
        }).then(res => res.json());

        if (deleteResponse.status !== "success") {
            throw new Error(deleteResponse.error || "Delete failed");
        }

        let totalCreated = 0;
        let totalUpdated = 0;
        let totalRejected = 0;

        for (let index = 0; index < files.length; index++) {
            const file = files[index];
            const formData = new FormData();

            formData.append("file", file);
            formData.append("data_type", dataType);
            formData.append("type_name", typeName);
            formData.append("total_files", totalFiles);
            formData.append("file_index", index + 1);

            const uploadResponse = await fetch(apiEndpoint, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                },
                body: formData
            }).then(res => res.json());

            if (uploadResponse.status !== "success") {
                throw new Error(uploadResponse.error || "Re-upload failed");
            }

            totalCreated += uploadResponse.records_created || 0;
            totalUpdated += uploadResponse.records_updated || 0;
            totalRejected += uploadResponse.errors?.length || 0;
        }

        Swal.fire({
            title: "Re-upload Successful",
            html: `
                <div style="text-align:left">
                    <p><strong>Records Created:</strong> ${totalCreated}</p>
                    <p><strong>Records Updated:</strong> ${totalUpdated}</p>
                    <p><strong>Records Rejected:</strong> ${totalRejected}</p>
                </div>
            `,
            icon: totalRejected > 0 ? "warning" : "success"
        });

    } catch (error) {
        handleError(error);
        return;
    }

    button.innerHTML = originalText;
    button.disabled = false;
}

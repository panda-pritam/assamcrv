function showSummaryLoader() {
    const summaryLoader = document.getElementById('summary-loader');
    if (summaryLoader) summaryLoader.style.display = 'inline';
}

function hideSummaryLoader() {
    const summaryLoader = document.getElementById('summary-loader');
    if (summaryLoader) summaryLoader.style.display = 'none';
}



async function New_updateSummaryText() {
    console.log("New_updateSummaryText called");

    const districtId = $('#district').val();
    const circleId = $('#circle').val();
    const gramPanchayatId = $('#gram_panchayat').val();
    const villageId = $('#village').val();

    let summaryText = '';

    try {
        // Build API URL
        let url = '/api/count_of_villages_with_survey';
        const params = new URLSearchParams();

        if (villageId) {
            params.append('village_id', villageId);
        } else if (gramPanchayatId) {
            params.append('gram_panchayat_id', gramPanchayatId);
        } else if (circleId) {
            params.append('circle_id', circleId);
        } else if (districtId) {
            params.append('district_id', districtId);
        }

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        // Call API
        const response = await fetch(url);
        const data = await response.json();

        // Build summary text based on API response
        if (villageId) {
            if (data.has_data) {
                summaryText = `Summary: District: <strong>${data.district_val}</strong> Village: <strong>${data.village_val}</strong>`;
            } else {
                summaryText = `Summary: <strong>${data.district_val}</strong> : This village has no data`;
            }
        } else if (gramPanchayatId) {
            summaryText = `Summary: District: <strong>${data.district_val}</strong> | Villages : <strong>${data.village_val}</strong>`;
        } else if (circleId) {
            summaryText = `Summary: District: <strong>${data.district_val}</strong> | Villages : <strong>${data.village_val}</strong>`;
        } else if (districtId) {
            summaryText = `Summary: District: <strong>${data.district_val}</strong> | Villages : <strong>${data.village_val}</strong>`;
        } else {
            summaryText = `Summary: Districts : <strong>${data.district_val}</strong> | Villages : <strong>${data.village_val}</strong>`;
        }

    } catch (error) {
        console.error('Error fetching summary:', error);
        summaryText = '⚠️ Failed to load summary';
    }

    // Update UI
    const summaryElement = document.querySelector('.summary-line span');
    if (summaryElement) {
        summaryElement.innerHTML = summaryText;
    }
}





async function updateSummaryText(isVDMPProgress = false) {
    showSummaryLoader();
    const districtId = $('#district').val();
    const circleId = $('#circle').val();
    const gramPanchayatId = $('#gram_panchayat').val();
    const villageId = $('#village').val();

    const districtText = $('#district option:selected').text();
    const circleText = $('#circle option:selected').text();
    const gramPanchayatText = $('#gram_panchayat option:selected').text();
    const villageText = $('#village option:selected').text();

    let summaryText = '';
    let villageCount = 0;

    try {
        if (isVDMPProgress) {
            // Get village count for all cases
            let url = '/api/get_location_counts';
            const params = new URLSearchParams();

            if (villageId) {
                params.append('village_id', villageId);
            } else if (gramPanchayatId) {
                params.append('gram_panchayat_id', gramPanchayatId);
            } else if (circleId) {
                params.append('circle_id', circleId);
            } else if (districtId) {
                params.append('district_id', districtId);
            }

            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            // Build summary with location names and village count
            if (villageId && villageText !== 'Select Villages') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Village: <strong>${villageText}</strong> | Villages: <strong>${data.village_count}</strong>`;
            } else if (gramPanchayatId && gramPanchayatText !== 'Select Gram Panchayat') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Villages: <strong>${data.village_count}</strong>`;
            } else if (circleId && circleText !== 'Select Circle') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Villages: <strong>${data.village_count}</strong>`;
            } else if (districtId && districtText !== 'Select Districts') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Villages: <strong>${data.village_count}</strong>`;
            } else {
                summaryText = `Summary: Districts: <strong>${data.district_count}</strong>| Villages: <strong>${data.village_count}</strong>`;
            }
        } else {
            // Original logic for other pages
            let url = '/api/get_village_count';
            const params = new URLSearchParams();

            if (gramPanchayatId) {
                params.append('gram_panchayat_id', gramPanchayatId);
            } else if (circleId) {
                params.append('circle_id', circleId);
            } else if (districtId) {
                params.append('district_id', districtId);
            }

            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await fetch(url);
            const data = await response.json();
            villageCount = data.village_count || 0;

            if (data.district_count) {
                window.districtCount = data.district_count;
            }

            // Build summary text based on selection
            if (villageId && villageText !== 'Select Villages') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Village: <strong>${villageText}</strong>`;
            } else if (gramPanchayatId && gramPanchayatText !== 'Select Gram Panchayat') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Total Villages: <strong>${villageCount}</strong>`;
            } else if (circleId && circleText !== 'Select Circle') {
                summaryText = `Summary: District: <strong>${districtText}</strong> | Total Villages: <strong>${villageCount}</strong>`;
            } else if (districtId && districtText !== 'Select Districts') {
                summaryText = `District: <strong>${districtText}</strong> | Total Villages: <strong>${villageCount}</strong>`;
            } else {
                const districtCount = window.districtCount || 1;
                summaryText = `Summary: Districts: <strong>${districtCount}</strong> | Total Villages: <strong>${villageCount}</strong>`;
            }
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }

    // Update the summary line
    const summaryElement = document.getElementById('summary-text');
    if (summaryElement) {
        summaryElement.innerHTML = summaryText;
    }

    hideSummaryLoader();
}

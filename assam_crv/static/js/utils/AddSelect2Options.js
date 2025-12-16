function initializeSelect2(selectId, placeholder = gettext('Select Option')) {
    $(`#${selectId}`).select2({
        placeholder: placeholder,
        allowClear: true
    });
}

function loadDistrictsAndVillages(districtSelectId, villageSelectId) {
    // Load districts on page load
    fetch('/api/get_districts')
        .then(response => response.json())
        .then(data => {
            const districtSelect = document.getElementById(districtSelectId);
            data.forEach(district => {
                const option = document.createElement('option');
                option.value = district.id;
                option.textContent = district.name;
                option.setAttribute('data-lat', district.latitude || '');
                option.setAttribute('data-lng', district.longitude || '');
                option.setAttribute('code', district.code || '');
                districtSelect.appendChild(option);
            });
            $(`#${districtSelectId}`).trigger('change.select2');
        });

    // Load villages when district changes
    $(`#${districtSelectId}`).on('change', function () {
        const districtId = this.value;
        $(`#${villageSelectId}`).empty().append(`<option value="" selected disabled>${gettext('Select Villages')}</option>`);

        if (districtId) {
            fetch(`/api/villages_by_district?district_id=${districtId}`)
                .then(response => response.json())
                .then(data => {
                    const villageSelect = document.getElementById(villageSelectId);
                    data.forEach(village => {
                        const option = document.createElement('option');
                        option.value = village.id;
                        option.textContent = village.name;
                        option.setAttribute('data-lat', village.latitude || '');
                        option.setAttribute('data-lng', village.longitude || '');
                        option.setAttribute('code', village.code || '');
                        villageSelect.appendChild(option);
                    });
                    $(`#${villageSelectId}`).trigger('change.select2');
                });
        }
    });
}

async function setupLocationSelectors(districtId, circleId, gpId, villageId, userDistrictId, userCircleId, userGramPanchayatId, userVillageId) {
    const districtEl = document.getElementById(districtId);
    const circleEl = document.getElementById(circleId);
    const gpEl = document.getElementById(gpId);
    const villageEl = document.getElementById(villageId);

    // Load Districts on page load
    const districtRes = await fetch('/api/get_districts');
    const districtData = await districtRes.json();
    districtData.forEach(district => {
        const option = document.createElement('option');
        option.value = district.id;
        option.textContent = district.name;
        districtEl.appendChild(option);
    });
    
    // Sequential loading and value setting
    if (userDistrictId) {
        $(`#${districtId}`).val(userDistrictId);
        
        // Load circles for the district
        const circleRes = await fetch(`/api/get_circles?district_id=${userDistrictId}`);
        const circleData = await circleRes.json();
        $(`#${circleId}`).empty().append(`<option selected disabled>${gettext('Select Circle')}</option>`);
        circleData.forEach(circle => {
            $(`#${circleId}`).append(`<option value="${circle.id}">${circle.name}</option>`);
        });
        
        if (userCircleId) {
            $(`#${circleId}`).val(userCircleId);
            
            // Load gram panchayats for the circle
            const gpRes = await fetch(`/api/get_gram_panchayats?circle_id=${userCircleId}`);
            const gpData = await gpRes.json();
            $(`#${gpId}`).empty().append(`<option selected disabled>${gettext('Select Gram Panchayat')}</option>`);
            gpData.forEach(gp => {
                $(`#${gpId}`).append(`<option value="${gp.id}">${gp.name}</option>`);
            });
            
            if (userGramPanchayatId) {
                $(`#${gpId}`).val(userGramPanchayatId);
                
                // Load villages for the gram panchayat
                const villageRes = await fetch(`/api/get_villages?gram_panchayat_id=${userGramPanchayatId}`);
                const villageData = await villageRes.json();
                $(`#${villageId}`).empty().append(`<option selected disabled>${gettext('Select Village')}</option>`);
                villageData.forEach(village => {
                    $(`#${villageId}`).append(`<option value="${village.id}">${village.name}</option>`);
                });
                
                if (userVillageId) {
                    $(`#${villageId}`).val(userVillageId);
                }
            }
        }
    }

    // District → Circle
    $(`#${districtId}`).on('change', function () {
        const districtVal = $(this).val();
        $(`#${circleId}`).empty().append(`<option selected disabled>${gettext('Select Circle')}</option>`);
        $(`#${gpId}`).empty().append(`<option selected disabled>${gettext('Select Gram Panchayat')}</option>`);
        $(`#${villageId}`).empty().append(`<option selected disabled>${gettext('Select Village')}</option>`);

        if (districtVal) {
            $.get(`/api/get_circles?district_id=${districtVal}`, function (data) {
                data.forEach(circle => {
                    $(`#${circleId}`).append(`<option value="${circle.id}">${circle.name}</option>`);
                });
            });
        }
    });

    // Circle → Gram Panchayat
    $(`#${circleId}`).on('change', function () {
        const circleVal = $(this).val();
        $(`#${gpId}`).empty().append(`<option selected disabled>${gettext('Select Gram Panchayat')}</option>`);
        $(`#${villageId}`).empty().append(`<option selected disabled>${gettext('Select Village')}</option>`);

        if (circleVal) {
            $.get(`/api/get_gram_panchayats?circle_id=${circleVal}`, function (data) {
                data.forEach(gp => {
                    $(`#${gpId}`).append(`<option value="${gp.id}">${gp.name}</option>`);
                });
            });
        }
    });

    // Gram Panchayat → Village
    $(`#${gpId}`).on('change', function () {
        const gpVal = $(this).val();
        $(`#${villageId}`).empty().append(`<option selected disabled>${gettext('Select Village')}</option>`);

        if (gpVal) {
            $.get(`/api/get_villages?gram_panchayat_id=${gpVal}`, function (data) {
                data.forEach(village => {
                    $(`#${villageId}`).append(`<option value="${village.id}">${village.name}</option>`);
                });
            });
        }
    });
}

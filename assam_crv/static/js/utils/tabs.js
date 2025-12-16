function showTab(tab, buttonId, adjustDataTableCallback = null,master_btn_id=null) {
    if (adjustDataTableCallback) {
        adjustDataTableCallback();
    }
    // console.log("showTab", tab, buttonId, adjustDataTableCallback, master_btn_id)

    // adjustDataTableColumns('rescue_equipment_table_master')
    // adjustDataTableColumns('rescue_equipment_table')
    // adjustDataTableColumns('training_activities_table')
    // adjustDataTableColumns('training_activities_table_master')

    if (tab === 'master') {
        if (document.getElementById('activities-master')) {
            document.getElementById('activities-master').classList.remove('d-none');
            document.getElementById('activities-master').classList.add('d-block');
        }
        document.getElementById('activities-villages').classList.remove('d-block');
        document.getElementById('activities-villages').classList.add('d-none');
        if (document.getElementById('master-tab')) {
            document.getElementById('master-tab').classList.add('active');
        }
        document.getElementById('village-tab').classList.remove('active');
        if (buttonId && document.getElementById(buttonId)) {
            document.getElementById(buttonId).classList.remove('d-none');
            document.getElementById(buttonId).classList.add('d-flex');
        }
        if (master_btn_id && document.getElementById(master_btn_id)) {
            document.getElementById(master_btn_id).classList.remove('d-none');
            document.getElementById(master_btn_id).classList.add('d-flex');
        }
    } else {
        if (document.getElementById('activities-master')) {
            document.getElementById('activities-master').classList.remove('d-block');
            document.getElementById('activities-master').classList.add('d-none');
        }
        document.getElementById('activities-villages').classList.remove('d-none');
        document.getElementById('activities-villages').classList.add('d-block');
        document.getElementById('village-tab').classList.add('active');
        if (document.getElementById('master-tab')) {
            document.getElementById('master-tab').classList.remove('active');
        }
        if (buttonId && document.getElementById(buttonId)) {
            document.getElementById(buttonId).classList.remove('d-flex');
            document.getElementById(buttonId).classList.add('d-none');
        }
        if (master_btn_id && document.getElementById(master_btn_id)) {
            document.getElementById(master_btn_id).classList.remove('d-flex');
            document.getElementById(master_btn_id).classList.add('d-none');
        }
    }
}
let taskForceTable;
let taskForceData = [];
let taskForceChartInstance = null;

$(document).ready(async function() {
    colorChange('task_force','task_force')
    initializeTaskForceTable();
    initializeSelect2('district');
    initializeSelect2('circle');
    initializeSelect2('gram_panchayat');
    initializeSelect2('village');
    initializeSelect2('team_type');
    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');
    
    await loadTeamTypesDropdown();
    await loadTaskForceChartData();
    await loadTaskForceData();
    await updateSummaryText(true);
    
    setupEventListeners();
});

function initializeTaskForceTable() {
    const columns = [
        { title: gettext("Sr. No"), width: "5%" },
        { title: gettext("Name") },
        { title: gettext("Father's Name") },
        { title: gettext("Gender"), width: "8%" },
        { title: gettext("Phone Number") },
        { title: gettext("Position/Responsibility") },
        { title: gettext("District Name") },
        { title: gettext("Village Name") },
        { title: gettext("Team Type") },
        { title: gettext("Occupation") }
    ];
    
    taskForceTable = initializeDataTable('taskforce_table', columns, {}, false);
}

function setupEventListeners() {
    $('#district, #circle, #gram_panchayat, #village, #team_type').change(async () => {
        await loadTaskForceChartData();
        await loadTaskForceData();
        await updateSummaryText(true);
    });
}

async function loadTaskForceData() {
    try {
        // Show table loader
        showTaskForceTableLoader();
        
        const params = new URLSearchParams();
        
        const districtId = $('#district').val();
        const circleId = $('#circle').val();
        const gpId = $('#gram_panchayat').val();
        const villageId = $('#village').val();
        const teamType = $('#team_type').val();
        
        if (districtId) params.append('district_id', districtId);
        if (circleId) params.append('circle_id', circleId);
        if (gpId) params.append('gram_panchayat_id', gpId);
        if (villageId) params.append('village_id', villageId);
        if (teamType) params.append('team_type', teamType);
        
        const response = await fetch(`/en/api/taskforce/?${params.toString()}`);
        const data = await response.json();
        
        taskForceData = data;
        populateTaskForceTable(data);
    } catch (error) {
        console.error('Error loading task force data:', error);
        hideTaskForceTableLoader();
    }
}

function populateTaskForceTable(data) {
    // Clear loader first
    if (taskForceTable) {
        taskForceTable.clear();
    }
    
    const rowMapper = (item, index) => [
        index + 1,
        item.fullname || '',
        item.father_name || '',
        item.gender || '',
        item.mobile_number || '',
        item.position_responsibility || '',
        item.district_name || 'N/A',
        item.village_name || 'N/A',
        item.team_type || '',
        item.occupation || 'N/A'
    ];
    
    populateDataTable(taskForceTable, data, rowMapper, false);
}

async function loadTeamTypesDropdown() {
    try {
        const response = await fetch('/api/team_types_dropdown/');
        const teamTypes = await response.json();
        
        const container = $('#team-type-checkboxes');
        container.empty();
        
        teamTypes.forEach(teamType => {
            const checkboxHtml = `
                <div class="form-check mb-1">
                    <input class="form-check-input team-type-checkbox" type="checkbox" value="${teamType.value}" id="team-type-${teamType.value}" checked>
                    <label class="form-check-label" for="team-type-${teamType.value}">
                        ${teamType.name}
                    </label>
                </div>
            `;
            container.append(checkboxHtml);
        });

        $('.team-type-checkbox').on('change', handleTeamTypeChange);
        $('#select-all-team-types').on('change', handleSelectAllTeamTypes);
        updateTeamTypeDisplay();
    } catch (error) {
        console.error('Error loading team types:', error);
    }
}

function handleSelectAllTeamTypes() {
    const isChecked = $('#select-all-team-types').is(':checked');
    $('.team-type-checkbox').prop('checked', isChecked);
    updateTeamTypeDisplay();
    reloadTaskForceChartAndSummary();
}

function handleTeamTypeChange() {
    const totalTeamTypes = $('.team-type-checkbox').length;
    const checkedTeamTypes = $('.team-type-checkbox:checked').length;
    $('#select-all-team-types').prop('checked', checkedTeamTypes === totalTeamTypes);
    updateTeamTypeDisplay();
    reloadTaskForceChartAndSummary();
}
async function reloadTaskForceChartAndSummary() {
    const teamTypes = getSelectedTeamTypes();

    // If no team types selected, show "No data" and return
    if (!teamTypes || teamTypes.length === 0) {
        renderNoDataTaskForceChartAndSummary();
        return;
    }

    // Show loader if needed
    showTaskForceChartLoader();
    showTaskForceSummaryTableLoader();

    try {
        const params = new URLSearchParams();
        const districtId = $('#district').val();
        const circleId = $('#circle').val();
        const gpId = $('#gram_panchayat').val();
        const villageId = $('#village').val();

        if (districtId) params.append('district_id', districtId);
        if (circleId) params.append('circle_id', circleId);
        if (gpId) params.append('gram_panchayat_id', gpId);
        if (villageId) params.append('village_id', villageId);
        params.append('team_types', teamTypes.join(','));

        const response = await fetch(`/api/taskforce_chart_data?${params.toString()}`);
        const data = await response.json();

        renderTaskForceChart(data);
        renderTaskForceSummaryTable(data);

    } catch (error) {
        console.error('Error updating chart & summary table:', error);
        renderNoDataTaskForceChartAndSummary();
    } finally {
        hideTaskForceChartLoader();
        hideTaskForceSummaryTableLoader();
    }
}


function updateTeamTypeDisplay() {
    const totalTeamTypes = $('.team-type-checkbox').length;
    const checkedTeamTypes = $('.team-type-checkbox:checked').length;
    const displayElement = $('#team-type-display');

    if (checkedTeamTypes === 0) {
        displayElement.text('No Team Types Selected');
    } else if (checkedTeamTypes === totalTeamTypes) {
        displayElement.text('All Team Types');
    } else {
        displayElement.text(`${checkedTeamTypes} Team Types Selected`);
    }
}



function getSelectedTeamTypes() {
    const total = $('.team-type-checkbox').length;
    if (total === 0) return null;
    return $('.team-type-checkbox:checked').map(function () {
        return $(this).val();  // keep as string, do NOT use parseInt
    }).get();
}

async function loadTaskForceChartData() {
    const teamTypes = getSelectedTeamTypes();

    // If no team types selected, show "No data" and return
    if (!teamTypes || teamTypes.length === 0) {
        renderNoDataTaskForceChartAndSummary();
        return;
    }

    try {
        showTaskForceChartLoader();
        showTaskForceSummaryTableLoader();

        const params = new URLSearchParams();
        const districtId = $('#district').val();
        const circleId = $('#circle').val();
        const gpId = $('#gram_panchayat').val();
        const villageId = $('#village').val();

        if (districtId) params.append('district_id', districtId);
        if (circleId) params.append('circle_id', circleId);
        if (gpId) params.append('gram_panchayat_id', gpId);
        if (villageId) params.append('village_id', villageId);
        params.append('team_types', teamTypes.join(','));

        const response = await fetch(`/api/taskforce_chart_data?${params.toString()}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        renderTaskForceChart(data);
        renderTaskForceSummaryTable(data);

    } catch (error) {
        console.error('Error loading chart data:', error);
        renderNoDataTaskForceChartAndSummary();
    } finally {
        hideTaskForceChartLoader();
        hideTaskForceSummaryTableLoader();
    }
}

// Helper to render "No data" in chart and summary table
function renderNoDataTaskForceChartAndSummary() {
    const chart = document.getElementById('taskforce_chart');
    if (chart) chart.innerHTML = '<div class="text-center p-5 text-muted">No data available</div>';

    const tbody = document.querySelector('#taskforce_summary_table tbody');
    if (tbody) {
        tbody.innerHTML = `<tr>
            <td colspan="6" class="text-center text-muted p-4">
                <i class="fas fa-info-circle me-2"></i>No data available
            </td>
        </tr>`;
    }
}


function renderTaskForceSummaryTable(data) {
    const table = document.getElementById('taskforce_summary_table');
    if (!table) {
        console.error('taskforce_summary_table not found');
        return;
    }

    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error('tbody not found in taskforce_summary_table');
        return;
    }
    
    tbody.innerHTML = ''; // This clears the loader

    if (!data || data.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="5" class="text-center text-muted p-4">
                <i class="fas fa-info-circle me-2"></i>No data available
            </td>
        `;
        tbody.appendChild(row);
        return;
    }

    data.forEach((item, index) => {
        const total = parseInt(item.created || 0) + parseInt(item.not_created || 0);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class='text-center'>${index + 1}</td>
            <td class='text-start'>${item.team_type || 'N/A'}</td>
            <td class='text-center bg-blue'>${item.not_created || 0}</td>
            <td class='text-center bg-green'>${item.created || 0}</td>
            <td class='text-center font-weight-bold'>${total}</td>
        `;
        tbody.appendChild(row);
    });
}

async function printTaskForcePage() {
    try {
        showPrintLoading();
        const chartImage = await captureTaskForceChartAsImage();
        const filters = getTaskForceFilters();
        const printContent = generateTaskForcePrintContent(chartImage, filters);
        createPrintWindow(printContent);
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('Error generating PDF. Please try again.');
    } finally {
        hidePrintLoading();
    }
}

function showPrintLoading() {
    const loadingHtml = `
        <div id="print-loading" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
             background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
                <div style="font-size: 16px; margin-bottom: 10px;">Preparing PDF...</div>
                <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; 
                     border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto;"></div>
            </div>
        </div>
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

function hidePrintLoading() {
    const loading = document.getElementById('print-loading');
    if (loading) loading.remove();
}

async function captureTaskForceChartAsImage() {
    try {
        if (taskForceChartInstance) {
            const chartImage = await taskForceChartInstance.dataURI({
                format: 'png',
                width: 1400,
                height: 400,
                pixelRatio: 2
            });
            return chartImage.imgURI;
        }
        return null;
    } catch (error) {
        console.error('Error capturing chart:', error);
        return null;
    }
}

function getTaskForceFilters() {
    const district = $('#district option:selected').text();
    const circle = $('#circle option:selected').text();
    const gramPanchayat = $('#gram_panchayat option:selected').text();
    const village = $('#village option:selected').text();
    const teamTypeDisplay = $('#team-type-display').text();
    
    return {
        district: district !== 'Select Districts' ? district : 'All Districts',
        circle: circle !== 'Select Circle' ? circle : 'All Circles',
        gramPanchayat: gramPanchayat !== 'Select Gram Panchayat' ? gramPanchayat : 'All Gram Panchayats',
        village: village !== 'Select Villages' ? village : 'All Villages',
        teamTypes: teamTypeDisplay || 'All Team Types'
    };
}
function getTaskForceSummaryTableHTML() {
    const table = document.getElementById('taskforce_summary_table');
    if (!table) return '<p>Table not available</p>';
    
    const clonedTable = table.cloneNode(true);
    const rows = clonedTable.querySelectorAll('tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td, th');
        cells.forEach(cell => {
            const classList = Array.from(cell.classList);
            cell.className = '';
            if (classList.includes('text-center')) cell.classList.add('text-center');
            if (classList.includes('text-left') || classList.includes('text-start')) cell.classList.add('text-left');
            if (classList.includes('font-weight-bold')) cell.classList.add('font-weight-bold');
            if (classList.includes('bg-green')) cell.classList.add('bg-green');
            if (classList.includes('bg-blue')) cell.classList.add('bg-blue');
        });
    });
    return clonedTable.outerHTML;
}

function renderTaskForceChart(data) {
    const chartDiv = document.getElementById('taskforce_chart');
    if (!chartDiv) return;

    if (taskForceChartInstance) {
        taskForceChartInstance.destroy();
        taskForceChartInstance = null;
    }

    if (!Array.isArray(data) || data.length === 0) {
        chartDiv.innerHTML = '<div class="text-center p-5">No data available</div>';
        return;
    }

    // Clear loader
    chartDiv.innerHTML = '';

    const categories = data.map(item => item.team_type);
    const categories_label = data.map(item => {
        const maxLength = 10;
        return item.team_type.length > maxLength
            ? item.team_type.slice(0, maxLength) + '…'
            : item.team_type;
    });
    const createdData = data.map(item => item.created);
    const notCreatedData = data.map(item => item.not_created);

    const options = {
        series: [
            {
                name: 'Created',
                data: createdData
            },
            {
                name: 'Not Created',
                data: notCreatedData
            }
        ],
        chart: {
            type: 'bar',
            height: 400,
            stacked: true,
            toolbar: { 
                show: true,
                tools: {
                    download: true,
                    selection: false,
                    zoom: false,
                    zoomin: false,
                    zoomout: false,
                    pan: false,
                    reset: false
                }
            }
        },
        colors: ['#679436', '#357AF6'],
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '60%',
                endingShape: 'rounded'
            }
        },
        dataLabels: {
            enabled: true,
            style: {
                fontSize: '10px',
                colors: ['#fff'],
                fontWeight: 'bold'
            },
            formatter: function (val) {
                return val > 0 ? val : '';
            }
        },
        xaxis: {
            categories: categories_label,
            labels: {
                style: {
                    fontSize: '12px',
                    fontWeight: 'bold'
                },
                rotate: -45,
                rotateAlways: true
            },
            title: {
                text: gettext('Task force'),
                // offsetY: -10,
                style: {
                    fontSize: '14px',
                    fontWeight: 'bold',
                    color: '#333',
                }
            }
        },
        yaxis: {
            title: {
                text: 'Count of Villages',
                style: {
                    fontSize: '14px',
                    fontWeight: 'bold'
                }
            }
        },
        legend: {
            position: 'top',
            horizontalAlign: 'center'
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return val + ' villages';
                }
            },
            x: {
                formatter: function (val, opts) {
                    return categories[opts.dataPointIndex];
                }
            }
        }
    };

    taskForceChartInstance = new ApexCharts(chartDiv, options);
    taskForceChartInstance.render().then(() => {
        // Wait for the chart to be fully rendered
        setTimeout(() => {
            // Get all x-axis label elements
            const labels = document.querySelectorAll('.apexcharts-xaxis-label');

            // Loop through each label
            labels.forEach((label, index) => {
                // Get the corresponding full text from your original data
                const fullText = categories[index];

                // Find the <title> element inside the label
                const titleElement = label.querySelector('title');

                // Update the title element with the full text
                if (titleElement && fullText) {
                    titleElement.textContent = fullText;
                }
            });
        }, 500); // Small delay to ensure chart is fully rendered
    }).catch(error => {
        console.error('Error rendering chart:', error);
        chartDiv.innerHTML = '<div class="text-center p-5 text-danger">Error rendering chart</div>';
    });
}

function generateTaskForcePrintContent(chartImage, filters) {
    const currentDate = new Date().toLocaleDateString('en-IN', {
        year: 'numeric', month: 'long', day: 'numeric'
    });
    const currentTime = new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit'
    });
    const summaryElement = document.querySelector('.summary-line span');
    const summaryText = summaryElement ? summaryElement.textContent : '';
    const progressTable = getTaskForceSummaryTableHTML();
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Task Force Teams Report</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', sans-serif; font-size: 12px; color: #333; background: white; }
                .print-container { max-width: 210mm; margin: 0 auto; padding: 10mm; }
                .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #245FAE; padding-bottom: 15px; }
                .header h1 { color: #245FAE; font-size: 24px; margin-bottom: 8px; }
                .report-info { display: flex; justify-content: space-between; margin: 15px 0; font-size: 11px; color: #666; }
                .filters-section { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #dee2e6; }
                .filters-title { font-weight: bold; margin-bottom: 10px; color: #245FAE; font-size: 14px; }
                .filters-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 11px; }
                .filter-item { display: flex; }
                .filter-label { font-weight: 600; min-width: 100px; color: #495057; }
                .filter-value { color: #212529; }
                .summary-section { background: #e7f3ff; padding: 12px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #245FAE; }
                .summary-section p { margin: 0; color: #245FAE; font-weight: 500; }
                .chart-section { margin-bottom: 25px; text-align: center; }
                .chart-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #245FAE; }
                .chart-container { border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; background: white; display: inline-block; }
                .chart-image { max-width: 100%; height: auto; width: 100%; }
                .no-chart { padding: 40px; text-align: center; color: #6c757d; font-style: italic; border: 2px dashed #dee2e6; }
                .section-title { font-size: 16px; font-weight: bold; margin: 25px 0 15px 0; color: #245FAE; border-bottom: 2px solid #245FAE; padding-bottom: 5px; }
                .table-container { margin-bottom: 25px; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden; }
                .table-header { background: #245FAE !important; color: white !important; padding: 10px; font-weight: bold; display: flex; justify-content: space-between; -webkit-print-color-adjust: exact !important; }
                .legend { display: flex; gap: 15px; font-size: 10px; align-items: center; }
                .legend-item { display: flex; align-items: center; gap: 5px; }
                .legend-color { width: 12px; height: 12px; border-radius: 2px; }
                .notcreated { background-color: #357AF6 !important; -webkit-print-color-adjust: exact !important; }
                .created { background-color: #679436 !important; -webkit-print-color-adjust: exact !important; }
                table { width: 100%; border-collapse: collapse; font-size: 11px; }
                th, td { border: 1px solid #dee2e6; padding: 8px; text-align: center; }
                th { background-color: #f8f9fa; font-weight: bold; color: #495057; }
                .text-left { text-align: left !important; }
                .text-center { text-align: center !important; }
                .font-weight-bold { font-weight: bold; }
                .bg-green { background-color: rgba(103, 148, 54, 0.1) !important; -webkit-print-color-adjust: exact !important; }
                .bg-blue { background-color: rgba(53, 122, 246, 0.1) !important; -webkit-print-color-adjust: exact !important; }
                @media print {
                    body { margin: 0; }
                    .print-container { margin: 0; padding: 6mm; }
                    .chart-section, .table-container { page-break-inside: avoid; }
                    .table-header { background: #245FAE !important; color: white !important; -webkit-print-color-adjust: exact !important; }
                }
                @page { size: A4; margin: 8mm; }
            </style>
        </head>
        <body>
            <div class="print-container">
                <div class="header">
                    <h1>Task Force Teams Report</h1>
                    <div class="report-info">
                        <span><strong>Generated on:</strong> ${currentDate} at ${currentTime}</span>
                        <span><strong>Report Type:</strong> Task Force Analysis</span>
                    </div>
                </div>
                
                <div class="filters-section">
                    <div class="filters-title">Applied Filters:</div>
                    <div class="filters-grid">
                        <div class="filter-item"><span class="filter-label">District:</span><span class="filter-value">${filters.district}</span></div>
                        <div class="filter-item"><span class="filter-label">Circle:</span><span class="filter-value">${filters.circle}</span></div>
                        <div class="filter-item"><span class="filter-label">Gram Panchayat:</span><span class="filter-value">${filters.gramPanchayat}</span></div>
                        <div class="filter-item"><span class="filter-label">Village:</span><span class="filter-value">${filters.village}</span></div>
                        <div class="filter-item" style="grid-column: 1 / -1;"><span class="filter-label">Team Types:</span><span class="filter-value">${filters.teamTypes}</span></div>
                    </div>
                </div>
                
                ${summaryText ? `
                <div class="summary-section">
                    <p><i class="fas fa-info-circle"></i> ${summaryText}</p>
                </div>
                ` : ''}
                
                <div class="chart-section">
                    <div class="chart-title">Task Force Teams Progress Status</div>
                    <div class="chart-container">
                        ${chartImage ? `<img src="${chartImage}" alt="Task Force Chart" class="chart-image" />` : `<div class="no-chart">Chart not available for printing</div>`}
                    </div>
                </div>
                
                <div class="section-title" style="page-break-before: always;">Task Force Teams Status Summary</div>
                <div class="table-container">
                    <div class="table-header">
                        <span>Teams Status Overview</span>
                        <div class="legend">
                            <div class="legend-item"><div class="legend-color created"></div><span>Created</span></div>
                            <div class="legend-item"><div class="legend-color notcreated"></div><span>Not Created</span></div>
                        </div>
                    </div>
                    ${progressTable}
                </div>
            </div>
        </body>
        </html>
    `;
}



function createPrintWindow(htmlContent) {
    const printWindow = window.open('', '_blank', 'scrollbars=yes,resizable=yes');
    if (!printWindow) {
        alert('Please allow popups for this website to enable printing.');
        return;
    }
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.onload = function() {
        setTimeout(() => {
            printWindow.focus();
            printWindow.print();
            setTimeout(() => printWindow.close(), 1000);
        }, 500);
    };
}

function showTaskForceChartLoader() {
    document.getElementById('taskforce_chart').innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 400px;">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2">Loading chart data...</div>
            </div>
        </div>
    `;
}

function hideTaskForceChartLoader() {
    // Loader is hidden when chart renders
}

function showTaskForceSummaryTableLoader() {
    const tbody = document.querySelector('#taskforce_summary_table tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center p-4">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Loading summary data...
                </td>
            </tr>
        `;
    }
}

function hideTaskForceSummaryTableLoader() {
    // Loader is hidden when table renders
}

function showTaskForceTableLoader() {
    if (taskForceTable) {
        taskForceTable.clear();
        taskForceTable.row.add([
            '<div class="text-center" colspan="10"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Loading task force data...</div>',
            '', '', '', '', '', '', '', '', ''
        ]).draw();
    }
}

function hideTaskForceTableLoader() {
    // Loader is hidden when table populates
}

// Sidebar toggle adjustment
document.getElementById('sideBarToggler')?.addEventListener('click', () => {
    adjustDataTableColumns('taskforce_table');
});
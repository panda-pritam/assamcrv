let trainingChartInstance = null;

function renderTrainingChart(data) {
    const chartDiv = document.getElementById('training_chart');
    if (!chartDiv) return;

    if (trainingChartInstance) {
        trainingChartInstance.destroy();
        trainingChartInstance = null;
    }

    if (!Array.isArray(data) || data.length === 0) {
        chartDiv.innerHTML = '<div class="text-center p-5">No data available</div>';
        return;
    }

    // Clear loader
    chartDiv.innerHTML = '';

    const categories = data.map(item => item.activity);
    const categories_label = data.map(item => {
        const maxLength = 12;
        return item.activity.length > maxLength
            ? item.activity.slice(0, maxLength) + '…'
            : item.activity;
    });
    const completedData = data.map(item => item.completed);
    const remainingData = data.map(item => item.remaining);

    const options = {
        series: [
            {
                name: 'Completed',
                data: completedData
            },
            {
                name: 'Remaining',
                data: remainingData
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
        colors: [ '#679436','#357AF6',],
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
                text: gettext('Training Activities'),
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

    trainingChartInstance = new ApexCharts(chartDiv, options);
    trainingChartInstance.render().then(() => {
        setTimeout(() => {
            const labels = document.querySelectorAll('.apexcharts-xaxis-label');
            labels.forEach((label, index) => {
                const fullText = categories[index];
                const titleElement = label.querySelector('title');
                if (titleElement && fullText) {
                    titleElement.textContent = fullText;
                }
            });
        }, 500);
    });
}

function renderTrainingTable(data) {
    const table = document.getElementById('training_table');
    if (!table) return;

    const tbody = table.querySelector('tbody') || table.createTBody();
    tbody.innerHTML = ''; // This clears the loader

    data.forEach((item, index) => {
        const total = parseInt(item.completed) + parseInt(item.remaining);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class='text-center'>${index + 1}</td>
            <td class='text-start'>${item.activity}</td>
            <td class='text-center bg-blue'>${item.remaining}</td>
            <td class='text-center   bg-green'>${item.completed}</td>
            <td class='text-center font-weight-bold'>${total}</td>
        `;
        tbody.appendChild(row);
    });
}


function showNoActivitySelectedUI() {
    // destroy existing chart instance if any
    if (trainingChartInstance) {
        try { trainingChartInstance.destroy(); } catch (e) {}
        trainingChartInstance = null;
    }

    // Chart placeholder
    const chartDiv = document.getElementById('training_chart');
    if (chartDiv) {
        chartDiv.innerHTML = '<div class="text-center p-5">No activity selected</div>';
    }

    // Summary table (training_table)
    const trainingTable = document.getElementById('training_table');
    if (trainingTable) {
        const tbody = trainingTable.querySelector('tbody') || trainingTable.createTBody();
        tbody.innerHTML = `<tr><td colspan="5" class="text-center p-3">No activity selected</td></tr>`;
    }

    // Detailed activities table (training_activities_table)
    const activitiesBody = document.getElementById('training_activities_body');
    if (activitiesBody) {
        activitiesBody.innerHTML = `<tr><td colspan="7" class="text-center p-3">No activity selected</td></tr>`;
    }
}

async function loadTrainingChartData() {
    try {
        // Show loaders
        showTrainingChartLoader();
        showTrainingSummaryTableLoader();

        const district_id = $('#district').val();
        const circle_id = $('#circle').val();
        const gram_panchayat_id = $('#gram_panchayat').val();
        const village_id = $('#village').val();

        const totalActivities = $('.activity-checkbox').length;
        const activityIds = getSelectedActivityIds(); // null => not loaded yet

        // If checkboxes are present and none are checked => user intentionally unselected all
        if (totalActivities > 0 && (!Array.isArray(activityIds) || activityIds.length === 0)) {
            showNoActivitySelectedUI();
            return; // do not call API
        }

        // Build filter object
        const filters = {};
        if (district_id) filters.district_id = district_id;
        if (circle_id) filters.circle_id = circle_id;
        if (gram_panchayat_id) filters.gram_panchayat_id = gram_panchayat_id;
        if (village_id) filters.village_id = village_id;
        if (Array.isArray(activityIds) && activityIds.length > 0) filters.activity_ids = activityIds.join(',');

        // Compose URL (if filters empty, backend should return "all")
        const url = `/api/training_chart_data${Object.keys(filters).length ? '?' + new URLSearchParams(filters).toString() : ''}`;

        const response = await fetch(url);
        if (!response.ok) {
            // get response text for debug message
            const txt = await response.text();
            throw new Error(`Server returned ${response.status}: ${txt}`);
        }
        const data = await response.json();

        console.log('Chart data received:', data);
        renderTrainingChart(data);
        renderTrainingTable(data);

        // Load detailed activities table (send same filters object)
        await loadTrainingActivityData(filters);
    } catch (error) {
        console.error('Error loading chart data:', error);
        const chartDiv = document.getElementById('training_chart');
        if (chartDiv) chartDiv.innerHTML = '<div class="text-center p-5 text-danger">Error loading chart</div>';

        const trainingTable = document.getElementById('training_table');
        if (trainingTable) {
            const tbody = trainingTable.querySelector('tbody') || trainingTable.createTBody();
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger p-3">Failed to load data.</td></tr>`;
        }

        const activitiesBody = document.getElementById('training_activities_body');
        if (activitiesBody) {
            activitiesBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger p-3">Failed to load data.</td></tr>`;
        }
    } finally {
        hideTrainingChartLoader();
        hideTrainingSummaryTableLoader();
    }
}


async function loadActivitiesDropdown() {
    try {
        const response = await fetch('/api/activities_dropdown');
        const activities = await response.json();
        
        const container = $('#activity-checkboxes');
        container.empty();
        
        activities.forEach(activity => {
            const checkboxHtml = `
                <div class="form-check mb-1">
                    <input class="form-check-input activity-checkbox" type="checkbox" value="${activity.id}" id="activity-${activity.id}" checked>
                    <label class="form-check-label" for="activity-${activity.id}">
                        ${activity.name}
                    </label>
                </div>
            `;
            container.append(checkboxHtml);
        });

        $('.activity-checkbox').on('change', handleActivityChange);
        $('#select-all-activities').on('change', handleSelectAll);
        updateActivityDisplay();
    } catch (error) {
        console.error('Error loading activities:', error);
    }
}

function handleSelectAll() {
    const isChecked = $('#select-all-activities').is(':checked');
    $('.activity-checkbox').prop('checked', isChecked);
    updateActivityDisplay();
    loadTrainingChartData();
}

function handleActivityChange() {
    const totalActivities = $('.activity-checkbox').length;
    const checkedActivities = $('.activity-checkbox:checked').length;
    $('#select-all-activities').prop('checked', checkedActivities === totalActivities);
    updateActivityDisplay();
    loadTrainingChartData();
}

function updateActivityDisplay() {
    const totalActivities = $('.activity-checkbox').length;
    const checkedActivities = $('.activity-checkbox:checked').length;
    const displayElement = $('#activity-display');

    if (checkedActivities === 0) {
        displayElement.text('No Activities Selected');
    } else if (checkedActivities === totalActivities) {
        displayElement.text('All Activities');
    } else {
        displayElement.text(`${checkedActivities} Activities Selected`);
    }
}

// function getSelectedActivityIds() {
//     return $('.activity-checkbox:checked').map(function () {
//         return parseInt($(this).val());
//     }).get();
// }
// Utility: get selected activity ids
function getSelectedActivityIds() {
    const total = $('.activity-checkbox').length;
    // If no checkboxes yet in DOM => treat as "not loaded" (default = all selected)
    if (total === 0) return null;
    return $('.activity-checkbox:checked').map(function () {
        return parseInt($(this).val(), 10);
    }).get();
}
async function printTrainingPage() {
    try {
        showPrintLoading();
        const chartImage = await captureTrainingChartAsImage();
        const filters = getTrainingFilters();
        const printContent = generateTrainingPrintContent(chartImage, filters);
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

async function captureTrainingChartAsImage() {
    try {
        if (trainingChartInstance) {
            const chartImage = await trainingChartInstance.dataURI({
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

function getTrainingFilters() {
    const district = $('#district option:selected').text();
    const circle = $('#circle option:selected').text();
    const gramPanchayat = $('#gram_panchayat option:selected').text();
    const village = $('#village option:selected').text();
    const activityDisplay = $('#activity-display').text();
    
    return {
        district: district !== 'Select Districts' ? district : 'All Districts',
        circle: circle !== 'Select Circle' ? circle : 'All Circles',
        gramPanchayat: gramPanchayat !== 'Select Gram Panchayat' ? gramPanchayat : 'All Gram Panchayats',
        village: village !== 'Select Villages' ? village : 'All Villages',
        activities: activityDisplay || 'All Activities'
    };
}

function generateTrainingPrintContent(chartImage, filters) {
    const currentDate = new Date().toLocaleDateString('en-IN', {
        year: 'numeric', month: 'long', day: 'numeric'
    });
    const currentTime = new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit'
    });
    const progressTable = getTrainingTableHTML();
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Training Activities Report</title>
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
                .notstarted { background-color: #357AF6 !important; -webkit-print-color-adjust: exact !important; }
                .completed { background-color: #679436 !important; -webkit-print-color-adjust: exact !important; }
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
                    <h1>Training Activities Report</h1>
                    <div class="report-info">
                        <span><strong>Generated on:</strong> ${currentDate} at ${currentTime}</span>
                        <span><strong>Report Type:</strong> Training Progress Analysis</span>
                    </div>
                </div>
                
                <div class="filters-section">
                    <div class="filters-title">Applied Filters:</div>
                    <div class="filters-grid">
                        <div class="filter-item"><span class="filter-label">District:</span><span class="filter-value">${filters.district}</span></div>
                        <div class="filter-item"><span class="filter-label">Circle:</span><span class="filter-value">${filters.circle}</span></div>
                        <div class="filter-item"><span class="filter-label">Gram Panchayat:</span><span class="filter-value">${filters.gramPanchayat}</span></div>
                        <div class="filter-item"><span class="filter-label">Village:</span><span class="filter-value">${filters.village}</span></div>
                        <div class="filter-item" style="grid-column: 1 / -1;"><span class="filter-label">Activities:</span><span class="filter-value">${filters.activities}</span></div>
                    </div>
                </div>
                
               <!-- <div class="chart-section">
                    <div class="chart-title">Training Activities Progress Status</div>
                    <div class="chart-container">
                        ${chartImage ? `<img src="${chartImage}" alt="Training Progress Chart" class="chart-image" />` : `<div class="no-chart">Chart not available for printing</div>`}
                    </div>
                </div>
                -->
               <!-- <div class="section-title" style="page-break-before: always;">Training Progress Status Summary</div> -->
                <div class="section-title" >Training Progress Status Summary</div>
                <div class="table-container">
                    <div class="table-header">
                        <span>Progress Status Overview</span>
                        <div class="legend">
                            <div class="legend-item"><div class="legend-color notstarted"></div><span>Not Started</span></div>
                            <div class="legend-item"><div class="legend-color completed"></div><span>Completed</span></div>
                        </div>
                    </div>
                    ${progressTable}
                </div>
            </div>
        </body>
        </html>
    `;
}

function getTrainingTableHTML() {
    const table = document.getElementById('training_table');
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

function showTrainingChartLoader() {
    document.getElementById('training_chart').innerHTML = `
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

function hideTrainingChartLoader() {
    // Loader is hidden when chart renders
}

function showTrainingSummaryTableLoader() {
    const tbody = document.querySelector('#training_table tbody');
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

function hideTrainingSummaryTableLoader() {
    // Loader is hidden when table renders
}

$(document).ready(function() {
    loadActivitiesDropdown();
    loadTrainingChartData();
    
    $('#district, #circle, #gram_panchayat, #village').on('change', loadTrainingChartData);
});
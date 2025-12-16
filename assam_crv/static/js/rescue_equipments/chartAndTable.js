// Chart and Table functionality for Rescue Equipments
let rescueEquipmentChartInstance = null;

async function loadEquipmentsDropdown() {
    try {
        const response = await fetch('/api/equipments_dropdown/');
        const equipments = await response.json();

        const container = $('#equipment-checkboxes');
        container.empty();

        equipments.forEach(equipment => {
            const checkboxHtml = `
                <div class="form-check mb-1">
                    <input class="form-check-input equipment-checkbox" type="checkbox" value="${equipment.id}" id="equipment-${equipment.id}" checked>
                    <label class="form-check-label" for="equipment-${equipment.id}">
                        ${equipment.name}
                    </label>
                </div>
            `;
            container.append(checkboxHtml);
        });

        $('.equipment-checkbox').on('change', handleEquipmentChange);
        $('#select-all-equipments').on('change', handleSelectAllEquipments);
        updateEquipmentDisplay();
    } catch (error) {
        console.error('Error loading equipments:', error);
    }
}

function handleSelectAllEquipments() {
    const isChecked = $('#select-all-equipments').is(':checked');
    $('.equipment-checkbox').prop('checked', isChecked);
    updateEquipmentDisplay();
    loadRescueEquipmentChartData(); // will respect empty selection
}

function handleEquipmentChange() {
    const totalEquipments = $('.equipment-checkbox').length;
    const checkedEquipments = $('.equipment-checkbox:checked').length;

    // Update "Select All" checkbox
    $('#select-all-equipments').prop('checked', checkedEquipments === totalEquipments);

    updateEquipmentDisplay();
    loadRescueEquipmentChartData(); // will respect empty selection
}

function updateEquipmentDisplay() {
    const totalEquipments = $('.equipment-checkbox').length;
    const checkedEquipments = $('.equipment-checkbox:checked').length;
    const displayElement = $('#equipment-display');

    if (checkedEquipments === 0) {
        displayElement.text('No Equipments Selected');
    } else if (checkedEquipments === totalEquipments) {
        displayElement.text('All Equipments'); // default text
    } else {
        displayElement.text(`${checkedEquipments} Equipments Selected`);
    }
}


// function getSelectedEquipmentIds() {
//     return $('.equipment-checkbox:checked').map(function () {
//         return parseInt($(this).val());
//     }).get();
// }
function getSelectedEquipmentIds() {
    const total = $('.equipment-checkbox').length;
    // If no checkboxes yet in DOM => treat as "not loaded" (default = all selected)
    if (total === 0) return null;
    return $('.equipment-checkbox:checked').map(function () {
        return parseInt($(this).val(), 10);
    }).get();
}
async function loadRescueEquipmentChartData() {
    try {
        // Show loaders
        showChartLoader();
        showSummaryTableLoader();

        const params = new URLSearchParams();

        const districtId = $('#rescue_equipment_district_select').val();
        const circleId = $('#rescue_equipment_circle').val();
        const gpId = $('#rescue_equipment_gram_panchayat').val();
        const villageId = $('#rescue_equipment_village_select').val();
        const equipmentIds = getSelectedEquipmentIds();
        // If no equipment selected, show "No data available" and return early
        if (!equipmentIds || equipmentIds.length === 0) {
            const chartDiv = document.getElementById('rescue_equipment_chart');
            if (chartDiv) {
                chartDiv.innerHTML = '<div class="text-center p-5">No data available</div>';
            }

            const tbody = document.querySelector('#rescue_equipment_summary_table tbody');
            if (tbody) {
                tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center p-5">No data available</td>
                </tr>
            `;
            }
            return; // Stop further API call
        }
        if (districtId) params.append('district_id', districtId);
        if (circleId) params.append('circle_id', circleId);
        if (gpId) params.append('gram_panchayat_id', gpId);
        if (villageId) params.append('village_id', villageId);
        if (equipmentIds && equipmentIds.length > 0) params.append('equipment_ids', equipmentIds.join(','));

        const response = await fetch(`/api/rescue_equipment_chart_data/?${params.toString()}`);
        const data = await response.json();

        renderRescueEquipmentChart(data);
        renderRescueEquipmentSummaryTable(data);
    } catch (error) {
        console.error('Error loading chart data:', error);
        document.getElementById('rescue_equipment_chart').innerHTML = '<div class="text-center p-5 text-danger">Error loading chart</div>';
        hideChartLoader();
        hideSummaryTableLoader();
    }
}

function showChartLoader() {
    document.getElementById('rescue_equipment_chart').innerHTML = `
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

function hideChartLoader() {
    // Loader is hidden when chart renders
}

function showSummaryTableLoader() {
    const tbody = document.querySelector('#rescue_equipment_summary_table tbody');
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

function hideSummaryTableLoader() {
    // Loader is hidden when table renders
}

function renderRescueEquipmentChart(data) {
    const chartDiv = document.getElementById('rescue_equipment_chart');
    if (!chartDiv) return;

    if (rescueEquipmentChartInstance) {
        rescueEquipmentChartInstance.destroy();
        rescueEquipmentChartInstance = null;
    }

    if (!Array.isArray(data) || data.length === 0) {
        chartDiv.innerHTML = '<div class="text-center p-5">No data available</div>';
        return;
    }

    // Clear loader
    chartDiv.innerHTML = '';

    const categories = data.map(item => {
        const maxLength = 15;
        return item.equipment.length > maxLength
            ? item.equipment.slice(0, maxLength) + '…'
            : item.equipment;
    });
    const fullCategories = data.map(item => item.equipment);
    const availableData = data.map(item => item.available);
    const notAvailableData = data.map(item => item.not_available);

    const options = {
        series: [
            {
                name: 'Available',
                data: availableData
            },
            {
                name: 'Not Available',
                data: notAvailableData
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
            categories: categories,
            labels: {
                style: {
                    fontSize: '12px',
                    fontWeight: 'bold'
                },
                rotate: -45,
                rotateAlways: true
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
                    return fullCategories[opts.dataPointIndex];
                }
            }
        }
    };

    rescueEquipmentChartInstance = new ApexCharts(chartDiv, options);
    rescueEquipmentChartInstance.render().then(() => {
        setTimeout(() => {
            const labels = document.querySelectorAll('.apexcharts-xaxis-label');
            labels.forEach((label, index) => {
                const fullText = fullCategories[index];
                const titleElement = label.querySelector('title');
                if (titleElement && fullText) {
                    titleElement.textContent = fullText;
                }
            });
        }, 500);
    });
}

function renderRescueEquipmentSummaryTable(data) {
    const table = document.getElementById('rescue_equipment_summary_table');
    if (!table) return;

    const tbody = table.querySelector('tbody') || table.createTBody();
    tbody.innerHTML = ''; // This clears the loader

    data.forEach((item, index) => {
        const total = parseInt(item.available) + parseInt(item.not_available);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class='text-center'>${index + 1}</td>
            <td class='text-start'>${item.equipment}</td>
            <td class='text-center bg-blue'>${item.not_available}</td>
            <td class='text-center bg-green'>${item.available}</td>
            <td class='text-center font-weight-bold'>${total}</td>
        `;
        tbody.appendChild(row);
    });
}

// Print functionality
async function printRescueEquipmentToPDF() {
    try {
        showPrintLoading();

        const chartImage = await captureRescueEquipmentChart();
        const filters = getCurrentRescueFilters();
        const printContent = generateRescueEquipmentPrintContent(chartImage, filters);

        createRescueEquipmentPrintWindow(printContent);

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
    if (loading) {
        loading.remove();
    }
}

async function captureRescueEquipmentChart() {
    try {
        if (rescueEquipmentChartInstance) {
            const chartImage = await rescueEquipmentChartInstance.dataURI({
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

function getCurrentRescueFilters() {
    const district = $('#rescue_equipment_district_select option:selected').text();
    const circle = $('#rescue_equipment_circle option:selected').text();
    const gramPanchayat = $('#rescue_equipment_gram_panchayat option:selected').text();
    const village = $('#rescue_equipment_village_select option:selected').text();
    const equipmentDisplay = $('#equipment-display').text();

    return {
        district: district !== 'Select Districts' ? district : 'All Districts',
        circle: circle !== 'Select Circle' ? circle : 'All Circles',
        gramPanchayat: gramPanchayat !== 'Select Gram Panchayat' ? gramPanchayat : 'All Gram Panchayats',
        village: village !== 'Select Villages' ? village : 'All Villages',
        equipments: equipmentDisplay || 'All Equipments'
    };
}

function generateRescueEquipmentPrintContent(chartImage, filters) {
    const currentDate = new Date().toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    const currentTime = new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
    });

    const summaryElement = document.querySelector('.summary-line span');
    const summaryText = summaryElement ? summaryElement.textContent : '';

    const summaryTable = getRescueEquipmentSummaryTableHTML();

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rescue Equipment Report</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                    color: #333;
                    background: white;
                }
                
                .print-container {
                    max-width: 210mm;
                    margin: 0 auto;
                    padding: 10mm;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #245FAE;
                    padding-bottom: 15px;
                }
                
                .header h1 {
                    color: #245FAE;
                    font-size: 24px;
                    margin-bottom: 8px;
                    font-weight: bold;
                }
                
                .report-info {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 15px 0;
                    font-size: 11px;
                    color: #666;
                }
                
                .filters-section {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border: 1px solid #dee2e6;
                }
                
                .filters-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #245FAE;
                    font-size: 14px;
                }
                
                .filters-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 8px;
                    font-size: 11px;
                }
                
                .filter-item {
                    display: flex;
                }
                
                .filter-label {
                    font-weight: 600;
                    min-width: 100px;
                    color: #495057;
                }
                
                .filter-value {
                    color: #212529;
                }
                
                .summary-section {
                    background: #e7f3ff;
                    padding: 12px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                    border-left: 4px solid #245FAE;
                }
                
                .summary-section p {
                    margin: 0;
                    color: #245FAE;
                    font-weight: 500;
                }
                
                .chart-section {
                    margin-bottom: 25px;
                    text-align: center;
                }
                
                .chart-title {
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #245FAE;
                    text-align: center;
                }
                
                .chart-container {
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    background: white;
                    display: inline-block;
                }
                
                .chart-image {
                    max-width: 100%;
                    height: auto;
                    width: 100%;
                    border-radius: 4px;
                }
                
                .no-chart {
                    padding: 40px;
                    text-align: center;
                    color: #6c757d;
                    font-style: italic;
                    border: 2px dashed #dee2e6;
                    border-radius: 8px;
                }
                
                .section-title {
                    font-size: 16px;
                    font-weight: bold;
                    margin: 25px 0 15px 0;
                    color: #245FAE;
                    border-bottom: 2px solid #245FAE;
                    padding-bottom: 5px;
                }
                
                .table-container {
                    margin-bottom: 25px;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                .table-header {
                    background: #245FAE !important;
                    color: white !important;
                    padding: 10px;
                    font-weight: bold;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                
                .legend {
                    display: flex;
                    gap: 15px;
                    font-size: 10px;
                    align-items: center;
                }
                
                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                
                .legend-color {
                    width: 12px;
                    height: 12px;
                    border-radius: 2px;
                }
                
                .notstarted { 
                    background-color: #679436 !important;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                .completed { 
                    background-color: #357AF6 !important;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 11px;
                }
                
                th, td {
                    border: 1px solid #dee2e6;
                    padding: 8px;
                    text-align: center;
                }
                
                th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                    color: #495057;
                }
                
                tbody tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                
                .text-left { text-align: left !important; }
                .text-center { text-align: center !important; }
                .font-weight-bold { font-weight: bold; }
                
                .bg-green { 
                    background-color: rgba(103, 148, 54, 0.1) !important;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                .bg-blue { 
                    background-color: rgba(53, 122, 246, 0.1) !important;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                
                .footer {
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #dee2e6;
                    text-align: center;
                    font-size: 10px;
                    color: #6c757d;
                }
                
                @media print {
                    body { margin: 0; }
                    .print-container { margin: 0; padding: 6mm; }
                   <!-- .chart-section { page-break-inside: avoid; }
                    .table-container { page-break-inside: avoid; }
                    .section-title { page-break-after: avoid; }-->
                    .table-header {
                        background: #245FAE !important;
                        color: white !important;
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }
                    .notstarted, .completed, .bg-green, .bg-blue {
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }
                }
                    @media print {
  .table-container { page-break-inside: auto; } /* instead of avoid */
}

                
                @page {
                    size: A4;
                    margin: 8mm;
                }
            </style>
        </head>
        <body>
            <div class="print-container">
                <div class="header">
                    <h1>Rescue Equipment Report</h1>
                    <div class="report-info">
                        <span><strong>Generated on:</strong> ${currentDate} at ${currentTime}</span>
                        <span><strong>Report Type:</strong> Equipment Availability Analysis</span>
                    </div>
                </div>
                
                <div class="filters-section">
                    <div class="filters-title">Applied Filters:</div>
                    <div class="filters-grid">
                        <div class="filter-item">
                            <span class="filter-label">District:</span>
                            <span class="filter-value">${filters.district}</span>
                        </div>
                        <div class="filter-item">
                            <span class="filter-label">Circle:</span>
                            <span class="filter-value">${filters.circle}</span>
                        </div>
                        <div class="filter-item">
                            <span class="filter-label">Gram Panchayat:</span>
                            <span class="filter-value">${filters.gramPanchayat}</span>
                        </div>
                        <div class="filter-item">
                            <span class="filter-label">Village:</span>
                            <span class="filter-value">${filters.village}</span>
                        </div>
                        <div class="filter-item" style="grid-column: 1 / -1;">
                            <span class="filter-label">Equipments:</span>
                            <span class="filter-value">${filters.equipments}</span>
                        </div>
                    </div>
                </div>
                
                ${summaryText ? `
                <div class="summary-section">
                    <p><i class="fas fa-info-circle"></i> ${summaryText}</p>
                </div>
                ` : ''}
                
                <!-- <div class="chart-section">
                    <div class="chart-title">Rescue Equipment Availability</div>
                    <div class="chart-container">
                        ${chartImage ?
            `<img src="${chartImage}" alt="Rescue Equipment Chart" class="chart-image" />` :
            `<div class="no-chart">Chart not available for printing</div>`
        }
                    </div>
                </div> -->
                
                <div class="section-title">Equipment Availability Summary</div>
                <div class="table-container">
                    <div class="table-header">
                        <span>Equipment Status Overview</span>
                        <div class="legend">
                            <div class="legend-item">
                                <div class="legend-color notstarted"></div>
                                <span>Not Available</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color completed"></div>
                                <span>Available</span>
                            </div>
                        </div>
                    </div>
                    ${summaryTable}
                </div>
                
                <div class="footer">
                    <p><strong>Rescue Equipment Management System</strong> | Generated automatically | Page 1 of 1</p>
                    <p>This report contains confidential information. Please handle accordingly.</p>
                </div>
            </div>
        </body>
        </html>
    `;
}

function getRescueEquipmentSummaryTableHTML() {
    const table = document.getElementById('rescue_equipment_summary_table');
    if (!table) return '<p>Table not available</p>';

    const clonedTable = table.cloneNode(true);

    const rows = clonedTable.querySelectorAll('tr');
    rows.forEach(row => {
        row.classList.remove('odd', 'even');
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

function createRescueEquipmentPrintWindow(htmlContent) {
    const printWindow = window.open('', '_blank', 'width=1200,height=800,left=100,top=50,scrollbars=yes,resizable=yes');

    if (!printWindow) {
        alert('Please allow popups for this website to enable printing.');
        return;
    }

    printWindow.document.write(htmlContent);
    printWindow.document.close();

    printWindow.onload = function () {
        setTimeout(() => {
            printWindow.focus();
            printWindow.print();

            setTimeout(() => {
                printWindow.close();
            }, 1000);
        }, 500);
    };
}

// Export functions for global use
window.printRescueEquipmentToPDF = printRescueEquipmentToPDF;


document.addEventListener('DOMContentLoaded', () => {
    loadEquipmentsDropdown();

    loadRescueEquipmentChartData();
});
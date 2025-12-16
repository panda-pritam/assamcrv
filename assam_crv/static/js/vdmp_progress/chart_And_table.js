// Global chart instance to manage chart updates
let chartInstance = null;

// function renderVDMPChart(data) {
//     const chartDiv = document.getElementById('VDMP_progress_page_chart');
//     if (!chartDiv) {
//         console.error('Chart container not found!');
//         return;
//     }

//     // Clear previous chart if exists
//     if (chartInstance) {
//         chartInstance.destroy();
//         chartInstance = null;
//     }

//     // Prepare data for stacked chart
//     const categories = data.map(item => item.activity);
//     const categories_label = data.map(item => {
//         const maxLength = 10;
//         return item.activity.length > maxLength
//             ? item.activity.slice(0, maxLength) + '…'
//             : item.activity;
//     });

//     // Prepare series data for stacked chart
//     const notStartedData = data.map(item => parseInt(item.not_started) || 0);
//     const inProgressData = data.map(item => parseInt(item.in_progress) || 0);
//     const completedData = data.map(item => parseInt(item.completed) || 0);

//     // Update chart title
//     document.getElementById('chartTitle').textContent = gettext('VDMP Activity Progress Status');

//     const options = {
//         series: [
//             {
//                 name: gettext('Completed'),
//                 data: completedData
//             },
//             {
//                 name: gettext('Not Started'),
//                 data: notStartedData
//             },
//             // {
//             //     name: gettext('In Progress'),
//             //     data: inProgressData
//             // },

//         ],
//         chart: {
//             type: 'bar',
//             height: '100%',
//             stacked: true,
//             toolbar: {
//                 show: true,
//                 tools: {
//                     download: true,
//                     selection: false,
//                     zoom: false,
//                     zoomin: false,
//                     zoomout: false,
//                     pan: false,
//                     reset: false
//                 }
//             },
//             animations: {
//                 enabled: true,
//                 easing: 'easeinout',
//                 speed: 800
//             }
//         },
//         colors: [ '#679436', '#357AF6'], // Blue, Yellow, Green
//         plotOptions: {
//             bar: {
//                 horizontal: false,
//                 columnWidth: '60%',
//                 endingShape: 'rounded',
//                 borderRadius: 0
//             }
//         },
//         dataLabels: {
//             enabled: true,
//             style: {
//                 fontSize: '10px',
//                 colors: ['#fff'],
//                 fontWeight: 'bold'
//             },
//             formatter: function (val) {
//                 return val > 0 ? val : '';
//             }
//         },
//         xaxis: {
//             categories: categories_label,
//             labels: {
//                 style: {
//                     fontSize: '14px',
//                     colors: '#666',
//                     fontWeight: 'bold',
//                 },
//                 rotate: -45,
//                 rotateAlways: true,
//             },
//             axisBorder: {
//                 show: true,
//                 color: '#E4E4E4'
//             },
//             axisTicks: {
//                 show: true,
//                 color: '#E4E4E4'
//             },
//             title: {
//                 text: gettext('VDMP Activities'),
//                 offsetY: -30,
//                 style: {
//                     fontSize: '14px',
//                     fontWeight: 'bold',
//                     color: '#333',
//                 }
//             }
//         },
//         yaxis: {
//             title: {
//                 text: gettext('Count Of Villages'),
//                 style: {
//                     fontSize: '14px',
//                     fontWeight: 'bold',
//                     color: '#333'
//                 }
//             },
//             labels: {
//                 style: {
//                     fontSize: '12px',
//                     colors: '#666'
//                 }
//             },
//             min: 0,

//         },
//         legend: {
//             position: 'top',
//             horizontalAlign: 'center',
//             offsetY: 0,
//             markers: {
//                 width: 12,
//                 height: 12,
//                 radius: 0
//             },
//             itemMargin: {
//                 horizontal: 15,
//                 vertical: 5
//             }
//         },
//         grid: {
//             show: true,
//             borderColor: '#F1F1F1',
//             strokeDashArray: 3,
//             position: 'back',
//             xaxis: {
//                 lines: {
//                     show: false
//                 }
//             },
//             yaxis: {
//                 lines: {
//                     show: true
//                 }
//             }
//         },
//         tooltip: {
//             theme: 'light',
//             style: {
//                 fontSize: '12px'
//             },
//             y: {
//                 formatter: function (val) {
//                     return val + ' ' + gettext('villages');
//                 }
//             },
//             x: {
//                 formatter: function (val, opts) {
//                     console.log('Tooltip data:', {
//                         clippedValue: val,
//                         fullValue: categories[opts.dataPointIndex],
//                         index: opts.dataPointIndex
//                     });
//                     return categories[opts.dataPointIndex];
//                 }
//             }
//         },
//         responsive: [{
//             breakpoint: 768,
//             options: {
//                 chart: {
//                     height: 500
//                 },
//                 plotOptions: {
//                     bar: {
//                         columnWidth: '70%'
//                     }
//                 },
//                 xaxis: {
//                     labels: {
//                         rotate: -90,
//                         style: {
//                             fontSize: '10px'
//                         }
//                     }
//                 },
//                 legend: {
//                     position: 'bottom',
//                     offsetY: 10
//                 }
//             }
//         }]
//     };

//     // Render the chart
//     chartInstance = new ApexCharts(chartDiv, options);
//     chartInstance.render().then(() => {
//         // Wait for the chart to be fully rendered
//         setTimeout(() => {
//             // Get all x-axis label elements
//             const labels = document.querySelectorAll('.apexcharts-xaxis-label');

//             // Loop through each label
//             labels.forEach((label, index) => {
//                 // Get the corresponding full text from your original data
//                 const fullText = categories[index];

//                 // Find the <title> element inside the label
//                 const titleElement = label.querySelector('title');

//                 // Update the title element with the full text
//                 if (titleElement && fullText) {
//                     titleElement.textContent = fullText;
//                 }
//             });
//         }, 500); // Small delay to ensure chart is fully rendered
//     }).catch(error => {
//         console.error('Error rendering chart:', error);
//         chartDiv.innerHTML = '<div class="text-center p-5 text-danger">Error rendering chart</div>';
//     });
// }
function renderVDMPChart(data) {
    const chartDiv = document.getElementById('VDMP_progress_page_chart');
    if (!chartDiv) {
        console.error('Chart container not found!');
        return;
    }

    // Clear previous chart if exists
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }

    // Prepare data for stacked chart
    const categories = data.map(item => item.activity);
    const categories_label = data.map(item => {
        const maxLength = 10;
        return item.activity.length > maxLength
            ? item.activity.slice(0, maxLength) + '…'
            : item.activity;
    });

    // Series data
    const notStartedData = data.map(item => parseInt(item.not_started) || 0);
    const completedData   = data.map(item => parseInt(item.completed) || 0);

    // Update chart title
    document.getElementById('chartTitle').textContent = gettext('VDMP Activity Progress Status');

    const options = {
        series: [
            { name: gettext('Completed'), data: completedData },
            { name: gettext('Not Started'), data: notStartedData }
        ],
        chart: {
            type: 'bar',
            // ✅ Dynamic height with cap (no overlap on Nest Hub Max)
            height: Math.min(data.length * 45, 800),
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
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        colors: ['#679436', '#357AF6'],
        plotOptions: {
            bar: {
                horizontal: true,
                columnWidth: '60%',
                barHeight: '70%',
                borderRadius: 0
            }
        },
        dataLabels: {
            enabled: true,
            style: {
                fontSize: '10px',
                colors: ['#fff'],
                fontWeight: 'bold'
            },
            formatter: val => (val > 0 ? val : '')
        },
        yaxis: {
            title: {
                text: gettext('VDMP Activities'),
                style: { fontSize: '12px', fontWeight: 'bold', color: '#333' }
            },
            labels: {
                style: { fontSize: '13px', colors: '#666' },
                maxWidth: 300
            }
        },
        xaxis: {
            categories: categories,
            labels: {
                style: { fontSize: '12px', colors: '#666', fontWeight: 'bold' },
                rotate: 0
            },
            axisBorder: { show: true, color: '#E4E4E4' },
            axisTicks: { show: true, color: '#E4E4E4' },
            title: {
                text: gettext('Count Of Villages'),
                style: { fontSize: '14px', fontWeight: 'bold', color: '#333' }
            },
            min: 0
        },
        legend: {
            position: 'top',
            horizontalAlign: 'center',
            markers: { width: 12, height: 12, radius: 0 },
            itemMargin: { horizontal: 15, vertical: 5 }
        },
        grid: {
            borderColor: '#F1F1F1',
            strokeDashArray: 3,
            xaxis: { lines: { show: true } },
            yaxis: { lines: { show: false } }
        },
        tooltip: {
            theme: 'light',
            style: { fontSize: '12px' },
            y: { formatter: val => val + ' ' + gettext('villages') },
            x: {
                formatter: (val, opts) => categories[opts.dataPointIndex]
            }
        },
         maintainAspectRatio: false,
        responsive: [
            {
                // ✅ Special handling for Nest Hub Max (~1280px)
                breakpoint: 1400,
                options: {
                    chart: { height: Math.min(data.length * 35, 650) },
                    plotOptions: { bar: { columnWidth: '65%', barHeight: '60%' } },
                    xaxis: { labels: { style: { fontSize: '11px' } } },
                    legend: { position: 'bottom', offsetY: 5 }
                }
            },
            {
                breakpoint: 768, // tablets/mobiles
                options: {
                    chart: { height: Math.min(data.length * 30, 500) },
                    plotOptions: { bar: { columnWidth: '70%' } },
                    xaxis: { labels: { style: { fontSize: '10px' } } },
                    legend: { position: 'bottom', offsetY: 10 }
                }
            }
        ]
    };

    chartInstance = new ApexCharts(chartDiv, options);
    chartInstance.render().then(() => {
        setTimeout(() => {
            const yLabels = document.querySelectorAll('.apexcharts-yaxis-label');
            const xLabels = document.querySelectorAll('.apexcharts-xaxis-label');
            if (yLabels.length) {
                yLabels.forEach((label, index) => {
                    const fullText = categories[index];
                    const titleElement = label.querySelector('title');
                    if (titleElement && fullText) titleElement.textContent = fullText;
                });
            } else if (xLabels.length) {
                xLabels.forEach((label, index) => {
                    const fullText = categories[index];
                    const titleElement = label.querySelector('title');
                    if (titleElement && fullText) titleElement.textContent = fullText;
                });
            }
        }, 500);
    }).catch(error => {
        console.error('Error rendering chart:', error);
        chartDiv.innerHTML = '<div class="text-center p-5 text-danger">Error rendering chart</div>';
    });
}

// Updated event listener for chart (removed filter)
document.addEventListener('DOMContentLoaded', async () => {

    colorChange('vdmp_progress')

    const chartDiv = document.getElementById('VDMP_progress_page_chart');
    if (!chartDiv) {
        console.error('Chart container not found! Check the ID: VDMP_progress_page_chart');
    } else {
        console.log('Chart container found:', chartDiv);
    }

    const VDMP_progress_table = document.getElementById('VDMP_progress_table');
    if (!VDMP_progress_table) {
        console.error('Table not found! Check the ID: VDMP_progress_table');
    }

    // Initialize Select2 dropdowns
    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('village', gettext('Select Villages'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('circle', gettext('Select Circle'));
    // Load activities for custom dropdown
    await loadActivities();

    // Initialize detailed progress table
    initializeDetailedProgressTable();

    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village')
    await updateSummaryText(true);

    // Load initial chart & table
    try {
        await getTableAndChartData();
    } catch (error) {
        console.error('Error loading initial data:', error);
    }

    // Add event listeners for filter changes
    $('#district').on('change', handleFilterChange);
    $('#village').on('change', handleFilterChange);
    $('#gram_panchayat').on('change', handleFilterChange);
    $('#circle').on('change', handleFilterChange);
    // Activity filter handled by checkbox events
});

async function loadActivities() {
    try {
        const response = await fetch('/api/dropdown_vdmp_activity');
        const activities = await response.json();

        const container = $('#activity-checkboxes');
        container.empty();

        activities.forEach(activity => {
            const checkboxHtml = `
                <div class="form-check mb-1">
                    <input class="form-check-input activity-checkbox" type="checkbox" value="${activity.id}" id="activity-${activity.id}" checked>
                    <label class="form-check-label" for="activity-${activity.id}" style="font-size: 13px;">
                        ${activity.name}
                    </label>
                </div>
            `;
            container.append(checkboxHtml);
        });

        // Add event listeners
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
    handleFilterChange(true);
}

function handleActivityChange() {
    const totalActivities = $('.activity-checkbox').length;
    const checkedActivities = $('.activity-checkbox:checked').length;

    $('#select-all-activities').prop('checked', checkedActivities === totalActivities);
    updateActivityDisplay();
    handleFilterChange(true);
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

function getSelectedActivityIds() {
    const total = $('.activity-checkbox').length;
    // If no checkboxes yet in DOM => treat as "not loaded" (default = all selected)
    if (total === 0) return null;
    return $('.activity-checkbox:checked').map(function () {
        return parseInt($(this).val(), 10);
    }).get();
}

async function handleFilterChange(reloadTableAndChart = false) {
    const districtId = $('#district').val();
    const villageId = $('#village').val();
    const circle_id = $('#circle').val();
    const gram_panchayat_id = $('#gram_panchayat').val();
    const activityIds = getSelectedActivityIds();
    // 🚨 If no activity is selected → show "No data" and stop here
    if (!activityIds || activityIds.length === 0) {
        document.getElementById('VDMP_progress_page_chart').innerHTML =
            '<div class="text-center p-5">No data available</div>';

        const table = document.getElementById('VDMP_progress_table');
        if (table) {
            const tbody = table.querySelector('tbody') || table.createTBody();
            tbody.innerHTML =
                `<tr><td colspan="5" class="text-center text-muted">No data available</td></tr>`;
        }

        // also clear detailed progress table
        populateDetailedProgressTable([]);

        return; // stop, don’t fetch API
    }
    // Update both chart and table
    // await getTableAndChartData(districtId, circle_id, gram_panchayat_id, villageId, activityIds);

    if (reloadTableAndChart) {
        await getTableAndChartData(districtId, circle_id, gram_panchayat_id, villageId, activityIds);
    } else {
        getChartData(districtId, circle_id, gram_panchayat_id, villageId, activityIds)
    }
    await updateSummaryText(true);
}

let detailedProgressTable = null;

function initializeDetailedProgressTable() {
    const columns = [
        { title: gettext("S. No."), width: "5%" },
        { title: gettext("District") },
        { title: gettext("Village") },
        { title: gettext("Activity Name") },
        { title: gettext("Status") }
    ];

    detailedProgressTable = initializeDataTable('vdmp_detailed_progress_table', columns);
}

// Original function - loads both chart and table (used for initial load)
async function getTableAndChartData(district_id = '', circle_id = '', gram_panchayat_id = '', village_id = '', activity_ids = []) {
    try {
        // Show loaders
        showVDMPChartLoader();
        showVDMPSummaryTableLoader();

        const params = new URLSearchParams();

        if (district_id) params.append('district_id', district_id);
        if (circle_id) params.append('circle_id', circle_id);
        if (gram_panchayat_id) params.append('gram_panchayat_id', gram_panchayat_id);
        if (village_id) params.append('village_id', village_id);
        if (activity_ids && activity_ids.length > 0) params.append('activity_ids', activity_ids.join(','));

        let url = '/api/get_vdmp_activity_status_data';
        const query = params.toString();
        if (query) {
            url += `?${query}`;
        }

        console.log('Fetching data from URL:', url);
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`API request failed with status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Data received:', data);

        if (!Array.isArray(data) || data.length === 0) {
            console.warn('No data available for chart rendering');
            document.getElementById('VDMP_progress_page_chart').innerHTML = '<div class="text-center p-5">No data available</div>';
            return;
        }

        renderVDMPChart(data);
        renderVDMPTable(data);

        // Hide loaders after successful rendering
        hideVDMPChartLoader();
        hideVDMPSummaryTableLoader();

        // Load detailed progress data
        // Load detailed progress data with activity filtering
        await loadDetailedProgressData(district_id, circle_id, gram_panchayat_id, village_id, activity_ids);

    } catch (error) {
        console.error("Error fetching or processing data:", error);
        document.getElementById('VDMP_progress_page_chart').innerHTML =
            `<div class="text-center p-5 text-danger">Error loading chart data: ${error.message}</div>`;
        hideVDMPChartLoader();
        hideVDMPSummaryTableLoader();
    }
}


// this function is to load the village level data 
// Load detailed progress data with activity filtering
// Update the function signature and add activity filtering
async function loadDetailedProgressData(district_id = '', circle_id = '', gram_panchayat_id = '', village_id = '', activity_ids = []) {
    try {
        const params = new URLSearchParams();

        if (district_id) params.append('district_id', district_id);
        if (circle_id) params.append('circle_id', circle_id);
        if (gram_panchayat_id) params.append('gram_panchayat_id', gram_panchayat_id);
        if (village_id) params.append('village_id', village_id);

        if (activity_ids && activity_ids.length > 0) {
            activity_ids.forEach(id => params.append('activity_id', id));
        }

        // Detect optional two-letter lang prefix like "/en/" and include it if present
        const langMatch = window.location.pathname.match(/^\/([a-z]{2})(?:\/|$)/i);
        const langPrefix = langMatch ? `/${langMatch[1]}` : '';

        let url = `${langPrefix}/api/vdmp_activity_status`;
        const query = params.toString();
        if (query) url += `?${query}`;

        // debug logging (remove in production)
        console.debug('Fetching VDMP url:', url);

        const response = await fetch(url);
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`API request failed with status ${response.status}: ${text}`);
        }

        const data = await response.json();
        populateDetailedProgressTable(data);
    } catch (error) {
        console.error('Error loading detailed progress data:', error);
    }
}



function populateDetailedProgressTable(data) {
    const rowMapper = (item, index) => [
        index + 1,
        item.district_name || '',
        item.village_name || '',
        item.activity_name || '',
        item.status || ''
    ];

    populateDataTable(detailedProgressTable, data, rowMapper);
}

// New function - updates only chart (used for filter changes)
async function getChartData(district_id = '', circle_id = '', gram_panchayat_id = '', village_id = '', activity_ids = []) {
    try {
        const params = new URLSearchParams();

        if (district_id) params.append('district_id', district_id);
        if (circle_id) params.append('circle_id', circle_id);
        if (gram_panchayat_id) params.append('gram_panchayat_id', gram_panchayat_id);
        if (village_id) params.append('village_id', village_id);
        if (activity_ids && activity_ids.length > 0) params.append('activity_ids', activity_ids.join(','));

        let url = '/api/get_vdmp_activity_status_data';
        const query = params.toString();
        if (query) {
            url += `?${query}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API request failed with status: ${response.status}`);
        }

        const data = await response.json();
        if (!Array.isArray(data) || data.length === 0) {
            document.getElementById('VDMP_progress_page_chart').innerHTML = '<div class="text-center p-5">No data available</div>';
            return;
        }

        // Only update chart, not table
        renderVDMPChart(data);
    } catch (error) {
        console.error("Error fetching chart data:", error);
        document.getElementById('VDMP_progress_page_chart').innerHTML =
            `<div class="text-center p-5 text-danger">Error loading chart data: ${error.message}</div>`;
    }
}

function renderVDMPTable(data) {
    const table = document.getElementById('VDMP_progress_table');
    if (!table) return;

    const tbody = table.querySelector('tbody') || table.createTBody();
    tbody.innerHTML = ''; // Clear old rows and loader

    data.forEach((item, index) => {
        const total = parseInt(item.not_started) + parseInt(item.in_progress) + parseInt(item.completed);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class='text-center'>${index + 1}</td>
            <td class='text-start'>${item.activity}</td>
            <td class='text-center bg-blue'>${item.not_started}</td>
          
            <td class='text-center bg-green'>${item.completed}</td>
            <td class='text-center font-weight-bold'>${total}</td>
        `;
        tbody.appendChild(row);
    });
}

function showVDMPChartLoader() {
    document.getElementById('VDMP_progress_page_chart').innerHTML = `
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

function hideVDMPChartLoader() {
    const chartDiv = document.getElementById('VDMP_progress_page_chart');
    if (chartDiv) {
        const loaderElements = chartDiv.querySelectorAll('.spinner-border, .d-flex');
        loaderElements.forEach(element => element.remove());
    }
}

function showVDMPSummaryTableLoader() {
    const tbody = document.querySelector('#VDMP_progress_table tbody');
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

function hideVDMPSummaryTableLoader() {
    const tbody = document.querySelector('#VDMP_progress_table tbody');
    if (tbody) {
        const loaderRows = tbody.querySelectorAll('tr');
        loaderRows.forEach(row => {
            if (row.innerHTML.includes('spinner-border')) {
                row.remove();
            }
        });
    }
}
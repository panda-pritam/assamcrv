// CRV Dashboard JavaScript with ApexCharts
let geoserverURL = "http://10.2.114.150:8085/geoserver";


let charts = {};

let baseMapTogglerBtn = document.getElementById('baseMapTogglerBtn');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function () {

    colorChange('en')

    baseLayer = new ol.layer.Tile({
        title: 'BaseMap',
        type: 'base',
        visible: true,
        zIndex: 0,
        source: new ol.source.OSM({
            crossOrigin: 'anonymous'
        })
    });

    // Create map with single base layer
    const map = new ol.Map({
        target: 'map-container',
        layers: [baseLayer], // Only one base layer
        view: new ol.View({
            projection: 'EPSG:4326',
            center: [92.9376, 26.2006],
            zoom: 7
        })
    });

    // Initialize Select2 dropdowns
    initializeSelect2('district', gettext('Select Districts'));
    initializeSelect2('village', gettext('Select Villages'));
    initializeSelect2('gram_panchayat', gettext('Select Gram Panchayat'));
    initializeSelect2('circle', gettext('Select Circle'));
    setupLocationSelectors('district', 'circle', 'gram_panchayat', 'village');
    New_updateSummaryText();

    $('#district, #circle, #gram_panchayat, #village').on('change', () => {

        New_updateSummaryText();
    });

    // Add event listeners for filter changes
    $('#district').on('change', handleFilterChange);
    $('#village').on('change', handleFilterChange);
    $('#gram_panchayat').on('change', handleFilterChange);
    $('#circle').on('change', handleFilterChange);

    const wmsLayer = new ol.layer.Tile({
        source: new ol.source.TileWMS({
            url: `${geoserverURL}/assam/wms`,
            params: {
                LAYERS: "assam:district_boundary", // workspace:layername
                TILED: true,
                FORMAT: "image/png",
                TRANSPARENT: true
            },
            serverType: "geoserver"
        })
    });
    mapObj = map;

    mapObj.addLayer(wmsLayer);

    initializeCharts();
    handleFilterChange(); // Initial load of chart data
});

document.addEventListener("DOMContentLoaded", function () {
    const togglerBtn = document.getElementById("baseMapTogglerBtn");
    const optionsDiv = document.getElementById("baseMapOptionsDiv");
    const closeBtn = document.getElementById("baseMapDivCloseButton");
    const basemapItems = document.querySelectorAll(".basemap-item");

    // Toggle visibility on button click
    togglerBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        optionsDiv.style.display =
            optionsDiv.style.display === "block" ? "none" : "block";
    });

    // Close on close button click
    closeBtn.addEventListener("click", function () {
        optionsDiv.style.display = "none";
    });

    // Close when clicking outside
    document.addEventListener("click", function (e) {
        if (
            optionsDiv.style.display === "block" &&
            !optionsDiv.contains(e.target) &&
            e.target !== togglerBtn
        ) {
            optionsDiv.style.display = "none";
        }
    });

    // Handle basemap switching
    basemapItems.forEach(item => {
        item.addEventListener("click", function () {
            const mapType = this.getAttribute("data-map-type");

            // Call your switch function
            switchBaseMapSource(mapType);

            // Update active class
            basemapItems.forEach(i => i.classList.remove("active"));
            this.classList.add("active");

            // Close after selection
            optionsDiv.style.display = "none";
        });
    });
});



// Initialize all charts
function initializeCharts() {
    const data = {
        total: 75.2,
        economic: 68.5,
        social: 72.3,
        environmental: 81.2,
        infrastructure: 69.8,
        institutional: 77.4,
        community: 82.1
    };

    // Total Score Chart - Donut with multiple segments
    charts.total = new ApexCharts(document.querySelector("#total-chart"), {
        series: [26.9, 12.2, 1.4, 3.2, 11.6, 7.3],
        chart: {
            type: 'donut',
            height: 320,
            width: '100%',
            toolbar: {
                show: true,
                tools: {
                    download: true, // enable download options
                    selection: false,
                    zoom: false,
                    zoomin: false,
                    zoomout: false,
                    pan: false,
                    reset: false,
                    customIcons: []
                }
            }
        },
        labels: [
            'Resilient Livelihoods & Economic Security',
            'Governance and Partnerships for Resilience',
            'Resilient Infrastructure',
            'Resilient Essential Services',
            'Knowledge, Skills, Behaviours for Resilience',
            'Resilient Housing'
        ],
        colors: ['#dc3545', '#fd7e14', '#20c997', '#6f42c1', '#0d6efd', '#6c757d'],
        plotOptions: {
            pie: {
                donut: {
                    size: '60%',
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'Resilient Index',
                            fontSize: '14px',
                            formatter: () => '1.5%'
                        }
                    }
                }
            }
        },
        legend: { position: 'right' },
        responsive: [{
            breakpoint: 768,
            options: {
                legend: { position: 'bottom' }
            }
        }]
    });

    charts.total.render();

    // Thematic Charts - Donut charts
    const themes = ['environmental', 'infrastructure', 'institutional', 'community'];
    const themeData = [
        { series: [40, 35, 25], labels: ['Quality Education', 'food security', 'health facilities'], colors: ['#34495e', '#e67e22', '#95a5a6'] },
        { series: [28, 42, 30], labels: ['Knowledge skills', 'Income + livelihood', 'market access'], colors: ['#8e44ad', '#d35400', '#27ae60'] },
        { series: [38, 32, 30], labels: ['Development of VDMP', 'Community camps', 'local governance'], colors: ['#2980b9', '#c0392b', '#16a085'] },
        { series: [33, 37, 30], labels: ['Access to EWS', 'Village awareness', 'training programs'], colors: ['#7f8c8d', '#f1c40f', '#e91e63'] }
    ];

    themes.forEach((theme, index) => {
        charts[theme] = new ApexCharts(document.querySelector(`#${theme}-chart`), {
            series: themeData[index].series,
            chart: {
                type: 'donut',
                height: 250,
                width: '100%',
                toolbar: {
                    show: true,   // Enable toolbar
                    tools: {
                        download: true, // Enable download
                        selection: false,
                        zoom: false,
                        zoomin: false,
                        zoomout: false,
                        pan: false,
                        reset: false,
                        customIcons: [] // You can add custom buttons here
                    }
                }
            },
            labels: themeData[index].labels,
            colors: themeData[index].colors,
            plotOptions: {
                pie: {
                    donut: {
                        size: '60%',
                        labels: {
                            show: true,
                            total: {
                                show: true,
                                label: 'Total Score',
                                fontSize: '12px',
                                formatter: () => '59%'
                            }
                        }
                    }
                }
            },
            legend: { position: 'bottom', fontSize: '12px' },
            responsive: [{
                breakpoint: 768,
                options: {
                    chart: { height: 200 },
                    legend: { fontSize: '10px' }
                }
            }]
        });
        charts[theme].render();
    });


    // Call once

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

        let url = '/api/dashboard_chart_data/';
        const query = params.toString();
        if (query) {
            url += `?${query}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API request failed with status: ${response.status}`);
        }

        const data = await response.json();
        renderResilienceCharts(data);
    } catch (error) {
        console.error("Error fetching chart data:", error);
    }
}

// Store chart instances
let chartInstances = {};

async function renderResilienceCharts(data) {
    try {
        const chartConfigs = [
            {
                elementId: "resiliant_housing-chart",
                dataKey: "resiliant_housing",
            },
            {
                elementId: "resiliant_infrastructure-chart",
                dataKey: "resiliant_infrastructure",
            }
        ];

        const res_colors = ['#00c59eff', '#29d875ff', '#5887a7ff', '#9b59b6', '#f1c40f'];
        const no_colors = ['#ff0000ff', '#ff8174ff', '#66312cff', '#d35400', '#95a5a6'];


        chartConfigs.forEach(config => {
            const categories = Object.keys(data[config.dataKey]);
            const resilient = categories.map(key => data[config.dataKey][key].resiliant);
            const noResilient = categories.map(key => data[config.dataKey][key].no_resiliant);
            const getRandomColor = (arr) => arr[Math.floor(Math.random() * arr.length)];

            const options = {
                chart: {
                    type: 'bar',
                    height: 350,
                    stacked: true,
                    toolbar: { show: true, tools: { download: true } }
                },
                plotOptions: { bar: { horizontal: false, columnWidth: '50%' } },
                series: [
                    { name: 'Resilient', data: resilient },
                    { name: 'Not Resilient', data: noResilient }
                ],
                xaxis: { categories: categories },
                yaxis: { title: { text: 'Percentage (%)' }, max: 100 },
                colors: [
                    getRandomColor(res_colors),
                    getRandomColor(no_colors)
                ],
                legend: { position: 'bottom' },
                tooltip: { y: { formatter: val => val + "%" } },
                title: { align: 'center' }
            };

            if (chartInstances[config.elementId]) {
                // Update existing chart instead of creating new one
                chartInstances[config.elementId].updateOptions(options);
                chartInstances[config.elementId].updateSeries(options.series);
            } else {
                // Create chart first time
                chartInstances[config.elementId] = new ApexCharts(
                    document.getElementById(config.elementId),
                    options
                );
                chartInstances[config.elementId].render();
            }
        });

    } catch (error) {
        console.error("Error rendering chart:", error);
    }
}


async function handleFilterChange() {
    const districtId = $('#district').val();
    const villageId = $('#village').val();
    const circle_id = $('#circle').val();
    const gram_panchayat_id = $('#gram_panchayat').val();
    await getChartData(districtId, circle_id, gram_panchayat_id, villageId);
}


function switchBaseMapSource(mapType) {
    if (!baseLayer) {
        console.error('Base layer not initialized');
        return;
    }

    let newSource;

    switch (mapType) {
        case 'osm':
            newSource = new ol.source.OSM({
                crossOrigin: 'anonymous'
            });
            baseLayer.setVisible(true);
            break;

        case 'satellite':
            newSource = new ol.source.XYZ({
                url: 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
                crossOrigin: 'anonymous'
            });
            baseLayer.setVisible(true);
            break;

        case 'terrain':
            newSource = new ol.source.XYZ({
                url: 'http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}&s=Ga',
                crossOrigin: 'anonymous'
            });
            baseLayer.setVisible(true);
            break;

        case 'blank':
            // For blank, hide the base layer instead of creating empty source
            baseLayer.setVisible(false);
            console.log('Base layer hidden for blank map');
            return; // Exit early, no need to set new source

        default:
            console.warn('Unknown map type:', mapType);
            return;
    }

    // Set the new source to the base layer
    baseLayer.setSource(newSource);

    console.log(`Base map switched to: ${mapType}`);
}
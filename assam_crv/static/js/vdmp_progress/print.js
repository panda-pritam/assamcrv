// print.js - VDMP Progress Page Print Functionality

// Function to print VDMP Progress page to PDF
async function printVDMPProgressToPDF() {
    try {
        // Show loading indicator
        showPrintLoading();
        
        // Capture the chart as image
        const chartImage = await captureChartAsImage();
        
        // Get the current filters for header
        const filters = getCurrentFilters();
        
        // Generate print content
        const printContent = generatePrintContent(chartImage, filters);
        
        // Create and trigger print
        createPrintWindow(printContent);
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('Error generating PDF. Please try again.');
    } finally {
        hidePrintLoading();
    }
}

// Show loading indicator
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

// Hide loading indicator
function hidePrintLoading() {
    const loading = document.getElementById('print-loading');
    if (loading) {
        loading.remove();
    }
}

// Capture ApexCharts chart as image
async function captureChartAsImage() {
    try {
        if (chartInstance) {
            // Use ApexCharts built-in method to get chart as base64 with horizontal layout
            const chartImage = await chartInstance.dataURI({
                format: 'png',
                width: 1400,  // Wider for horizontal layout
                height: 400,  // Reduced height for horizontal layout
                pixelRatio: 2 // Higher pixel ratio for crisp image
            });
            return chartImage.imgURI;
        } else {
            console.warn('Chart instance not found');
            return null;
        }
    } catch (error) {
        console.error('Error capturing chart:', error);
        // Fallback: try to capture using html2canvas if available
        try {
            const chartElement = document.getElementById('VDMP_progress_page_chart');
            if (chartElement && window.html2canvas) {
                const canvas = await html2canvas(chartElement, {
                    backgroundColor: '#ffffff',
                    scale: 3, // Higher scale for better quality
                    useCORS: true,
                    width: 1200,
                    height: 800
                });
                return canvas.toDataURL('image/png', 1.0); // Maximum quality
            }
        } catch (fallbackError) {
            console.error('Fallback capture failed:', fallbackError);
        }
        return null;
    }
}

// Get current filter values for display
function getCurrentFilters() {
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

// Generate complete print content
function generatePrintContent(chartImage, filters) {
    const currentDate = new Date().toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    const currentTime = new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
    });

    // Get summary text
    const summaryElement = document.querySelector('.summary-line span');
    const summaryText = summaryElement ? summaryElement.textContent : '';

    // Get the progress status table HTML
    const progressTable = getProgressStatusTableHTML();
    
    // Get the detailed progress table HTML
    const detailedTable = getDetailedProgressTableHTML();

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VDMP Progress Monitoring Report</title>
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
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    align-items: center;
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
                    .chart-section { page-break-inside: avoid; }
                    .table-container { page-break-inside: avoid; }
                    .section-title { page-break-after: avoid; }
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
                
                @page {
                    size: A4;
                    margin: 8mm;
                }
            </style>
        </head>
        <body>
            <div class="print-container">
                <!-- Header -->
                <div class="header">
                    <h1>VDMP Progress Monitoring Report</h1>
                    <div class="report-info">
                        <span><strong>Generated on:</strong> ${currentDate} at ${currentTime}</span>
                        <span><strong>Report Type:</strong> Progress Status Analysis</span>
                    </div>
                </div>
                
                <!-- Filters -->
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
                            <span class="filter-label">Activities:</span>
                            <span class="filter-value">${filters.activities}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Summary -->
                ${summaryText ? `
                <div class="summary-section">
                    <p><i class="fas fa-info-circle"></i> ${summaryText}</p>
                </div>
                ` : ''}
                
                <!-- Chart Section -->
                <div class="chart-section">
                    <div class="chart-title">VDMP Activity Progress Status</div>
                    <div class="chart-container">
                        ${chartImage ? 
                            `<img src="${chartImage}" alt="VDMP Progress Chart" class="chart-image" />` : 
                            `<div class="no-chart">Chart not available for printing</div>`
                        }
                    </div>
                </div>
                
                <!-- Progress Status Table -->
                <div class="section-title">VDMP Progress Status Summary</div>
                <div class="table-container">
                    <div class="table-header">
                        <span>Progress Status Overview</span>
                        <div class="legend">
                            <div class="legend-item">
                                <div class="legend-color notstarted"></div>
                                <span>Not Started</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color completed"></div>
                                <span>Completed</span>
                            </div>
                        </div>
                    </div>
                    ${progressTable}
                </div>
                
                
                
               
            </div>
        </body>
        </html>
    `;
}

// Get progress status table HTML
function getProgressStatusTableHTML() {
    const table = document.getElementById('VDMP_progress_table');
    if (!table) return '<p>Table not available</p>';
    
    const clonedTable = table.cloneNode(true);
    
    // Clean up classes for print
    const rows = clonedTable.querySelectorAll('tr');
    rows.forEach(row => {
        row.classList.remove('odd', 'even');
        const cells = row.querySelectorAll('td, th');
        cells.forEach(cell => {
            // Keep important classes, remove others
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

// Get detailed progress table HTML
function getDetailedProgressTableHTML() {
    const table = document.getElementById('vdmp_detailed_progress_table');
    if (!table) return '<p>Detailed table not available</p>';
    
    const clonedTable = table.cloneNode(true);
    
    // Remove DataTables classes and clean up
    clonedTable.classList.remove('dataTable', 'no-footer');
    clonedTable.removeAttribute('aria-describedby');
    clonedTable.removeAttribute('role');
    
    // Clean up rows
    const rows = clonedTable.querySelectorAll('tr');
    rows.forEach((row, index) => {
        row.classList.remove('odd', 'even');
        const cells = row.querySelectorAll('td, th');
        cells.forEach(cell => {
            cell.classList.remove('sorting_1');
            // Keep text alignment classes
            if (!cell.classList.contains('text-center') && !cell.classList.contains('text-left')) {
                if (index === 0) cell.classList.add('text-center'); // Header
                else if (cell.cellIndex === 0) cell.classList.add('text-center'); // S.No column
                else cell.classList.add('text-left'); // Other columns
            }
        });
    });
    
    return clonedTable.outerHTML;
}

// Create and open print window
function createPrintWindow(htmlContent) {
    const printWindow = window.open('', '_blank', 'scrollbars=yes,resizable=yes');
    
    if (!printWindow) {
        alert('Please allow popups for this website to enable printing.');
        return;
    }
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    // Wait for content to load, then print
    printWindow.onload = function() {
        setTimeout(() => {
            printWindow.focus();
            printWindow.print();
            
            // Close the window after printing (optional)
            setTimeout(() => {
                printWindow.close();
            }, 1000);
        }, 500);
    };
}

// Alternative function for direct browser print (without popup)
function printDirectly() {
    const originalContent = document.body.innerHTML;
    const printContent = document.querySelector('.container-fluid').cloneNode(true);
    
    // Hide non-printable elements
    const elementsToHide = [
        '.breadcrump__wrapper',
        '.printCss',
        'button',
        '.dropdown-toggle'
    ];
    
    elementsToHide.forEach(selector => {
        const elements = printContent.querySelectorAll(selector);
        elements.forEach(el => el.style.display = 'none');
    });
    
    document.body.innerHTML = printContent.innerHTML;
    window.print();
    document.body.innerHTML = originalContent;
    
    // Reinitialize the page after printing
    location.reload();
}

// Export functions for global use
window.printVDMPProgressToPDF = printVDMPProgressToPDF;
window.printDirectly = printDirectly;
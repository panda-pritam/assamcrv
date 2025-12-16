/**
 * VDMP Dashboard Print to PDF Functionality - Tabular Format
 */

function printDashboardToPDF() {
    // Store original accordion states
    const accordionItems = document.querySelectorAll('.accordion-collapse');
    const originalStates = [];
    
    try {
        // Expand all accordions
        accordionItems.forEach((item, index) => {
            originalStates[index] = item.classList.contains('show');
            item.classList.add('show');
        });
        
        // Create print content with tabular format
        const printContent = createPrintContent();
        
        // Open print window
        const printWindow = window.open('', '_blank', 'scrollbars=yes,resizable=yes');
        
        if (!printWindow) {
            alert('Please allow popups for this website to enable printing.');
            return;
        }
        
        printWindow.document.write(printContent);
        printWindow.document.close();
        
        printWindow.onload = function() {
            setTimeout(() => {
                printWindow.focus();
                printWindow.print();
                
                setTimeout(() => {
                    printWindow.close();
                }, 1000);
            }, 500);
        };
        
    } finally {
        // Restore original states
        setTimeout(() => {
            accordionItems.forEach((item, index) => {
                if (!originalStates[index]) {
                    item.classList.remove('show');
                }
            });
        }, 1000);
    }
}

function extractDashboardData() {
    return {
        // Demographics
        male_population: document.getElementById('male_population')?.textContent || '0',
        female_population: document.getElementById('female_population')?.textContent || '0',
        total_population: document.getElementById('total_population')?.textContent || '0',
        total_households: document.getElementById('total_households')?.textContent || '0',
        
        // Vulnerable Populations
        priority_households: document.getElementById('priority_households')?.textContent || '0',
        bpl_households: document.getElementById('bpl_households')?.textContent || '0',
        population_bl_six: document.getElementById('population_bl_six')?.textContent || '0',
        senior_citizens: document.getElementById('senior_citizens')?.textContent || '0',
        pregnant_lactating: document.getElementById('pregnant_lactating')?.textContent || '0',
        total_disabled: document.getElementById('total_disabled')?.textContent || '0',
        
        // Assets
        total_road_length: document.getElementById('total_road_length')?.textContent || '0 km',
        big_cattles_asset: document.getElementById('big_cattles_asset')?.textContent || '0',
        small_cattles_asset: document.getElementById('small_cattles_asset')?.textContent || '0',
        kachcha_houses_asset: document.getElementById('kachcha_houses_asset')?.textContent || '0',
        semi_pucca_houses_asset: document.getElementById('semi_pucca_houses_asset')?.textContent || '0',
        pucca_houses_asset: document.getElementById('pucca_houses_asset')?.textContent || '0',
        anganwadi_asset: document.getElementById('anganwadi_asset')?.textContent || '0',
        school_asset: document.getElementById('school_asset')?.textContent || '0',
        religous_places_asset: document.getElementById('religous_places_asset')?.textContent || '0',
        
        // Hazards
        avg_flood_depth: document.getElementById('avg_flood_depth')?.textContent || '0 feet',
        max_flood_depth: document.getElementById('max_flood_depth')?.textContent || '0 feet',
        
        // Vulnerability
        flood_vulnerable_houses: document.getElementById('flood_vulnerable_houses')?.textContent || '0',
        erosion_vulnerable_houses: document.getElementById('erosion_vulnerable_houses')?.textContent || '0',
        flood_vulnerable_roads: document.getElementById('flood_vulnerable_roads')?.textContent || '0',
        erosion_vulnerable_roads: document.getElementById('erosion_vulnerable_roads')?.textContent || '0'
    };
}

function createTabularContent(data) {
    return `
        <div class="section">
            <div class="section-title">1. Demographic Summary</div>
            <table>
                <tr><th colspan="2" class="subsection-header">Population</th></tr>
                <tr><td>Male Population</td><td>${data.male_population}</td></tr>
                <tr><td>Female Population</td><td>${data.female_population}</td></tr>
                <tr><td>Total Population</td><td>${data.total_population}</td></tr>
                <tr><td>Total Households</td><td>${data.total_households}</td></tr>
                <tr><th colspan="2" class="subsection-header">Vulnerable Populations</th></tr>
                <tr><td>Priority Households</td><td>${data.priority_households}</td></tr>
                <tr><td>BPL Households</td><td>${data.bpl_households}</td></tr>
                <tr><td>Children (Age < 6)</td><td>${data.population_bl_six}</td></tr>
                <tr><td>Senior Citizens</td><td>${data.senior_citizens}</td></tr>
                <tr><td>Pregnant/Lactating Women</td><td>${data.pregnant_lactating}</td></tr>
                <tr><td>Physically Challenged</td><td>${data.total_disabled}</td></tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title" >2. Asset Summary</div>
            <table>
                <tr><th colspan="2" class="subsection-header">Infrastructure</th></tr>
                <tr><td>Total Road Length</td><td>${data.total_road_length}</td></tr>
                <tr><th colspan="2" class="subsection-header">Health Facilities</th></tr>
                <tr><td>PHC/CHC</td><td>-</td></tr>
                <tr><td>Other Health Facilities</td><td>-</td></tr>
                <tr><th colspan="2" class="subsection-header">Livestock</th></tr>
                <tr><td>Big Cattle</td><td>${data.big_cattles_asset}</td></tr>
                <tr><td>Small Cattle</td><td>${data.small_cattles_asset}</td></tr>
                <tr><th colspan="2" class="subsection-header">Housing</th></tr>
                <tr><td>Kachcha Houses</td><td>${data.kachcha_houses_asset}</td></tr>
                <tr><td>Semi Pucca Houses</td><td>${data.semi_pucca_houses_asset}</td></tr>
                <tr><td>Pucca Houses</td><td>${data.pucca_houses_asset}</td></tr>
                <tr><th colspan="2" class="subsection-header">Educational Facilities</th></tr>
                <tr><td>Anganwadi Centers</td><td>${data.anganwadi_asset}</td></tr>
                <tr><td>Schools</td><td>${data.school_asset}</td></tr>
                <tr><td>Religious Places</td><td>${data.religous_places_asset}</td></tr>
                <tr><th colspan="2" class="subsection-header">Other Assets</th></tr>
                
            </table>
        </div>

        <div class="section">
            <div class="section-title" >3. Hazard & Vulnerability</div>
            <table>
                <tr><th colspan="2" class="subsection-header">Hazard Summary</th></tr>
                <tr><td>Average Flood Depth</td><td>${data.avg_flood_depth}</td></tr>
                <tr><td>Maximum Flood Depth</td><td>${data.max_flood_depth}</td></tr>
                <tr><td>Bank Erosion</td><td>-</td></tr>
                <tr><td>Landslide</td><td>-</td></tr>
                <tr><th colspan="2" class="subsection-header">Vulnerable Assets</th></tr>
                <tr><td>Flood Vulnerable Houses</td><td>${data.flood_vulnerable_houses}</td></tr>
                <tr><td>Erosion Vulnerable Houses</td><td>${data.erosion_vulnerable_houses}</td></tr>
                <tr><td>Flood Vulnerable Roads</td><td>${data.flood_vulnerable_roads}</td></tr>
                <tr><td>Erosion Vulnerable Roads</td><td>${data.erosion_vulnerable_roads}</td></tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">4. Flood Shelter</div>
            <table>
                <tr><th>Shelter Type</th><th>Details</th></tr>
                <tr><td>LP School, Rupakuchi</td><td>For moderate flood</td></tr>
                <tr><td>Elevated Platforms</td><td>For Livestocks</td></tr>
            </table>
        </div>
    `;
}

function createPrintContent() {
    // Get summary text
    const summaryLine = document.querySelector('.summary-line span');
    const summaryText = summaryLine ? summaryLine.textContent : '';
    
    // Extract data
    const data = extractDashboardData();
    
    const currentDate = new Date().toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    const currentTime = new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Village Summary Dashboard</title>
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
                padding: 15mm;
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
            
            .section {
                margin-bottom: 25px;
                page-break-inside: avoid;
            }
            
            td:nth-child(2) {
                text-align: right;
            }
            

            .section-title {
                font-size: 16px;
                font-weight: bold;
                margin: 25px 0 15px 0;
                color: #245FAE;
                border-bottom: 2px solid #245FAE;
                padding-bottom: 5px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
                border: 1px solid #dee2e6;
                
                overflow: hidden;
            }
            
            th, td {
                border: 1px solid #dee2e6;
                padding: 8px;
                text-align: left;
            }
            
            th {
                background-color: #f8f9fa;
                font-weight: bold;
                color: #495057;
            }
            
            .subsection-header {
                background-color: #245FAE !important;
                color: white !important;
                font-weight: bold !important;
                text-align: center !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            tbody tr:nth-child(even) {
                background-color: #f8f9fa;
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
                .print-container { margin: 0; padding: 10mm; }
                .section { page-break-inside: avoid; }
                .section-title { page-break-after: avoid; }
                .subsection-header {
                    background-color: #245FAE !important;
                    color: white !important;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
            }
            
            @page {
                size: A4;
                margin: 10mm;
            }
        </style>
    </head>
    <body>
        <div class="print-container">
            <!-- Header -->
            <div class="header">
                <h1>Village Summary Dashboard</h1>
                <div class="report-info">
                    <span><strong>Generated on:</strong> ${currentDate} at ${currentTime}</span>
                    <span><strong>Report Type:</strong> Village Dashboard Summary</span>
                </div>
            </div>
            
            <!-- Summary -->
            ${summaryText ? `
            <div class="summary-section">
                <p><i class="fas fa-info-circle"></i> ${summaryText}</p>
            </div>
            ` : ''}
            
            ${createTabularContent(data)}
            
            <!-- Footer -->
             <!-- <div class="footer">
                <p><strong>Village Dashboard Management System</strong> | Generated automatically | Page 1 of 1</p>
                <p>This report contains confidential information. Please handle accordingly.</p>
            </div> -->
        </div>
    </body>
    </html>
    `;
}

// Initialize print functionality
document.addEventListener('DOMContentLoaded', function() {
    const printButton = document.getElementById('printDashboardBtn');
    if (printButton) {
        printButton.addEventListener('click', function(e) {
            e.preventDefault();
            printDashboardToPDF();
        });
    }
});



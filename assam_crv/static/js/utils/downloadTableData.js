/**
 * Utility functions for downloading DataTable data as CSV
 */

/**
 * Download DataTable data as CSV
 * @param {string} tableId - The ID of the DataTable
 * @param {string} filename - The filename for the CSV (without extension)
 * @param {boolean} excludeActions - Whether to exclude Actions column from export
 */
function downloadTableAsCSV(tableId, filename = 'table_data', excludeActions = true) {
    try {
        // Check if DataTable exists
        if (!$.fn.DataTable.isDataTable('#' + tableId)) {
            console.error('DataTable not found:', tableId);
            return;
        }

        const table = $('#' + tableId).DataTable();
        
        // Get all data (not just visible rows)
        const data = table.rows({ search: 'applied' }).data().toArray();
        const headers = [];
        
        // Get headers from table
        $('#' + tableId + ' thead th').each(function(index) {
            const headerText = $(this).text().trim();
            
            // Skip Actions column if excludeActions is true
            if (excludeActions && headerText.toLowerCase().includes('action')) {
                return;
            }
            
            headers.push(headerText);
        });
        
        // Prepare CSV content
        let csvContent = '';
        
        // Add headers
        csvContent += headers.join(',') + '\n';
        
        // Add data rows
        data.forEach(row => {
            const filteredRow = [];
            
            row.forEach((cell, index) => {
                // Skip Actions column if excludeActions is true
                const headerText = $('#' + tableId + ' thead th').eq(index).text().trim();
                if (excludeActions && headerText.toLowerCase().includes('action')) {
                    return;
                }
                
                // Clean cell data (remove HTML tags and escape commas)
                let cleanCell = typeof cell === 'string' ? cell.replace(/<[^>]*>/g, '') : cell;
                cleanCell = String(cleanCell).replace(/"/g, '""'); // Escape quotes
                
                // Wrap in quotes if contains comma or quotes
                if (String(cleanCell).includes(',') || String(cleanCell).includes('"')) {
                    cleanCell = '"' + cleanCell + '"';
                }
                
                filteredRow.push(cleanCell);
            });
            
            csvContent += filteredRow.join(',') + '\n';
        });
        
        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename + '.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('CSV downloaded successfully:', filename + '.csv');
        } else {
            console.error('Browser does not support file download');
        }
        
    } catch (error) {
        console.error('Error downloading CSV:', error);
    }
}

/**
 * Download table data with custom data array
 * @param {Array} data - Array of data objects
 * @param {Array} headers - Array of header strings
 * @param {string} filename - The filename for the CSV
 */
function downloadCustomDataAsCSV(data, headers, filename = 'data') {
    try {
        let csvContent = '';
        
        // Add headers
        csvContent += headers.join(',') + '\n';
        
        // Add data rows
        data.forEach(row => {
            const csvRow = headers.map(header => {
                let cell = row[header] || '';
                
                // Clean cell data
                cell = String(cell).replace(/"/g, '""');
                
                // Wrap in quotes if contains comma or quotes
                if (String(cell).includes(',') || String(cell).includes('"')) {
                    cell = '"' + cell + '"';
                }
                
                return cell;
            });
            
            csvContent += csvRow.join(',') + '\n';
        });
        
        // Create and download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename + '.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
    } catch (error) {
        console.error('Error downloading custom CSV:', error);
    }
}
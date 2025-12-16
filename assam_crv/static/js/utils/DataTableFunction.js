/**
 * Common DataTable utility functions for consistent table initialization and data population
 */

/**
 * Initialize a DataTable with common configuration
 * @param {string} tableId - The ID of the table element
 * @param {Array} columns - Array of column configuration objects with translated titles
 * @param {Object} options - Optional additional DataTable options
 * @param {boolean} includeActions - Whether to include actions column with edit/delete buttons
 * @returns {Object} DataTable instance
 * 
 * Note: Pass translated column titles from Django template like:
 * const columns = [
 *     { title: "{{ 'S. No.'|trans }}", width: "5%" },
 *     { title: "{{ 'District'|trans }}" }
 * ];
 */
function initializeDataTable(tableId, columns, options = {}, includeActions = false) {
    // Check if table already has a thead element
    const hasExistingHeader = $('#' + tableId + ' thead').length > 0;

    // console.log(tableId,columns,options)

    const defaultConfig = {
        responsive: true,
        scrollX: true,
        pageLength: 10,
        lengthMenu: [[10, 15, 25, 50, -1], [10, 15, 25, 50, "All"]],

        // fixedHeader: true,
        // scrollY: '400px'
        // 
        

        // Prevent DataTables from creating a duplicate thead if one already exists
        headerCallback: function(thead, data, start, end, display) {
            // If we have two thead elements, remove the empty one
            const theadElements = $('#' + tableId + ' thead');
            if (theadElements.length > 1) {
                // Find the empty thead and remove it
                theadElements.each(function() {
                    if ($(this).children().length == 0) {
                        $(this).remove();
                    }
                });
            }
        },
        
        // Apply consistent styling after each draw
        drawCallback: function () {
            $('#' + tableId + ' tbody td').css({
                'font-size': '14px',
                'color': '#000000',
                'text-align': 'left',
            });
       

            // Center align first column (Sr. No.)
            $('#' + tableId + ' tbody td:first-child').css({
                'text-align': 'right'
            });

            $('.dataTables_wrapper .dataTables_length').css({
                'margin-bottom': '15px'
            });

            $('.dataTables_wrapper .row:first-child').css({
                'margin-bottom': '20px'
            });
            


        },

        // Consistent language settings
        language: {
            search: "Search:",
            lengthMenu: "Show _MENU_ entries",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "No entries found",
            infoFiltered: "(filtered from _MAX_ total entries)",
            paginate: {
                first: "First",
                last: "Last",
                next: "Next",
                previous: "Previous"
            }
        },
        columns: columns, // Disable auto-generated headers
        order: [[0, 'asc']],
        columnDefs: [
            {
                targets: 0,
                orderable: false // First column (S.No) not sortable
            },
            // Apply column widths from columns array
            ...columns.map((col, index) => ({
                targets: index,
                width: col.width || null
            })).filter(def => def.width !== null),
            // Actions column configuration if included
            ...(includeActions ? [{
                targets: -1, // Last column (Actions)
                orderable: false,
                searchable: false,
                width: "150px"
            }] : [])
        ]
    };

    // Merge with custom options
    const config = { ...defaultConfig, ...options };
    return $('#' + tableId).DataTable(config);
}

/**
 * Populate DataTable with data using a custom row mapper function
 * @param {Object} dataTable - DataTable instance
 * @param {Array} data - Array of data objects
 * @param {Function} rowMapper - Function to map data item to table row array
 * @param {boolean} includeActions - Whether to include actions column
 * @param {Function} actionsMapper - Function to generate actions HTML for each row
 */
function populateDataTable(dataTable, data, rowMapper, includeActions = false, actionsMapper = null) {
    // console.log(dataTable, data, rowMapper, includeActions, actionsMapper)
    // Clear existing data
    dataTable.clear();

    // Add new rows using the mapper function
    data.forEach((item, index) => {
        let row = rowMapper(item, index);
        if (includeActions && actionsMapper) {
            row.push(actionsMapper(item, index));
        }
        dataTable.row.add(row);
    });

    // Redraw the table
    dataTable.draw();
}

/**
 * Generate standard edit/delete action buttons HTML
 * @param {number} id - Record ID
 * @param {Function} editCallback - Edit function name
 * @param {Function} deleteCallback - Delete function name
 * @returns {string} HTML string for action buttons
 */

//onmouseover="this.style.background='#245FAE';
//onmouseover="this.style.background='#dc3545';
 //onmouseout="this.style.background='white'; this.style.color='#245FAE';" 
function generateActionButtons(id, editCallback, deleteCallback) {
    return `
        <button   class='table_edit_Btn'
                 this.style.color='white';" 
               
                onclick="${editCallback}(${id})">
            <i class="fa-solid fa-pen-to-square"></i>
        </button>
        <button type="button" class='table_Delete_Btn' 
                 this.style.color='white';" 
                onmouseout="this.style.background='white'; this.style.color='#dc3545';" 
                onclick="${deleteCallback}(${id})">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;
}

/**
 * Manually adjust specific DataTable columns
 * @param {string} tableId - The ID of the table element
 */
function adjustDataTableColumns(tableId) {
    setTimeout(() => {
        try {
            // Check if table element exists
            if ($('#' + tableId).length === 0) {
                console.warn('Table element not found:', tableId);
                return;
            }

            // Check if DataTable is initialized
            if (!$.fn.DataTable.isDataTable('#' + tableId)) {
                console.warn('DataTable not initialized for:', tableId);
                return;
            }

            const table = $('#' + tableId).DataTable();

            // Force table container to be visible and recalculate
            const $tableContainer = $('#' + tableId).closest('.dataTables_wrapper');
            if ($tableContainer.is(':visible')) {
                table.columns.adjust();
                table.responsive.recalc();
                table.draw(false);
                console.log('Adjusted columns for table:', tableId);
            } else {
                console.warn('Table container is not visible:', tableId);
            }
        } catch (error) {
            console.error('Error adjusting table columns:', error);
        }
    }, 100);
}

/**
 * Adjust all DataTables when sidebar toggles
 */
function adjustAllDataTables() {
    $.fn.dataTable.tables({ visible: true, api: true }).columns.adjust();
}
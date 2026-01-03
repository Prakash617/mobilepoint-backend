document.addEventListener('DOMContentLoaded', function () {
    
    function setupRow(row) {
        const typeSelect = row.querySelector('select[name$="-types"]');
        if (!typeSelect) return;

        const valueCell = row.querySelector('td.field-value');
        const colorCell = row.querySelector('td.field-color_code');
        const imageCell = row.querySelector('td.field-image');

        console.log('Setup row:', row.id, {valueCell, colorCell, imageCell});

        function toggle() {
            const type = typeSelect.value;
            
            console.log('Toggle called with type:', type, 'Row:', row.id);

            // Hide all cells first
            if (valueCell) {
                valueCell.style.display = 'none';
                console.log('Hidden value cell');
            }
            if (colorCell) {
                colorCell.style.display = 'none';
                console.log('Hidden color cell');
            }
            if (imageCell) {
                imageCell.style.display = 'none';
                console.log('Hidden image cell');
            }

            // Show the relevant cell based on type
            if (type === 'text') {
                if (valueCell) {
                    valueCell.style.display = 'table-cell';
                    console.log('Showing value cell for text');
                }
            } else if (type === 'color') {
                if (colorCell) {
                    colorCell.style.display = 'table-cell';
                    console.log('Showing color cell for color');
                }
            } else if (type === 'image') {
                if (imageCell) {
                    imageCell.style.display = 'table-cell';
                    console.log('Showing image cell for image');
                }
            }
        }

        // Initial toggle
        toggle();

        // Listen to native change event
        typeSelect.addEventListener('change', function(e) {
            console.log('Native change event fired, value:', typeSelect.value);
            toggle();
        });

        // Listen to Select2 change events
        if (window.$ && window.$.fn.select2) {
            $(typeSelect).on('select2:select', function(e) {
                console.log('Select2 change event fired, value:', typeSelect.value);
                setTimeout(toggle, 50);
            });
            
            $(typeSelect).on('select2:unselect', function(e) {
                console.log('Select2 unselect event fired, value:', typeSelect.value);
                setTimeout(toggle, 50);
            });
        }
    }

    function initAll() {
        console.log('Initializing all rows');
        const rows = document.querySelectorAll('tr.form-row.dynamic-values, tr.form-row.has_original.dynamic-values');
        console.log('Found rows:', rows.length);
        rows.forEach(setupRow);
    }

    // Wait for Select2 to be initialized, then init rows
    function waitForSelect2AndInit() {
        const tableContainer = document.querySelector('fieldset[data-select2-id]');
        if (tableContainer && window.$) {
            // Check if Select2 is initialized
            const select2Elements = tableContainer.querySelectorAll('.select2-container');
            if (select2Elements.length > 0) {
                console.log('Select2 initialized, setting up rows');
                initAll();
            } else {
                console.log('Select2 not ready yet, waiting...');
                setTimeout(waitForSelect2AndInit, 100);
            }
        } else {
            console.log('Fallback: initializing without waiting for Select2');
            initAll();
        }
    }

    // Initial setup with delay to ensure DOM is ready
    setTimeout(waitForSelect2AndInit, 300);

    // Setup mutation observer for new rows added to the table
    const tableContainer = document.querySelector('fieldset[data-select2-id]');
    if (tableContainer) {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'TR' && node.classList.contains('dynamic-values')) {
                            console.log('New row detected:', node.id);
                            setTimeout(() => setupRow(node), 100);
                        }
                    }
                });
            });
        });

        // Observe the tbody for new rows
        const tbody = tableContainer.querySelector('tbody');
        if (tbody) {
            observer.observe(tbody, {
                childList: true
            });
            console.log('Observing tbody for new rows');
        }
    }

    // Fallback: Handle "Add another" button clicks
    document.body.addEventListener('click', function (e) {
        const addBtn = e.target.closest('.add-row a, .addlink');
        if (addBtn) {
            console.log('Add button clicked');
            setTimeout(function () {
                initAll();
            }, 200);
        }
    });

});

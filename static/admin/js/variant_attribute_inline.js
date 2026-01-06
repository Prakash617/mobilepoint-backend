document.addEventListener('DOMContentLoaded', function () {

    function setupRow(row) {
        const typeSelect = row.querySelector('select[name$="-types"]');
        if (!typeSelect) return;

        const valueCell = row.querySelector('td.field-value');
        const colorCell = row.querySelector('td.field-color_code');
        const imageCell = row.querySelector('td.field-image');

        const table = row.closest('table');
        const thValue = table.querySelector('th.column-value');
        const thColor = table.querySelector('th.column-color_code');
        const thImage = table.querySelector('th.column-image');

        function toggle() {
            const type = typeSelect.value;

            // Hide all cells first
            if (valueCell) valueCell.style.display = 'none';
            if (colorCell) colorCell.style.display = 'none';
            if (imageCell) imageCell.style.display = 'none';

            // Hide all headers first
            thValue.style.display = 'none';
            thColor.style.display = 'none';
            thImage.style.display = 'none';

            // Show only relevant cell and header
            if (type === 'text') {
                if (valueCell) valueCell.style.display = 'table-cell';
                if (thValue) thValue.style.display = 'table-cell';
            } else if (type === 'color') {
                if (colorCell) colorCell.style.display = 'table-cell';
                if (thColor) thColor.style.display = 'table-cell';
            } else if (type === 'image') {
                if (imageCell) imageCell.style.display = 'table-cell';
                if (thImage) thImage.style.display = 'table-cell';
            }
        }

        // Initial toggle
        toggle();

        // Native change event
        typeSelect.addEventListener('change', toggle);

        // Select2 events
        if (window.$ && window.$.fn.select2) {
            $(typeSelect).on('select2:select select2:unselect', function () {
                setTimeout(toggle, 50);
            });
        }
    }

    function initAll() {
        const rows = document.querySelectorAll('tr.form-row.dynamic-values, tr.form-row.has_original.dynamic-values');
        rows.forEach(setupRow);
    }

    function waitForSelect2AndInit() {
        const tableContainer = document.querySelector('fieldset[data-select2-id]');
        if (tableContainer && window.$) {
            const select2Elements = tableContainer.querySelectorAll('.select2-container');
            if (select2Elements.length > 0) {
                initAll();
            } else {
                setTimeout(waitForSelect2AndInit, 100);
            }
        } else {
            initAll();
        }
    }

    setTimeout(waitForSelect2AndInit, 300);

    // Mutation observer for new rows
    const tableContainer = document.querySelector('fieldset[data-select2-id]');
    if (tableContainer) {
        const tbody = tableContainer.querySelector('tbody');
        if (tbody) {
            const observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (mutation) {
                    mutation.addedNodes.forEach(function (node) {
                        if (node.nodeType === 1 && node.tagName === 'TR' && node.classList.contains('dynamic-values')) {
                            setTimeout(() => setupRow(node), 100);
                        }
                    });
                });
            });
            observer.observe(tbody, { childList: true });
        }
    }

    // Add another button
    document.body.addEventListener('click', function (e) {
        const addBtn = e.target.closest('.add-row a, .addlink');
        if (addBtn) {
            setTimeout(initAll, 200);
        }
    });

});

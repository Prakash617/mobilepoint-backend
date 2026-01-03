document.addEventListener('DOMContentLoaded', function() {
    var typeField = document.getElementById('id_types') || document.querySelector('select[name="types"]');
    var valueRow = document.querySelector('.field-value');
    var colorCodeRow = document.querySelector('.field-color_code');
    var imageRow = document.querySelector('.field-image');

    function toggleFields() {
        if (!typeField) return;

        var selectedType = typeField.value;

        // Hide all rows
        if (valueRow) valueRow.style.display = 'none';
        if (colorCodeRow) colorCodeRow.style.display = 'none';
        if (imageRow) imageRow.style.display = 'none';

        // Show only the relevant row
        if (selectedType === 'text' && valueRow) valueRow.style.display = '';
        if (selectedType === 'color' && colorCodeRow) colorCodeRow.style.display = '';
        if (selectedType === 'image' && imageRow) imageRow.style.display = '';
    }

    // Initial call
    toggleFields();

    // Listen for Select2 change
    if (typeField && typeof $ !== 'undefined') {
        $(typeField).on('change', toggleFields);
    } else if (typeField) {
        // fallback for normal select
        typeField.addEventListener('change', toggleFields);
    }

    // Optional: red borders to confirm JS runs
    // if (colorCodeRow) colorCodeRow.style.border = '2px solid blue';
});

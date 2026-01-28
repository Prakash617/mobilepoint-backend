(function() {
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        // Find the status field
        const statusField = document.querySelector('.field-status');
        if (!statusField) return;
        
        const radioButtons = statusField.querySelectorAll('input[type="radio"]');
        const labels = statusField.querySelectorAll('label');
        
        // Add click handlers to make the entire label clickable
        labels.forEach(label => {
            label.style.cursor = 'pointer';
            label.addEventListener('click', function(e) {
                const radio = this.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    // Trigger change event
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        });
        
        // Add visual feedback on selection
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                // Remove all active classes
                labels.forEach(label => {
                    label.classList.remove('active');
                });
                // Add active class to checked label
                if (this.checked && this.parentElement) {
                    this.parentElement.classList.add('active');
                }
            });
        });
        
        // Initialize checked states
        radioButtons.forEach(radio => {
            if (radio.checked && radio.parentElement) {
                radio.parentElement.classList.add('active');
            }
        });
    });
})();

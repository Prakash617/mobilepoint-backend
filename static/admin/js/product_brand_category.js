(function() {
    'use strict';

    function initializeCategoryFilter() {
        const brandSelect = document.getElementById('id_brand');
        const categorySelect = document.getElementById('id_category');

        if (!brandSelect || !categorySelect) {
            console.warn('Brand or Category field not found on this page');
            return false;
        }

        console.log('Initializing category filter...');

        function updateCategories(brandId) {
            console.log('Updating categories for brand ID:', brandId);

            // Clear categories
            categorySelect.innerHTML = '<option value="">---------</option>';

            if (!brandId) {
                // Refresh Select2 if available
                if (window.$ && categorySelect.classList.contains('select2-hidden-accessible')) {
                    setTimeout(function() {
                        $(categorySelect).trigger('change.select2');
                    }, 100);
                }
                return;
            }

            // Fetch categories for the selected brand
            fetch(`/admin/product/filter-categories/?brand_id=${brandId}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Categories received:', data);

                    // Store current selection
                    const currentValue = categorySelect.value;

                    // Add blank option
                    categorySelect.innerHTML = '<option value="">---------</option>';

                    // Add categories
                    if (data.categories && Array.isArray(data.categories)) {
                        data.categories.forEach(category => {
                            const option = document.createElement('option');
                            option.value = category.id;
                            option.textContent = category.name;
                            categorySelect.appendChild(option);
                        });
                    }

                    // Restore previous selection if it exists
                    if (currentValue) {
                        const optionExists = Array.from(categorySelect.options).some(
                            opt => opt.value === currentValue
                        );
                        if (optionExists) {
                            categorySelect.value = currentValue;
                        }
                    }

                    // Refresh Select2
                    if (window.$ && categorySelect.classList.contains('select2-hidden-accessible')) {
                        setTimeout(function() {
                            $(categorySelect).trigger('change.select2');
                        }, 50);
                    }

                    console.log('Categories updated successfully');
                })
                .catch(error => {
                    console.error('Error fetching categories:', error);
                });
        }

        // Initial population if brand is already selected
        const initialBrandId = brandSelect.value;
        if (initialBrandId) {
            console.log('Initial brand ID found:', initialBrandId);
            setTimeout(function() {
                updateCategories(initialBrandId);
            }, 500);
        }

        // Listen to Select2 change events
        if (window.$ && $.fn.select2) {
            $(brandSelect).on('select2:select', function(e) {
                console.log('Select2 select event fired:', this.value);
                updateCategories(this.value);
            });

            $(brandSelect).on('select2:clear', function(e) {
                console.log('Select2 clear event fired');
                updateCategories('');
            });

            $(brandSelect).on('change', function(e) {
                if (!e.originalEvent || !e.originalEvent.isTrusted) {
                    // Programmatic change
                    console.log('Programmatic brand change:', this.value);
                    updateCategories(this.value);
                }
            });
        } else {
            // Fallback for non-Select2 fields
            console.warn('Select2 not available, using standard change listener');
            brandSelect.addEventListener('change', function() {
                console.log('Standard change event:', this.value);
                updateCategories(this.value);
            });
        }

        return true;
    }

    // Initialize when DOM is ready
    function tryInit() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeCategoryFilter);
        } else {
            // DOM is already loaded
            initializeCategoryFilter();
        }
    }

    // Also try initialization after a small delay to ensure all JS is loaded
    if (document.readyState === 'complete') {
        setTimeout(initializeCategoryFilter, 100);
    } else {
        tryInit();
    }
})();

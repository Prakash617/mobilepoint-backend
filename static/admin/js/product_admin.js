// document.addEventListener("DOMContentLoaded", function () {
//   const categoryField = document.getElementById("id_category");
//   const brandField = document.getElementById("id_brand");

//   if (!categoryField || !brandField) return;
//   console.log("Product admin JS loaded.");
//   categoryField.addEventListener("change", function () {
//     console.log("Category changed:", this.value);
//     const categoryId = this.value;

//     // Reset Select2
//     if ($(brandField).data('select2')) {
//       $(brandField).empty().trigger('change');
//     } else {
//       brandField.innerHTML = '<option value="">-----hell me----</option>';
//     }

//     if (!categoryId) return;

//     fetch(`/admin/product/product/get-brands/?category_id=${categoryId}`, {
//       headers: {
//         "X-Requested-With": "XMLHttpRequest",
//       },
//     })
//       .then((response) => {
//         if (!response.ok) throw new Error("Network response was not ok");
//         return response.json();
//       })
//       .then((data) => {
//         if (data.length === 0) return;

//         data.forEach((brand) => {
//           const option = document.createElement("option");
//           option.value = brand.id;
//           option.textContent = brand.name;
//           brandField.appendChild(option);
//         });

//         // If Select2 is enabled, trigger change so it updates visually
//         if ($(brandField).data('select2')) {
//           $(brandField).trigger('change');
//         }
//       })
//       .catch((error) => {
//         console.error("Failed to load brands:", error);
//       });
//   });
// });
document.addEventListener("DOMContentLoaded", function () {
  const categorySelect = document.getElementById("id_category");
  const brandSelect = document.getElementById("id_brand");

  if (!categorySelect || !brandSelect) return;

  console.log("✅ Product admin JS loaded");

  // Select2 renders selected value here
  const categoryRendered = document.getElementById(
    "select2-id_category-container"
  );

  if (!categoryRendered) {
    console.error("❌ Select2 container not found");
    return;
  }

  let lastCategory = categorySelect.value;

  // 🔥 Detect Select2 changes (vanilla-safe)
  const observer = new MutationObserver(() => {
    const categoryId = categorySelect.value;

    if (categoryId === lastCategory) return;
    lastCategory = categoryId;

    console.log("✅ Category changed:", categoryId);

    // Reset brand select
    brandSelect.innerHTML = '<option value="">---------</option>';

    if (!categoryId) return;

    fetch(
      `/admin/product/product/get-brands/?category_id=${categoryId}`,
      {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      }
    )
      .then((response) => {
        if (!response.ok) throw new Error("Network error");
        return response.json();
      })
      .then((brands) => {
        console.log("✅ Brands loaded:", brands);
        brands.forEach((brand) => {
          const option = document.createElement("option");
          option.value = brand.id;
          option.textContent = brand.name;
          brandSelect.appendChild(option);
        });

        // 🔁 Notify Select2 that options changed
        brandSelect.dispatchEvent(
          new Event("change", { bubbles: true })
        );
      })
      .catch((error) => {
        console.error("❌ Failed to load brands:", error);
      });
  });

  observer.observe(categoryRendered, {
    childList: true,
    subtree: true,
    characterData: true,
  });
});

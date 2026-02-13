(() => {
  const apiBase = "/api/mitigation";
  const statusFilter = "active";
  const currencySymbol = "\u20b9";
  const addedInterventions = [];
  let currentInterventions = [];

  const $theme = $("#theme");
  const $subtheme = $("#subtheme");
  const $component = $("#component");
  const $operations = $("#operations");
  const $mitigationIntervention = $("#mitigation_intervention");
  const $unit = $("#unit");
  const $quantity = $("#quantity");
  const $unitCost = $("#unit_cost");
  const $lumpsum = $("#lumpsum");
  const $estimatedCost = $("#estimated_cost");
  const $addedBody = $("#addedInterventionsBody");

  function showError(message) {
    if (window.Swal) {
      Swal.fire({ icon: "error", text: message });
    } else {
      alert(message);
    }
  }

  function formatNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return "0";
    }
    return number.toLocaleString("en-IN", { maximumFractionDigits: 2 });
  }

  function formatCurrency(value) {
    return `${currencySymbol} ${formatNumber(value)}`;
  }

  function parseNumber(value) {
    if (value === null || value === undefined || value === "") {
      return 0;
    }
    const number = Number(String(value).replace(/,/g, ""));
    return Number.isFinite(number) ? number : 0;
  }

  function setSelectOptions($select, options, placeholder) {
    $select.empty();
    $select.append(`<option value="" selected disabled>${placeholder}</option>`);
    options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue;
      $select.append(option);
    });
    $select.trigger("change.select2");
  }

  function getUnique(values) {
    return [...new Set(values.filter((value) => value))];
  }

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
  }

  function buildQuery(params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        searchParams.append(key, value);
      }
    });
    return searchParams.toString();
  }

  async function loadThemes() {
    const query = buildQuery({ status: statusFilter });
    const data = await fetchJson(`${apiBase}/themes/?${query}`);
    setSelectOptions($theme, data, gettext("Select Theme"));
  }

  async function loadSubthemes(theme) {
    if (!theme) {
      setSelectOptions($subtheme, [], gettext("Select Sub-theme"));
      return;
    }
    const query = buildQuery({ theme, status: statusFilter });
    const data = await fetchJson(`${apiBase}/subthemes/?${query}`);
    setSelectOptions($subtheme, data, gettext("Select Sub-theme"));
  }

  async function loadComponents(theme, subtheme) {
    if (!theme) {
      setSelectOptions($component, [], gettext("Select Component"));
      return;
    }
    const query = buildQuery({
      theme,
      subtheme,
      status: statusFilter,
    });
    const data = await fetchJson(`${apiBase}/vulnerable-assets/?${query}`);
    setSelectOptions($component, data, gettext("Select Component"));
  }

  function updateOperationsOptions() {
    const operations = getUnique(
      currentInterventions.map((item) => item.intervention_type).filter(Boolean)
    );
    const selected = $operations.val();
    setSelectOptions($operations, operations, gettext("Select Operation"));
    if (selected && operations.includes(selected)) {
      $operations.val(selected).trigger("change.select2");
    }
  }

  function updateMitigationOptions() {
    const selectedOperation = $operations.val();
    const interventions = currentInterventions.filter((item) => {
      if (!selectedOperation) {
        return true;
      }
      return item.intervention_type === selectedOperation;
    });

    $mitigationIntervention.empty();
    $mitigationIntervention.append(
      `<option value="" selected disabled>${gettext("Select Intervention")}</option>`
    );
    interventions.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.intervention_name;
      $mitigationIntervention.append(option);
    });
    $mitigationIntervention.trigger("change.select2");
    resetCostFields();
  }

  async function refreshInterventions() {
    const themeValue = $theme.val();
    if (!themeValue) {
      currentInterventions = [];
      updateOperationsOptions();
      updateMitigationOptions();
      return;
    }
    const query = buildQuery({
      theme: themeValue,
      subtheme: $subtheme.val(),
      vulnerable_asset: $component.val(),
      status: statusFilter,
    });
    currentInterventions = await fetchJson(
      `${apiBase}/interventions/?${query}`
    );
    updateOperationsOptions();
    updateMitigationOptions();
  }

  function resetCostFields() {
    $unit.val("");
    $quantity.val("");
    $unitCost.val("");
    $lumpsum.val("");
    $estimatedCost.val("");
  }

  function applyInterventionDetails() {
    const selectedId = $mitigationIntervention.val();
    if (!selectedId) {
      resetCostFields();
      return;
    }
    const selected = currentInterventions.find(
      (item) => String(item.id) === String(selectedId)
    );
    if (!selected) {
      resetCostFields();
      return;
    }

    const unitCost = parseNumber(selected.unit_cost_rs);
    const defaultQuantity = selected.default_quantity || "";

    $unit.val(selected.unit || "");
    $quantity.val(defaultQuantity);
    $unitCost.val(formatNumber(unitCost));
    $lumpsum.val(formatNumber(unitCost));
    updateEstimatedCost();
  }

  function updateEstimatedCost() {
    const quantity = parseNumber($quantity.val());
    const unitCost = parseNumber($unitCost.val());
    if (quantity <= 0 || unitCost <= 0) {
      showError(gettext("Please enter quantity and unit cost."));
      return;
    }
    const estimated = quantity * unitCost;
    $estimatedCost.val(formatCurrency(estimated));
  }

  function renderAddedInterventions() {
    $addedBody.empty();
    addedInterventions.forEach((item, index) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${item.component}</td>
        <td>${item.operation}</td>
        <td>${item.intervention}</td>
        <td>${item.unit}</td>
        <td>${formatNumber(item.quantity)}</td>
        <td>${formatNumber(item.unitCost)}</td>
        <td>${formatNumber(item.lumpsum)}</td>
      `;
      $addedBody.append(row);
    });

    $("#added-interventions-count").text(String(addedInterventions.length));
  }

  function updateTotals() {
    const totalQuantity = addedInterventions.reduce(
      (sum, item) => sum + item.quantity,
      0
    );
    const totalCost = addedInterventions.reduce(
      (sum, item) => sum + item.estimatedCost,
      0
    );

    $("#total-quantity").text(formatNumber(totalQuantity));
    $("#total-estimated-cost").text(formatCurrency(totalCost));
  }

  function updateReviewModal() {
    const themeText = $theme.find("option:selected").text() || "-";
    const subthemeText = $subtheme.find("option:selected").text() || "-";
    const componentText = $component.find("option:selected").text() || "-";

    $("#review-theme").text(themeText);
    $("#review-subtheme").text(subthemeText);
    $("#review-component").text(componentText);
    $("#review-vulnerable-asset").text(componentText);

    const reviewContainer = $("#review-interventions");
    reviewContainer.empty();

    if (addedInterventions.length === 0) {
      reviewContainer.append(
        `<p class="text-muted mb-0">${gettext("No interventions added yet.")}</p>`
      );
    } else {
      addedInterventions.forEach((item) => {
        const block = document.createElement("div");
        block.className = "bg-gray p-3 rounded mb-2";
        block.innerHTML = `
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <p class="mb-1 fw-bold">${item.intervention}</p>
              <p class="mb-0 text-muted small">Quantity: ${formatNumber(
                item.quantity
              )} x Unit Cost: ${formatCurrency(item.unitCost)}</p>
            </div>
            <p class="mb-0 fw-bold text-primary">${formatCurrency(
              item.estimatedCost
            )}</p>
          </div>
        `;
        reviewContainer.append(block);
      });
    }

    const totalQuantity = addedInterventions.reduce(
      (sum, item) => sum + item.quantity,
      0
    );
    const totalCost = addedInterventions.reduce(
      (sum, item) => sum + item.estimatedCost,
      0
    );
    $("#review-total-quantity").text(formatNumber(totalQuantity));
    $("#review-total-cost").text(formatCurrency(totalCost));
  }

  function addIntervention() {
    const component = $component.val();
    const operation = $operations.val();
    const interventionId = $mitigationIntervention.val();

    if (!component || !operation || !interventionId) {
      showError(gettext("Please select component, operation, and intervention."));
      return;
    }

    const selected = currentInterventions.find(
      (item) => String(item.id) === String(interventionId)
    );
    if (!selected) {
      showError(gettext("Selected intervention not found."));
      return;
    }

    const quantity = parseNumber($quantity.val());
    const unitCost = parseNumber($unitCost.val());
    const estimatedCost = quantity * unitCost;
    const lumpsum = parseNumber($lumpsum.val());

    addedInterventions.push({
      component,
      operation,
      intervention: selected.intervention_name,
      unit: selected.unit || "",
      quantity,
      unitCost,
      estimatedCost,
      lumpsum: lumpsum || unitCost,
    });

    renderAddedInterventions();
    updateTotals();
  }

  async function initMitigationForm() {
    initializeSelect2("theme", gettext("Select Theme"));
    initializeSelect2("subtheme", gettext("Select Sub-theme"));
    initializeSelect2("component", gettext("Select Component"));
    initializeSelect2("operations", gettext("Select Operation"));
    initializeSelect2("mitigation_intervention", gettext("Select Intervention"));

    await loadThemes();
    await loadSubthemes($theme.val());
    await loadComponents($theme.val(), $subtheme.val());
    await refreshInterventions();
  }

  async function initLocationSelectors() {
    const userDistrictId = $("#userDistrictId").val();
    const userCircleId = $("#userCircleId").val();
    const userGramPanchayatId = $("#userGramPanchayatId").val();
    const userVillageId = $("#userVillageId").val();

    initializeSelect2("district", gettext("Select Districts"));
    initializeSelect2("circle", gettext("Select Circle"));
    initializeSelect2("gram_panchayat", gettext("Select Gram Panchayat"));
    initializeSelect2("village", gettext("Select Villages"));

    await setupLocationSelectors(
      "district",
      "circle",
      "gram_panchayat",
      "village",
      userDistrictId,
      userCircleId,
      userGramPanchayatId,
      userVillageId
    );

    if (typeof New_updateSummaryText === "function") {
      New_updateSummaryText();
    }

    $("#district, #circle, #gram_panchayat, #village").on(
      "change",
      () => {
        if (typeof New_updateSummaryText === "function") {
          New_updateSummaryText();
        }
      }
    );
  }

  $(async () => {
    await initLocationSelectors();
    await initMitigationForm();

    $theme.on("change", async () => {
      await loadSubthemes($theme.val());
      await loadComponents($theme.val(), $subtheme.val());
      await refreshInterventions();
    });

    $subtheme.on("change", async () => {
      await loadComponents($theme.val(), $subtheme.val());
      await refreshInterventions();
    });

    $component.on("change", async () => {
      await refreshInterventions();
    });

    $operations.on("change", () => {
      updateMitigationOptions();
    });

    $mitigationIntervention.on("change", () => {
      applyInterventionDetails();
    });

    $quantity.on("input", () => {
      updateEstimatedCost();
    });

    $("#addInterventionBtn").on("click", (event) => {
      event.preventDefault();
      addIntervention();
    });

    $("#reviewModal").on("show.bs.modal", () => {
      updateReviewModal();
    });
  });
})();

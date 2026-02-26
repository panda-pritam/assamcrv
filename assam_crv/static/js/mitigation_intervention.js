(() => {
  const langMatch = window.location.pathname.match(/^\/([a-z]{2})(\/|$)/);
  const langPrefix = langMatch ? `/${langMatch[1]}` : "";
  const apiBase = `${langPrefix}/api/mitigation`;
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
  const $formSection = $(".mitigation-measures-section").first();

  function showError(message) {
    if (window.Swal) {
      Swal.fire({ icon: "error", text: message });
    } else {
      alert(message);
    }
  }

  function getCsrfHeaders() {
    const headers = {};
    if (typeof getCSRFToken === "function") {
      const token = getCSRFToken();
      if (token) {
        headers["X-CSRFToken"] = token;
      }
    }
    return headers;
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

  function normalizeValue(value) {
    if (!value) {
      return "";
    }
    return String(value).trim().toLowerCase();
  }

  function filterInterventions() {
    const selectedComponent = normalizeValue($component.val());
    const selectedOperation = normalizeValue($operations.val());

    return currentInterventions.filter((item) => {
      const componentMatch = selectedComponent
        ? normalizeValue(item.vulnerable_asset) === selectedComponent
        : true;
      const operationMatch = selectedOperation
        ? normalizeValue(item.intervention_type) === selectedOperation
        : true;
      return componentMatch && operationMatch;
    });
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
    const selectedComponent = normalizeValue($component.val());
    const operations = getUnique(
      currentInterventions
        .filter((item) =>
          selectedComponent
            ? normalizeValue(item.vulnerable_asset) === selectedComponent
            : true
        )
        .map((item) => item.intervention_type)
        .filter(Boolean)
    );
    const selected = $operations.val();
    setSelectOptions($operations, operations, gettext("Select Operation"));
    if (selected && operations.includes(selected)) {
      $operations.val(selected).trigger("change.select2");
    }
  }

  function updateMitigationOptions() {
    const interventions = filterInterventions();

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
      $estimatedCost.val("");
      return;
    }
    const estimated = quantity * unitCost;
    $estimatedCost.val(formatCurrency(estimated));
  }

  async function savePlanItem(payload) {
    const headers = {
      "Content-Type": "application/json",
      ...getCsrfHeaders(),
    };

    const response = await fetch(`${apiBase}/plan-items/`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let detail = "";
      try {
        const data = await response.json();
        detail = data.detail || JSON.stringify(data);
      } catch (error) {
        detail = "";
      }
      throw new Error(detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  async function deletePlanItem(planItemId) {
    if (!planItemId) {
      return;
    }

    const response = await fetch(`${apiBase}/plan-items/${planItemId}/`, {
      method: "DELETE",
      headers: getCsrfHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
  }

  function renderAddedInterventions() {
    $addedBody.empty();
    addedInterventions.forEach((item, index) => {
      const row = document.createElement("tr");
      const component = item.component || "-";
      const operation = item.operation || "-";
      const intervention = item.intervention || "-";
      const unit = item.unit || "-";
      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${component}</td>
        <td>${operation}</td>
        <td>${intervention}</td>
        <td>${unit}</td>
        <td>${formatNumber(item.quantity)}</td>
        <td>${formatNumber(item.unitCost)}</td>
        <td>${formatNumber(item.lumpsum)}</td>
        <td>
          <button type="button" class="btn btn-link p-0 edit-intervention" data-index="${index}" aria-label="${gettext(
            "Edit intervention"
          )}">
            <i class="fas fa-edit"></i>
          </button>
          <button type="button" class="btn btn-link p-0 ms-2 text-danger delete-intervention" data-index="${index}" aria-label="${gettext(
            "Delete intervention"
          )}">
            <i class="fas fa-trash-alt"></i>
          </button>
        </td>
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

  function buildAddedInterventionsFromPlanItems(items) {
    return items.map((item) => {
      const master = item.master_data || {};
      const unitCost = parseNumber(item.unit_cost_rs);
      const quantity = parseNumber(item.quantity);
      const estimatedCost =
        parseNumber(item.estimated_cost_rs) || unitCost * quantity;

      return {
        planItemId: item.id,
        masterId: master.id,
        theme: master.theme || "",
        subtheme: master.subtheme || "",
        component: master.vulnerable_asset || "",
        operation: master.intervention_type || "",
        intervention: master.intervention_name || "",
        unit: master.unit || "",
        quantity,
        unitCost,
        estimatedCost,
        lumpsum: unitCost,
      };
    });
  }

  async function populateFormFromItem(item) {
    if (!item) {
      return;
    }

    const themeValue = item.theme || "";
    const subthemeValue = item.subtheme || "";

    $theme.val(themeValue).trigger("change.select2");
    await loadSubthemes(themeValue);
    $subtheme.val(subthemeValue).trigger("change.select2");
    await loadComponents(themeValue, subthemeValue);
    await refreshInterventions();

    if (item.component) {
      $component.val(item.component).trigger("change.select2");
    }
    updateOperationsOptions();
    if (item.operation) {
      $operations.val(item.operation).trigger("change.select2");
    }
    updateMitigationOptions();

    if (item.masterId) {
      $mitigationIntervention
        .val(String(item.masterId))
        .trigger("change.select2");
    }
    applyInterventionDetails();

    if (item.unit) {
      $unit.val(item.unit);
    }
    if (Number.isFinite(item.quantity)) {
      $quantity.val(item.quantity);
    }
    if (Number.isFinite(item.unitCost)) {
      $unitCost.val(formatNumber(item.unitCost));
    }
    if (Number.isFinite(item.lumpsum)) {
      $lumpsum.val(formatNumber(item.lumpsum));
    }
    updateEstimatedCost();
  }

  function scrollToForm() {
    if (!$formSection.length) {
      return;
    }
    const element = $formSection.get(0);
    if (!element) {
      return;
    }
    if (typeof element.scrollIntoView === "function") {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const offsetTop = $formSection.offset().top;
    window.scrollTo({ top: Math.max(offsetTop - 20, 0), behavior: "smooth" });
  }

  async function loadPlanItems(villageId) {
    if (!villageId) {
      addedInterventions.length = 0;
      renderAddedInterventions();
      updateTotals();
      return;
    }

    const query = buildQuery({ village_id: villageId, status: "draft" });
    const items = await fetchJson(`${apiBase}/plan-items/?${query}`);
    addedInterventions.length = 0;
    addedInterventions.push(...buildAddedInterventionsFromPlanItems(items));
    renderAddedInterventions();
    updateTotals();
  }

  async function addIntervention() {
    const component = $component.val();
    const operation = $operations.val();
    const interventionId = $mitigationIntervention.val();
    const villageId = $("#village").val();

    if (!component || !operation || !interventionId || !villageId) {
      showError(
        gettext("Please select village, component, operation, and intervention.")
      );
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
    const payload = {
      master: selected.id,
      quantity,
      unit_cost_rs: unitCost,
      estimated_cost_rs: estimatedCost,
      status: "draft",
    };
    payload.village = villageId;

    try {
      await savePlanItem(payload);
    } catch (error) {
      showError(error.message || gettext("Unable to save intervention."));
      return;
    }

    await loadPlanItems(villageId);
  }

  function resetInterventionFields() {
    $mitigationIntervention.val("").trigger("change.select2");
    resetCostFields();
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

    $("#addInterventionBtn").on("click", async (event) => {
      event.preventDefault();
      await addIntervention();
    });

    $(".add-intervention-btn").on("click", (event) => {
      event.preventDefault();
      resetInterventionFields();
    });

    $("#village").on("change", async () => {
      await loadPlanItems($("#village").val());
    });

    $("#reviewModal").on("show.bs.modal", () => {
      updateReviewModal();
    });

    $addedBody.on("click", ".edit-intervention", async (event) => {
      event.preventDefault();
      const index = Number($(event.currentTarget).data("index"));
      if (!Number.isFinite(index)) {
        return;
      }
      await populateFormFromItem(addedInterventions[index]);
      scrollToForm();
    });

    $addedBody.on("click", ".delete-intervention", async (event) => {
      event.preventDefault();
      const index = Number($(event.currentTarget).data("index"));
      if (!Number.isFinite(index)) {
        return;
      }

      const confirmed = window.Swal
        ? await Swal.fire({
            icon: "warning",
            text: gettext("Delete this intervention?"),
            showCancelButton: true,
            confirmButtonText: gettext("Delete"),
            cancelButtonText: gettext("Cancel"),
          }).then((result) => result.isConfirmed)
        : confirm(gettext("Delete this intervention?"));

      if (!confirmed) {
        return;
      }

      const selectedItem = addedInterventions[index];
      const villageId = $("#village").val();

      if (selectedItem && selectedItem.planItemId) {
        try {
          await deletePlanItem(selectedItem.planItemId);
        } catch (error) {
          showError(error.message || gettext("Unable to delete intervention."));
          return;
        }
        await loadPlanItems(villageId);
        return;
      }

      addedInterventions.splice(index, 1);
      renderAddedInterventions();
      updateTotals();
    });
  });
})();

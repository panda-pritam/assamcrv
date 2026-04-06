(() => {
  const langMatch = window.location.pathname.match(/^\/([a-z]{2})(\/|$)/);
  const langPrefix = langMatch ? `/${langMatch[1]}` : "";
  const apiBase = `${langPrefix}/api/mitigation`;
  const statusFilter = "active";
  const currencySymbol = "\u20b9";
  const housingUnitSqft = 450;
  const addedInterventions = [];
  let currentInterventions = [];
  let totalAvailableCount = null;
  let currentAssetMode = "";
  let availableComponents = new Set();
  let availableComponentsNorm = new Set();

  const $theme = $("#theme");
  const $subtheme = $("#subtheme");
  const $component = $("#component");
  const $vulnerabilityType = $("#vulnerability_type");
  const $operations = $("#operations");
  const $mitigationIntervention = $("#mitigation_intervention");
  const $unit = $("#unit");
  const $quantity = $("#quantity");
  const $unitCost = $("#unit_cost");
  const $estimatedCost = $("#estimated_cost");
  const $addedBody = $("#addedInterventionsBody");
  const $formSection = $(".mitigation-measures-section").first();
  const $submitBtn = $("#addInterventionBtn");
  const $vulnerableAssetsHead = $("#vulnerableAssetsHead");
  const $vulnerableAssetsBody = $("#vulnerableAssetsBody");
  const $quantityRemaining = $("#quantity-remaining");
  const $quantityError = $("#quantity-error");
  const $unitLabel = $("label[for='unit']");
  const $interventionNoteBox = $("#intervention-note-box");
  const defaultUnitLabel = $unitLabel.text();
  let editState = { index: null, planItemId: null };
  let currentAreaValue = 0;
  let housingSummaryRows = [];

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

  function setSelectOptionsWithLabels($select, options, placeholder) {
    $select.empty();
    $select.append(`<option value="" selected disabled>${placeholder}</option>`);
    options.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = optionValue.value;
      option.textContent = optionValue.label;
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

  function normalizeRoadType(value) {
    let normalized = normalizeValue(value);
    normalized = normalized.replace(/\s+/g, " ");
    normalized = normalized.replace("bitumious", "bituminous");
    normalized = normalized.replace("concreate", "concrete");
    return normalized;
  }

  function normalizeHouseType(value) {
    return normalizeValue(value).replace(/\s+/g, " ");
  }

  function parseAreaValue(value) {
    if (!value) {
      return 0;
    }
    const match = String(value).match(/[\d,.]+/);
    return match ? parseNumber(match[0]) : 0;
  }

  function getAssetMode() {
    const subthemeValue = normalizeValue($subtheme.val());
    if (subthemeValue.includes("housing") || subthemeValue.includes("house")) {
      return "housing";
    }
    if (subthemeValue.includes("road")) {
      return "road";
    }
    if (
      subthemeValue.includes("critical") ||
      subthemeValue.includes("facility")
    ) {
      return "critical";
    }
    return "";
  }

  function getSelectedVulnerabilityType() {
    return normalizeValue($vulnerabilityType.val());
  }

  function loadVulnerabilityOptions() {
    const options = [
      { value: "flood", label: gettext("Flood") },
      { value: "erosion", label: gettext("Erosion") },
      { value: "flood_erosion", label: gettext("Flood and Erosion") },
    ];
    setSelectOptionsWithLabels(
      $vulnerabilityType,
      options,
      gettext("Select Vulnerability Type")
    );
  }

  function filterInterventions() {
    const selectedComponent = normalizeHouseType($component.val());
    const selectedOperation = normalizeValue($operations.val());
    const vulnerabilityType = getSelectedVulnerabilityType();

    return currentInterventions.filter((item) => {
      const componentMatch =
        currentAssetMode === "housing"
          ? true
          : selectedComponent
          ? normalizeValue(item.vulnerable_asset) === selectedComponent
          : true;
      const operationMatch = selectedOperation
        ? normalizeValue(item.intervention_type) === selectedOperation
        : true;
      const vulnerabilityMatch =
        !vulnerabilityType || vulnerabilityType === "flood"
          ? true
          : normalizeValue(item.intervention_type).includes("relocat");
      return componentMatch && operationMatch && vulnerabilityMatch;
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
      return [];
    }
    const query = buildQuery({ theme, status: statusFilter });
    const data = await fetchJson(`${apiBase}/subthemes/?${query}`);
    setSelectOptions($subtheme, data, gettext("Select Sub-theme"));
    return data;
  }

  function autoSelectHousingSubtheme(theme, subthemes) {
    if (!theme || $subtheme.val()) {
      return false;
    }
    const themeNorm = normalizeValue(theme);
    if (!themeNorm.includes("housing") && !themeNorm.includes("house")) {
      return false;
    }
    const match = subthemes.find((item) => {
      const norm = normalizeValue(item);
      return norm.includes("housing") || norm.includes("house");
    });
    if (!match) {
      return false;
    }
    $subtheme.val(match).trigger("change.select2");
    return true;
  }

  async function loadComponents(theme, subtheme) {
    if (!theme) {
      setSelectOptions($component, [], gettext("Select Component"));
      return;
    }
    if (currentAssetMode === "housing" && housingSummaryRows.length) {
      const options = housingSummaryRows
        .map((row) => row.house_type || "")
        .filter((value) => value);
      setSelectOptions($component, options, gettext("Select Component"));
      return;
    }
    const query = buildQuery({
      theme,
      subtheme,
      status: statusFilter,
    });
    const data = await fetchJson(`${apiBase}/vulnerable-assets/?${query}`);
    let options = data;
    if (currentAssetMode === "road" && availableComponentsNorm.size > 0) {
      options = data.filter((item) =>
        availableComponentsNorm.has(normalizeRoadType(item))
      );
    }
    setSelectOptions($component, options, gettext("Select Component"));
  }

  function updateOperationsOptions() {
    const selectedComponent = normalizeValue($component.val());
    const vulnerabilityType = getSelectedVulnerabilityType();
    const operations = getUnique(
      currentInterventions
        .filter((item) =>
          currentAssetMode === "housing"
            ? true
            : selectedComponent
            ? normalizeValue(item.vulnerable_asset) === selectedComponent
            : true
        )
        .filter((item) => {
          if (!vulnerabilityType || vulnerabilityType === "flood") {
            return true;
          }
          const operationValue = normalizeValue(item.intervention_type);
          return operationValue.includes("relocat");
        })
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
    setMitigationNote("");
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
    $estimatedCost.val("");
    currentAreaValue = 0;
    updateQuantityRemaining();
    validateQuantity();
    resetUnitLabel();
  }

  function resetUnitLabel() {
    if ($unitLabel.length) {
      $unitLabel.text(defaultUnitLabel);
    }
  }

  function setMitigationNote(note) {
    if (!$interventionNoteBox.length) {
      return;
    }
    const text = note ? String(note).trim() : "";
    if (!text) {
      $interventionNoteBox.addClass("d-none").text("");
      return;
    }
    $interventionNoteBox.removeClass("d-none").text(text);
  }

  function applyUnitBehavior(assetMode) {
    if (assetMode === "critical") {
      $unit.prop("readonly", false);
      $unit.css("background-color", "");
      $unitLabel.text(`${defaultUnitLabel} (Sqft)`);
      return;
    }
    $unit.prop("readonly", true);
    $unit.css("background-color", "#F2F4F6");
    if (assetMode === "housing") {
      $unitLabel.text(`${defaultUnitLabel} (Sqft)`);
      return;
    }
    resetUnitLabel();
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
    const areaValue = parseNumber(selected.area);
    const unitLabel = selected.unit || "";

    if (currentAssetMode === "housing") {
      $unit.val(`${formatNumber(housingUnitSqft)} Sqft`);
      $unitLabel.text(`${defaultUnitLabel} (Sqft)`);
      currentAreaValue = housingUnitSqft;
    } else if (currentAssetMode === "road") {
      $unit.val(unitLabel || "Meter");
      resetUnitLabel();
      currentAreaValue = areaValue || 1;
    } else {
      $unit.val(unitLabel || formatNumber(areaValue));
      currentAreaValue = areaValue || parseAreaValue($unit.val()) || 1;
    }

    $quantity.val("");
    $unitCost.val(formatNumber(unitCost));
    updateEstimatedCost();
    applyUnitBehavior(currentAssetMode);
    setMitigationNote(selected.display_note || "");
  }

  function getAreaValueForEstimate() {
    if (currentAssetMode === "housing") {
      return housingUnitSqft;
    }
    const inputArea = parseAreaValue($unit.val());
    if (inputArea > 0) {
      return inputArea;
    }
    return currentAreaValue || 0;
  }

  function calculateEstimatedCost() {
    const quantity = parseNumber($quantity.val());
    const unitCost = parseNumber($unitCost.val());
    const areaValue = getAreaValueForEstimate();
    if (quantity <= 0 || unitCost <= 0 || areaValue <= 0) {
      return null;
    }
    return {
      quantity,
      unitCost,
      areaValue,
      estimated: areaValue * quantity * unitCost,
    };
  }

  function updateEstimatedCost() {
    const estimate = calculateEstimatedCost();
    if (!estimate) {
      $estimatedCost.val("");
      return;
    }
    $estimatedCost.val(formatCurrency(estimate.estimated));
  }

  function setSubmitDisabled(disabled) {
    if (!$submitBtn.length) {
      return;
    }
    $submitBtn.prop("disabled", disabled);
  }

  function validateQuantity() {
    if (!$quantityError.length) {
      return true;
    }
    const quantity = parseNumber($quantity.val());
    if (!Number.isFinite(totalAvailableCount)) {
      $quantityError.text("");
      setSubmitDisabled(false);
      return true;
    }
    const remaining = Math.max(
      totalAvailableCount - getPlannedQuantityForSelection(editState.index),
      0
    );
    if (quantity > remaining) {
      const typology = $component.val() || gettext("selected typology");
      const vulnerabilityText =
        $vulnerabilityType.find("option:selected").text() ||
        gettext("selected vulnerability");
      $quantityError.text(
        gettext(
          `You can select up to ${formatNumber(
            remaining
          )} ${typology} households for ${vulnerabilityText} vulnerability. Please enter ${formatNumber(
            remaining
          )} or less.`
        )
      );
      setSubmitDisabled(true);
      return false;
    }
    $quantityError.text("");
    setSubmitDisabled(false);
    return true;
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

  async function updatePlanItem(planItemId, payload) {
    if (!planItemId) {
      throw new Error(gettext("Missing plan item id for update."));
    }

    const headers = {
      "Content-Type": "application/json",
      ...getCsrfHeaders(),
    };

    const response = await fetch(`${apiBase}/plan-items/${planItemId}/`, {
      method: "PATCH",
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

  async function finalizePlanItems(villageId) {
    if (!villageId) {
      throw new Error(gettext("Please select a village."));
    }
    const headers = {
      "Content-Type": "application/json",
      ...getCsrfHeaders(),
    };
    const response = await fetch(`${apiBase}/plan-items/finalize/`, {
      method: "POST",
      headers,
      body: JSON.stringify({ village_id: villageId }),
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
        <td>${formatCurrency(item.unitCost)}</td>
        <td>${formatCurrency(item.estimatedCost)}</td>
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

  function updateWarningModal() {
    const themeText = $theme.find("option:selected").text() || "-";
    const subthemeText = $subtheme.find("option:selected").text() || "-";
    $("#warning-theme").text(themeText);
    $("#warning-subtheme").text(subthemeText);

    const container = $("#warning-remaining-typologies");
    container.empty();

    if (currentAssetMode !== "housing" || !housingSummaryRows.length) {
      container.append(
        `<p class="text-muted mb-0">${gettext(
          "Remaining counts are available for housing typologies."
        )}</p>`
      );
      return;
    }

    const rows = housingSummaryRows
      .map((row) => {
        const typology = row.house_type || "-";
        const remainingFlood = Math.max(
          getHousingAvailableFor(row, "flood") -
            getPlannedQuantityFor(typology, "flood"),
          0
        );
        const remainingErosion = Math.max(
          getHousingAvailableFor(row, "erosion") -
            getPlannedQuantityFor(typology, "erosion"),
          0
        );
        return { typology, remainingFlood, remainingErosion };
      })
      .filter((row) => row.remainingFlood > 0 || row.remainingErosion > 0);

    if (!rows.length) {
      container.append(
        `<p class="text-muted mb-0">${gettext(
          "All housing typologies are covered."
        )}</p>`
      );
      return;
    }

    const table = document.createElement("table");
    table.className = "w-100";
    table.innerHTML = `
      <thead>
        <tr>
          <th class="text-left">${gettext("Typology")}</th>
          <th class="text-end">${gettext("Flood Remaining")}</th>
          <th class="text-end">${gettext("Erosion Remaining")}</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    const tbody = table.querySelector("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="text-left">${row.typology}</td>
        <td class="text-end">${formatNumber(row.remainingFlood)}</td>
        <td class="text-end">${formatNumber(row.remainingErosion)}</td>
      `;
      tbody.appendChild(tr);
    });
    container.append(table);
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
        component: item.typology || master.vulnerable_asset || "",
        vulnerabilityType: item.vulnerability_type || "",
        operation: master.intervention_type || "",
        intervention: master.intervention_name || "",
        unit: master.unit || "",
        quantity,
        unitCost,
        estimatedCost,
        lumpsum: estimatedCost,
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
    if (item.vulnerabilityType) {
      $vulnerabilityType
        .val(String(item.vulnerabilityType))
        .trigger("change.select2");
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
      currentAreaValue = parseAreaValue($unit.val()) || currentAreaValue;
    }
    if (Number.isFinite(item.quantity)) {
      $quantity.val(item.quantity);
    }
    if (Number.isFinite(item.unitCost)) {
      $unitCost.val(formatNumber(item.unitCost));
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

  function scrollToListing() {
    const $listing = $(".added-interventions-table").first();
    if (!$listing.length) {
      return;
    }
    const element = $listing.get(0);
    if (!element) {
      return;
    }
    if (typeof element.scrollIntoView === "function") {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const offsetTop = $listing.offset().top;
    window.scrollTo({ top: Math.max(offsetTop - 20, 0), behavior: "smooth" });
  }

  async function loadPlanItems(villageId) {
    if (!villageId) {
      addedInterventions.length = 0;
      renderAddedInterventions();
      updateTotals();
      setSubmitMode(false);
      resetEditState();
      updateQuantityRemaining();
      return;
    }

    const query = buildQuery({ village_id: villageId, status: "draft" });
    const items = await fetchJson(`${apiBase}/plan-items/?${query}`);
    addedInterventions.length = 0;
    addedInterventions.push(...buildAddedInterventionsFromPlanItems(items));
    renderAddedInterventions();
    updateTotals();
    setSubmitMode(false);
    resetEditState();
    updateQuantityRemaining();
  }

  function getHousingAvailableFor(row, vulnerabilityType) {
    if (!row || !vulnerabilityType) {
      return 0;
    }
    if (vulnerabilityType === "flood") {
      return parseNumber(row.flood_vulnerable);
    }
    if (vulnerabilityType === "erosion") {
      return parseNumber(row.erosion_vulnerable);
    }
    if (vulnerabilityType === "flood_erosion") {
      return parseNumber(row.flood_erosion_vulnerable);
    }
    return 0;
  }

  function getHousingCountBySelection() {
    const vulnerabilityType = getSelectedVulnerabilityType();
    if (!vulnerabilityType) {
      return null;
    }
    const selectedComponent = normalizeValue($component.val());

    if (selectedComponent) {
      const match = housingSummaryRows.find(
        (row) => normalizeHouseType(row.house_type) === selectedComponent
      );
      return match ? getHousingAvailableFor(match, vulnerabilityType) : 0;
    }

    return housingSummaryRows.reduce(
      (sum, row) => sum + getHousingAvailableFor(row, vulnerabilityType),
      0
    );
  }

  function updateTotalAvailableCount() {
    if (currentAssetMode !== "housing") {
      totalAvailableCount = null;
      updateQuantityRemaining();
      return;
    }
    const count = getHousingCountBySelection();
    totalAvailableCount = Number.isFinite(count) ? count : null;
    updateQuantityRemaining();
    validateQuantity();
  }

  function updateQuantityRemaining() {
    if (!$quantityRemaining.length) {
      return;
    }
    if (!Number.isFinite(totalAvailableCount)) {
      $quantityRemaining.text("");
      return;
    }
    const remaining = Math.max(
      totalAvailableCount - getPlannedQuantityForSelection(editState.index),
      0
    );
    $quantityRemaining.text(`${formatNumber(remaining)} left`);
  }

  function getPlannedQuantityFor(component, vulnerability, excludeIndex) {
    const selectedComponent = normalizeHouseType(component || "");
    const selectedVulnerability = normalizeValue(vulnerability || "");
    return addedInterventions.reduce((sum, item, index) => {
      if (Number.isFinite(excludeIndex) && index === excludeIndex) {
        return sum;
      }
      if (
        selectedComponent &&
        normalizeHouseType(item.component) !== selectedComponent
      ) {
        return sum;
      }
      if (
        selectedVulnerability &&
        normalizeValue(item.vulnerabilityType) !== selectedVulnerability
      ) {
        return sum;
      }
      return sum + parseNumber(item.quantity);
    }, 0);
  }

  function getPlannedQuantityForSelection(excludeIndex) {
    return getPlannedQuantityFor(
      $component.val(),
      $vulnerabilityType.val(),
      excludeIndex
    );
  }

  function warnRemainingBuildings() {
    if (!Number.isFinite(totalAvailableCount)) {
      return;
    }
    const remaining = Math.max(
      totalAvailableCount - getPlannedQuantityForSelection(editState.index),
      0
    );
    if (remaining <= 0) {
      return;
    }
    const message = `${gettext(
      "Remaining buildings to be considered:"
    )} ${formatNumber(remaining)}`;
    if (window.Swal) {
      Swal.fire({ icon: "warning", text: message });
    } else {
      alert(message);
    }
  }

  function setTableHeader(headers) {
    if (!$vulnerableAssetsHead.length) {
      return;
    }
    const row = document.createElement("tr");
    headers.forEach((label) => {
      const th = document.createElement("th");
      th.textContent = label;
      row.appendChild(th);
    });
    $vulnerableAssetsHead.empty().append(row);
  }

  function renderHousingSummary(rows) {
    setTableHeader([
      gettext("Typology"),
      gettext("Flood vulnerable houses (High+Severe)"),
      gettext("Erosion vulnerable houses (High+Severe)"),
      gettext("Flood and erosion houses (High+Severe)"),
    ]);
    $vulnerableAssetsBody.empty();
    housingSummaryRows = (Array.isArray(rows) ? rows : []).filter((row) => {
      const flood = parseNumber(row.flood_vulnerable);
      const erosion = parseNumber(row.erosion_vulnerable);
      const both = parseNumber(row.flood_erosion_vulnerable);
      return flood > 0 || erosion > 0 || both > 0;
    });
    if (!housingSummaryRows.length) {
      $vulnerableAssetsBody.append(
        `<tr><td colspan="4" class="text-muted">${gettext(
          "No data available."
        )}</td></tr>`
      );
      totalAvailableCount = null;
      updateQuantityRemaining();
      return;
    }
    housingSummaryRows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="text-left">${row.house_type || "-"}</td>
        <td><span class="badge-blue">${formatNumber(
          row.flood_vulnerable
        )}</span></td>
        <td><span class="badge-green">${formatNumber(
          row.erosion_vulnerable
        )}</span></td>
        <td><span class="badge-blue">${formatNumber(
          row.flood_erosion_vulnerable
        )}</span></td>
      `;
      $vulnerableAssetsBody.append(tr);
    });
    updateQuantityRemaining();
  }

  function renderRoadSummary(rows) {
    setTableHeader([
      gettext("Road Type"),
      gettext("Length for flood mitigation (m)"),
      gettext("Length for erosion & flood mitigation (m)"),
    ]);
    $vulnerableAssetsBody.empty();
    if (!rows.length) {
      $vulnerableAssetsBody.append(
        `<tr><td colspan="3" class="text-muted">${gettext(
          "No data available."
        )}</td></tr>`
      );
      totalAvailableCount = null;
      updateQuantityRemaining();
      return;
    }
    totalAvailableCount = null;
    updateQuantityRemaining();
    rows.forEach((row) => {
      const roadType = String(row.road_type || "");
      availableComponents.add(roadType);
      availableComponentsNorm.add(normalizeRoadType(roadType));
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="text-left">${roadType || "-"}</td>
        <td><span class="badge-blue">${formatNumber(
          row.flood_length_m
        )}</span></td>
        <td><span class="badge-green">${formatNumber(
          row.erosion_length_m
        )}</span></td>
      `;
      $vulnerableAssetsBody.append(tr);
    });
  }

  function renderCriticalList(rows) {
    setTableHeader([
      gettext("Facility"),
      gettext("Risk Category"),
      gettext("Area (Sqft)"),
    ]);
    $vulnerableAssetsBody.empty();
    if (!rows.length) {
      $vulnerableAssetsBody.append(
        `<tr><td colspan="3" class="text-muted">${gettext(
          "No data available."
        )}</td></tr>`
      );
      totalAvailableCount = null;
      updateQuantityRemaining();
      return;
    }
    totalAvailableCount = null;
    updateQuantityRemaining();
    rows.forEach((row) => {
      const labelParts = [row.facility_name, row.occupancy_type].filter(
        (part) => part && part !== "-"
      );
      const label = labelParts.length ? labelParts.join(" - ") : "-";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="text-left">${label}</td>
        <td>${row.risk_category || "-"}</td>
        <td><span class="badge-blue">${formatNumber(
          row.area_sqft
        )}</span></td>
      `;
      $vulnerableAssetsBody.append(tr);
    });
  }

  async function loadVulnerableAssets(villageId) {
    currentAssetMode = getAssetMode();
    availableComponents = new Set();
    availableComponentsNorm = new Set();
    if (currentAssetMode !== "housing") {
      $vulnerabilityType.val("").trigger("change.select2");
      housingSummaryRows = [];
    }
    if (!currentAssetMode || !villageId) {
      $vulnerableAssetsHead.empty();
      $vulnerableAssetsBody.empty();
      totalAvailableCount = null;
      updateQuantityRemaining();
      return;
    }

    const query = buildQuery({ village_id: villageId });
    if (currentAssetMode === "housing") {
      const data = await fetchJson(
        `${apiBase}/housing-risk-summary/?${query}`
      );
      renderHousingSummary(Array.isArray(data) ? data : []);
      await loadComponents($theme.val(), $subtheme.val());
      return;
    }
    if (currentAssetMode === "road") {
      const data = await fetchJson(
        `${apiBase}/road-risk-summary/?${query}`
      );
      renderRoadSummary(Array.isArray(data) ? data : []);
      await loadComponents($theme.val(), $subtheme.val());
      return;
    }
    if (currentAssetMode === "critical") {
      const data = await fetchJson(
        `${apiBase}/critical-risk-list/?${query}`
      );
      renderCriticalList(Array.isArray(data) ? data : []);
      return;
    }
  }

  async function addIntervention() {
    const component = $component.val();
    const vulnerabilityType = $vulnerabilityType.val();
    const operation = $operations.val();
    const interventionId = $mitigationIntervention.val();
    const villageId = $("#village").val();

    if (
      !component ||
      !vulnerabilityType ||
      !operation ||
      !interventionId ||
      !villageId
    ) {
      showError(
        gettext(
          "Please select village, typology, vulnerability type, mitigation type, and intervention."
        )
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

    if (!validateQuantity()) {
      showError(gettext("Quantity exceeds available count."));
      return;
    }

    const estimate = calculateEstimatedCost();
    if (!estimate) {
      showError(gettext("Please enter quantity and valid cost details."));
      return;
    }
    const { quantity, unitCost, areaValue } = estimate;
    const matchingIndex = !editState.planItemId
      ? addedInterventions.findIndex(
          (item) =>
            normalizeHouseType(item.component) ===
              normalizeHouseType(component) &&
            normalizeValue(item.vulnerabilityType) ===
              normalizeValue(vulnerabilityType) &&
            normalizeValue(item.operation) === normalizeValue(operation) &&
            String(item.masterId || "") === String(selected.id)
        )
      : -1;
    const existingItem =
      matchingIndex >= 0 ? addedInterventions[matchingIndex] : null;
    const mergedQuantity = existingItem
      ? parseNumber(existingItem.quantity) + quantity
      : quantity;
    const mergedEstimatedCost = areaValue * mergedQuantity * unitCost;
    const payload = {
      master: selected.id,
      typology: component,
      vulnerability_type: vulnerabilityType,
      quantity: mergedQuantity,
      unit_cost_rs: unitCost,
      estimated_cost_rs: mergedEstimatedCost,
      status: "draft",
    };
    payload.village = villageId;

    try {
      if (editState.planItemId) {
        await updatePlanItem(editState.planItemId, payload);
      } else if (existingItem && existingItem.planItemId) {
        await updatePlanItem(existingItem.planItemId, payload);
      } else {
        await savePlanItem(payload);
      }
    } catch (error) {
      showError(error.message || gettext("Unable to save intervention."));
      return;
    }

    await loadPlanItems(villageId);
    resetInterventionFields();
    setSubmitMode(false);
    resetEditState();
    scrollToListing();
    warnRemainingBuildings();
  }

  function resetInterventionFields() {
    $mitigationIntervention.val("").trigger("change.select2");
    resetCostFields();
    setMitigationNote("");
  }

  function resetEditState() {
    editState = { index: null, planItemId: null };
  }

  function setSubmitMode(isEdit) {
    if (!$submitBtn.length) {
      return;
    }
    if (isEdit) {
      $submitBtn.text(gettext("Update"));
      $submitBtn.addClass("mitigation-update-btn");
    } else {
      $submitBtn.text(gettext("Save"));
      $submitBtn.removeClass("mitigation-update-btn");
    }
  }

  async function initMitigationForm() {
    initializeSelect2("theme", gettext("Select Theme"));
    initializeSelect2("subtheme", gettext("Select Sub-theme"));
    initializeSelect2("component", gettext("Select Component"));
    initializeSelect2("vulnerability_type", gettext("Select Vulnerability Type"));
    initializeSelect2("operations", gettext("Select Operation"));
    initializeSelect2("mitigation_intervention", gettext("Select Intervention"));

    await loadThemes();
    await loadSubthemes($theme.val());
    loadVulnerabilityOptions();
    await loadComponents($theme.val(), $subtheme.val());
    await refreshInterventions();
  }

  let villagesIndex = new Map();

  async function loadDistricts() {
    const districtRes = await fetch("/api/get_districts");
    const districtData = await districtRes.json();
    const $district = $("#district");
    $district.empty();
    $district.append(
      `<option value="" selected disabled>${gettext("Select Districts")}</option>`
    );
    districtData.forEach((district) => {
      $district.append(`<option value="${district.id}">${district.name}</option>`);
    });
    $district.trigger("change.select2");
  }

  async function loadCircles(districtId) {
    const $circle = $("#circle");
    $circle.empty();
    $circle.append(
      `<option value="" selected disabled>${gettext("Select Circle")}</option>`
    );
    if (!districtId) {
      $circle.trigger("change.select2");
      return;
    }
    const circleRes = await fetch(`/api/get_circles?district_id=${districtId}`);
    const circleData = await circleRes.json();
    circleData.forEach((circle) => {
      $circle.append(`<option value="${circle.id}">${circle.name}</option>`);
    });
    $circle.trigger("change.select2");
  }

  async function loadGramPanchayats(circleId) {
    const $gp = $("#gram_panchayat");
    $gp.empty();
    $gp.append(
      `<option value="" selected disabled>${gettext(
        "Select Gram Panchayat"
      )}</option>`
    );
    if (!circleId) {
      $gp.trigger("change.select2");
      return;
    }
    const gpRes = await fetch(`/api/get_gram_panchayats?circle_id=${circleId}`);
    const gpData = await gpRes.json();
    gpData.forEach((gp) => {
      $gp.append(`<option value="${gp.id}">${gp.name}</option>`);
    });
    $gp.trigger("change.select2");
  }

  async function loadAllVillages() {
    const villageRes = await fetch("/api/get_all_villages_public");
    const villageData = await villageRes.json();
    villagesIndex = new Map(
      villageData.map((village) => [String(village.id), village])
    );
    populateVillageOptions(villageData);
  }

  function populateVillageOptions(villageData) {
    const $village = $("#village");
    $village.empty();
    $village.append(
      `<option value="" selected disabled>${gettext("Select Villages")}</option>`
    );
    villageData.forEach((village) => {
      $village.append(
        `<option value="${village.id}">${village.name}</option>`
      );
    });
    $village.trigger("change.select2");
  }

  async function loadVillages(gramPanchayatId) {
    if (!gramPanchayatId) {
      await loadAllVillages();
      return;
    }
    const villageRes = await fetch(
      `/api/get_villages?gram_panchayat_id=${gramPanchayatId}`
    );
    const villageData = await villageRes.json();
    populateVillageOptions(villageData);
  }

  async function applyVillageSelection(villageId) {
    const record = villagesIndex.get(String(villageId));
    if (!record) {
      $("#district").val("").trigger("change.select2");
      $("#circle").val("").trigger("change.select2");
      $("#gram_panchayat").val("").trigger("change.select2");
      return;
    }

    $("#district").val(String(record.district_id)).trigger("change.select2");
    await loadCircles(record.district_id);
    $("#circle").val(String(record.circle_id)).trigger("change.select2");
    await loadGramPanchayats(record.circle_id);
    $("#gram_panchayat")
      .val(String(record.gram_panchayat_id))
      .trigger("change.select2");
  }

  async function initLocationSelectors() {
    const userVillageId = $("#userVillageId").val();

    initializeSelect2("district", gettext("Select Districts"));
    initializeSelect2("circle", gettext("Select Circle"));
    initializeSelect2("gram_panchayat", gettext("Select Gram Panchayat"));
    initializeSelect2("village", gettext("Select Villages"));

    await loadDistricts();
    await loadAllVillages();

    if (userVillageId) {
      $("#village").val(String(userVillageId)).trigger("change.select2");
      await applyVillageSelection(userVillageId);
    }

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

    $("#district").on("change", async () => {
      const districtId = $("#district").val();
      await loadCircles(districtId);
      $("#gram_panchayat").val("").trigger("change.select2");
      await loadVillages("");
    });

    $("#circle").on("change", async () => {
      const circleId = $("#circle").val();
      await loadGramPanchayats(circleId);
      await loadVillages("");
    });

    $("#gram_panchayat").on("change", async () => {
      const gpId = $("#gram_panchayat").val();
      await loadVillages(gpId);
    });
  }

  $(async () => {
    await initLocationSelectors();
    await initMitigationForm();

    await loadVulnerableAssets($("#village").val());

    $theme.on("change", async () => {
      const themeValue = $theme.val();
      await loadSubthemes(themeValue);
      await loadComponents($theme.val(), $subtheme.val());
      await refreshInterventions();
      await loadVulnerableAssets($("#village").val());
    });

    $subtheme.on("change", async () => {
      await loadComponents($theme.val(), $subtheme.val());
      await refreshInterventions();
      await loadVulnerableAssets($("#village").val());
    });

    $component.on("change", async () => {
      await refreshInterventions();
      updateTotalAvailableCount();
    });

    $vulnerabilityType.on("change select2:select", () => {
      updateOperationsOptions();
      updateMitigationOptions();
      updateTotalAvailableCount();
    });

    $operations.on("change", () => {
      updateMitigationOptions();
    });

    $mitigationIntervention.on("change", () => {
      applyInterventionDetails();
    });

    $quantity.on("input", () => {
      updateEstimatedCost();
      updateQuantityRemaining();
      validateQuantity();
    });

    $unit.on("input", () => {
      currentAreaValue = parseAreaValue($unit.val()) || currentAreaValue;
      updateEstimatedCost();
    });

    $("#addInterventionBtn").on("click", async (event) => {
      event.preventDefault();
      await addIntervention();
    });

    $(".add-intervention-btn").on("click", (event) => {
      event.preventDefault();
      resetInterventionFields();
      setSubmitMode(false);
      resetEditState();
    });

    $("#village").on("change", async () => {
      const villageId = $("#village").val();
      await applyVillageSelection(villageId);
      await loadPlanItems(villageId);
      await loadVulnerableAssets(villageId);
    });

    $("#warningModal").on("show.bs.modal", () => {
      updateWarningModal();
    });

    $("#reviewModal").on("show.bs.modal", () => {
      updateReviewModal();
      warnRemainingBuildings();
    });

    $("#warningConfirmBtn").on("click", () => {
      const warningModal = bootstrap.Modal.getInstance(
        document.getElementById("warningModal")
      );
      if (warningModal) {
        warningModal.hide();
      }
      const reviewModalEl = document.getElementById("reviewModal");
      if (!reviewModalEl) {
        return;
      }
      const reviewModal = new bootstrap.Modal(reviewModalEl);
      reviewModal.show();
    });

    $("#reviewConfirmBtn").on("click", async () => {
      const villageId = $("#village").val();
      try {
        await finalizePlanItems(villageId);
      } catch (error) {
        showError(error.message || gettext("Unable to submit mitigation."));
        return;
      }
      const reviewModal = bootstrap.Modal.getInstance(
        document.getElementById("reviewModal")
      );
      if (reviewModal) {
        reviewModal.hide();
      }
      if (window.Swal) {
        Swal.fire({
          icon: "success",
          text: gettext("Mitigation submitted successfully."),
        });
      } else {
        alert(gettext("Mitigation submitted successfully."));
      }
      await loadPlanItems(villageId);
      resetInterventionFields();
    });

    $addedBody.on("click", ".edit-intervention", async (event) => {
      event.preventDefault();
      const index = Number($(event.currentTarget).data("index"));
      if (!Number.isFinite(index)) {
        return;
      }
      const selectedItem = addedInterventions[index];
      if (!selectedItem) {
        return;
      }
      if (!selectedItem.planItemId) {
        showError(gettext("This item cannot be updated yet."));
        return;
      }
      editState = { index, planItemId: selectedItem.planItemId };
      setSubmitMode(true);
      await populateFormFromItem(selectedItem);
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
      updateQuantityRemaining();
    });
  });
})();

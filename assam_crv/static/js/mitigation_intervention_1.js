(() => {
  const langMatch = window.location.pathname.match(/^\/([a-z]{2})(\/|$)/);
  const langPrefix = langMatch ? `/${langMatch[1]}` : "";
  const apiBase = `${langPrefix}/api/mitigation`;
  const statusFilter = "active";
  const currencySymbol = "\u20b9";
  const addedInterventions = [];
  let currentInterventions = [];
  let totalAvailableCount = null;
  let mitigationTooltip = null;

  const $theme = $("#theme");
  const $subtheme = $("#subtheme");
  const $component = $("#component");
  const $operations = $("#operations");
  const $mitigationIntervention = $("#mitigation_intervention");
  const $unit = $("#unit");
  const $quantity = $("#quantity");
  const $unitCost = $("#unit_cost");
  const $estimatedCost = $("#estimated_cost");
  const $addedBody = $("#addedInterventionsBody");
  const $formSection = $(".mitigation-measures-section").first();
  const $submitBtn = $("#addInterventionBtn");
  const $vulnerableAssetsBody = $("#vulnerableAssetsBody");
  const $quantityRemaining = $("#quantity-remaining");
  const $unitLabel = $("label[for='unit']");
  const $vulnerableAssetsSection = $(".dummy-table-section").first();
  const $houseTypeFilter = $("#house_type_filter");
  const defaultUnitLabel = $unitLabel.text();
  let editState = { index: null, planItemId: null };
  let vulnerableAssetsData = [];
  let villagesIndex = new Map();

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

  function isHousingAsset(value) {
    const normalized = normalizeValue(value);
    return normalized.includes("housing") || normalized.includes("house");
  }

  function isHousingSubtheme(value) {
    const normalized = normalizeValue(value);
    return normalized.includes("housing") || normalized.includes("house");
  }

  function getAreaDisplay(master) {
    const areaValue = parseNumber(master.area);
    if (!areaValue) {
      return "";
    }
    const formatted = formatNumber(areaValue);
    return isHousingAsset(master.vulnerable_asset)
      ? `${formatted} Sqft`
      : formatted;
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
    updateQuantityRemaining();
    resetUnitLabel();
  }

  function resetUnitLabel() {
    if ($unitLabel.length) {
      $unitLabel.text(defaultUnitLabel);
    }
  }

  function setMitigationNote(note) {
    const text = note ? String(note).trim() : "";
    const select2 = $mitigationIntervention.data("select2");
    const $container = select2
      ? $mitigationIntervention.next(".select2")
      : $mitigationIntervention;
    const $selection = $container.find(".select2-selection");
    const $rendered = $container.find(".select2-selection__rendered");
    const $tooltipTarget = $rendered.length ? $rendered : $selection;

    $tooltipTarget.attr("title", text);
    $tooltipTarget.attr("data-bs-original-title", text);
    $tooltipTarget.attr("data-bs-toggle", "tooltip");
    if (window.bootstrap && window.bootstrap.Tooltip) {
      if (mitigationTooltip) {
        mitigationTooltip.dispose();
      }
      if (text) {
        mitigationTooltip = new bootstrap.Tooltip($tooltipTarget.get(0));
      } else {
        mitigationTooltip = null;
        $tooltipTarget.removeAttr("title");
        $tooltipTarget.removeAttr("data-bs-original-title");
        $tooltipTarget.removeAttr("data-bs-toggle");
      }
    }
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
    const areaDisplay = getAreaDisplay(selected);

    $unit.val(areaDisplay);
    $quantity.val("");
    $unitCost.val(formatNumber(unitCost));
    updateEstimatedCost();

    if (isHousingAsset(selected.vulnerable_asset)) {
      $unitLabel.text(`${defaultUnitLabel} (Sqft)`);
    } else {
      resetUnitLabel();
    }

    setMitigationNote(selected.display_note || "");
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

  function renderAddedInterventions() {
    $addedBody.empty();
    addedInterventions.forEach((item, index) => {
      const row = document.createElement("tr");
      const component = item.component || "-";
      const operation = item.operation || "-";
      const intervention = item.intervention || "-";
      const area = item.areaDisplay || "-";
      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${component}</td>
        <td>${operation}</td>
        <td>${intervention}</td>
        <td>${area}</td>
        <td>${formatNumber(item.quantity)}</td>
        <td>${formatNumber(item.unitCost)}</td>
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
        areaDisplay: getAreaDisplay(master),
        quantity,
        unitCost,
        estimatedCost,
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
  }

  function setHouseTypeOptions(rows) {
    const houseTypes = getUnique(rows.map((row) => row.house_type));
    $houseTypeFilter.empty();
    $houseTypeFilter.append(
      `<option value="">${gettext("All House Types")}</option>`
    );
    houseTypes.forEach((houseType) => {
      if (!houseType) {
        return;
      }
      const option = document.createElement("option");
      option.value = houseType;
      option.textContent = houseType;
      $houseTypeFilter.append(option);
    });
    $houseTypeFilter.trigger("change.select2");
  }

  function renderVulnerableAssets(rows) {
    $vulnerableAssetsBody.empty();
    const selectedHouseType = $houseTypeFilter.val();
    const filteredRows = selectedHouseType
      ? rows.filter((row) => row.house_type === selectedHouseType)
      : rows;
    if (!filteredRows || filteredRows.length === 0) {
      $vulnerableAssetsBody.append(
        `<tr><td colspan="3" class="text-muted">${gettext(
          "No data available."
        )}</td></tr>`
      );
      totalAvailableCount = null;
      updateQuantityRemaining();
      return;
    }

    totalAvailableCount = filteredRows.reduce(
      (sum, row) => sum + parseNumber(row.count),
      0
    );

    filteredRows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="text-left">${row.house_type || "-"}</td>
        <td>${row.hazard_type || "-"}</td>
        <td><span class="badge-blue">${formatNumber(row.count)}</span></td>
      `;
      $vulnerableAssetsBody.append(tr);
    });
    updateQuantityRemaining();
  }

  async function loadVulnerableAssets(villageId) {
    if (!isHousingSubtheme($subtheme.val())) {
      $vulnerableAssetsBody.empty();
      totalAvailableCount = null;
      updateQuantityRemaining();
      if ($vulnerableAssetsSection.length) {
        $vulnerableAssetsSection.hide();
      }
      return;
    }
    if ($vulnerableAssetsSection.length) {
      $vulnerableAssetsSection.show();
    }
    const query = buildQuery({ village_id: villageId });
    const data = await fetchJson(
      `${apiBase}/vulnerable-assets-summary/?${query}`
    );
    vulnerableAssetsData = Array.isArray(data) ? data : [];
    setHouseTypeOptions(vulnerableAssetsData);
    renderVulnerableAssets(vulnerableAssetsData);
  }

  function updateQuantityRemaining() {
    if (!$quantityRemaining.length) {
      return;
    }
    if (!Number.isFinite(totalAvailableCount)) {
      $quantityRemaining.text("");
      return;
    }
    const selectedQuantity = parseNumber($quantity.val());
    const remaining = Math.max(totalAvailableCount - selectedQuantity, 0);
    $quantityRemaining.text(`${formatNumber(remaining)} left`);
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
      if (editState.planItemId) {
        await updatePlanItem(editState.planItemId, payload);
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
  }

  function resetInterventionFields() {
    $mitigationIntervention.val("").trigger("change.select2");
    resetCostFields();
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
    initializeSelect2("operations", gettext("Select Operation"));
    initializeSelect2("mitigation_intervention", gettext("Select Intervention"));
    initializeSelect2("house_type_filter", gettext("All House Types"));

    await loadThemes();
    await loadSubthemes($theme.val());
    await loadComponents($theme.val(), $subtheme.val());
    await refreshInterventions();
  }

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
  }

  $(async () => {
    await initLocationSelectors();
    await initMitigationForm();

    await loadVulnerableAssets($("#village").val());

    $theme.on("change", async () => {
      await loadSubthemes($theme.val());
      await loadComponents($theme.val(), $subtheme.val());
      await refreshInterventions();
    });

    $subtheme.on("change", async () => {
      await loadComponents($theme.val(), $subtheme.val());
      await refreshInterventions();
      await loadVulnerableAssets($("#village").val());
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
    $mitigationIntervention.on("select2:select", () => {
      const selectedId = $mitigationIntervention.val();
      const selected = currentInterventions.find(
        (item) => String(item.id) === String(selectedId)
      );
      setMitigationNote(selected ? selected.display_note || "" : "");
      applyInterventionDetails();
    });

    $houseTypeFilter.on("change", () => {
      renderVulnerableAssets(vulnerableAssetsData);
    });

    $quantity.on("input", () => {
      updateEstimatedCost();
      updateQuantityRemaining();
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

    $("#reviewModal").on("show.bs.modal", () => {
      updateReviewModal();
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
    });
  });
})();

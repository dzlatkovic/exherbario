// Results-table import: assign columns, preview, review PubChem matches and confirm. Reopening resumes the import.
import {bindForm, bindRunFields, endpoint, find, node, request, runMetadata, selectOptions, status} from "./core.js";

// Long runs report progress and can be stopped between batches; whatever was done is kept.
const LOOKUP_BATCH = 5;
let stopRequested = false;
let busy = false;

const importId = find("import").dataset.import;
const studyId = find("import").dataset.study;

// Spreadsheet import -----------------------------------------------------------------------------------------

const IMPORT_ROLES = [
  ["ignore", "Ignore"], ["name", "Compound name"], ["sample", "Sample values"], ["sd", "SD of a sample"],
  ["rt", "RT (min)"], ["ri_exp", "Experimental RI"], ["ri_ref", "Reference RI"], ["ri_ref_source", "RI reference source"],
  ["id_basis", "Identification basis"], ["id_level", "Identification level"], ["cid", "PubChem CID"],
  ["cas", "CAS"], ["inchikey", "InChIKey"], ["n", "Replicates (n)"],
  ["library_match", "MS library match (GC-MS)"], ["library_score", "Library match score (GC-MS)"],
  ["mz_obs", "Observed m/z (LC-MS)"], ["adduct", "Adduct (LC-MS)"], ["mass_error_ppm", "Mass error, ppm (LC-MS)"],
  ["msms_match", "MS/MS match (LC-MS)"],
];
const importState = {record: null, sheets: [], columns: [], rowOverrides: {}, review: [], study: null};

function columnLetter(index) {
  let letters = "";
  for (let value = index + 1; value > 0; value = Math.floor((value - 1) / 26)) {
    letters = String.fromCharCode(65 + ((value - 1) % 26)) + letters;
  }
  return letters;
}

function cellText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function currentSheet() {
  return importState.sheets.find((sheet) => sheet.name === find("import-sheet").value) ?? importState.sheets[0];
}

function guessRole(header, previousRole) {
  const text = header.toLowerCase();
  if (!text) return "ignore";
  if (/^(no\.?|#|nr\.?|peak)$/.test(text)) return "ignore";
  // Evidence headers that also contain words like "name" or "match" come first.
  if (/m\/z|\bmz\b|precursor/.test(text)) return "mz_obs";
  if (/adduct|\bion\b/.test(text)) return "adduct";
  if (/ppm|mass error|mass accuracy|δ ?m|Δ ?m/i.test(text)) return "mass_error_ppm";
  if (/ms\/ms|msms|ms2|fragment/.test(text)) return "msms_match";
  const retentionIndex = /\b(ri|ki|ai|lri)\b|retention ind/.test(text);
  if (!retentionIndex && /score|\bsi\b|\brsi\b|match factor|similarity/.test(text)) return "library_score";
  if (!retentionIndex && /library|\bnist\b|wiley|\bhit\b/.test(text)) return "library_match";
  if (/^n$|replicates?|^n ?=/.test(text)) return "n";
  if (/compound|component|constituent|name/.test(text)) return "name";
  if (/\bcas\b/.test(text)) return "cas";
  if (/\bcid\b/.test(text)) return "cid";
  if (/inchikey/.test(text)) return "inchikey";
  if (/\b(sd|s\.d\.|std|±)\b|±/.test(text)) return previousRole === "sample" ? "sd" : "ignore";
  if (/\b(ri|ki|ai|lri)\b|retention ind/.test(text)) return /lit|ref|adams|nist/.test(text) ? "ri_ref" : "ri_exp";
  if (/\brt\b|retention time/.test(text)) return "rt";
  if (/ident|method of id/.test(text)) return "id_basis";
  if (/level|msi/.test(text)) return "id_level";
  return "sample";
}

function preparationOptions() {
  const samples = Object.fromEntries((importState.study?.samples ?? []).map((sample) => [sample.id, sample.code]));
  return (importState.study?.preparations ?? []).map((preparation) => ({
    id: preparation.id, label: `${samples[preparation.sample_id] ?? "?"} · ${preparation.batch_code}`,
  }));
}

function renderImportGrid() {
  const sheet = currentSheet();
  const headerRow = Number(find("import-header-row").value) || 1;
  const grid = find("import-grid");
  grid.replaceChildren();
  const width = Math.max(0, ...sheet.rows.map((row) => row.length));
  const head = grid.insertRow();
  head.append(node("th", "Row"), ...Array.from({length: width}, (_, index) => node("th", columnLetter(index))));
  sheet.rows.forEach((row, index) => {
    const line = grid.insertRow();
    if (index + 1 === headerRow) line.className = "header-row";
    const number = node("button", String(index + 1), "secondary");
    number.type = "button";
    number.title = "Use as header row";
    number.addEventListener("click", () => { find("import-header-row").value = index + 1; resetImportColumns(); });
    line.insertCell().append(number);
    for (let column = 0; column < width; column += 1) line.insertCell().textContent = cellText(row[column]);
  });
}

function resetImportColumns(fromTemplate = null) {
  const sheet = currentSheet();
  const header = sheet.rows[(Number(find("import-header-row").value) || 1) - 1] ?? [];
  let previous = null;
  importState.columns = header.map((value, index) => {
    const preset = fromTemplate?.columns.find((column) => column.index === index);
    const role = preset?.role ?? guessRole(cellText(value).trim(), previous);
    previous = role;
    return {index, header: cellText(value).trim() || columnLetter(index), role,
            sd_for: preset?.sd_for ?? (role === "sd" ? index - 1 : null), preparation_id: preset?.preparation_id ?? "",
            run_code: preset?.run_code ?? ""};
  });
  importState.rowOverrides = {};
  renderImportGrid();
  renderImportColumns();
}

function renderImportColumns() {
  const table = find("import-columns");
  table.replaceChildren();
  const head = table.insertRow();
  head.append(node("th", "Column"), node("th", "Header"), node("th", "Role"), node("th", "Details"));
  const samples = importState.columns.filter((column) => column.role === "sample");
  for (const column of importState.columns) {
    const row = table.insertRow();
    row.insertCell().textContent = columnLetter(column.index);
    row.insertCell().textContent = column.header;
    const role = document.createElement("select");
    for (const [value, text] of IMPORT_ROLES) role.append(new Option(text, value));
    role.value = column.role;
    role.addEventListener("change", () => {
      column.role = role.value;
      if (column.role === "sd" && column.sd_for === null) column.sd_for = column.index - 1;
      renderImportColumns();
    });
    row.insertCell().append(role);
    const details = row.insertCell();
    if (column.role === "sample") {
      const preparation = document.createElement("select");
      preparation.append(new Option("Match by sample code", ""));
      for (const option of preparationOptions()) preparation.append(new Option(option.label, option.id));
      preparation.value = column.preparation_id;
      preparation.addEventListener("change", () => { column.preparation_id = preparation.value; });
      const runCode = document.createElement("input");
      runCode.placeholder = `Run code (default ${column.header})`;
      runCode.maxLength = 80;
      runCode.value = column.run_code;
      runCode.addEventListener("input", () => { column.run_code = runCode.value; });
      details.append(preparation, runCode);
    } else if (column.role === "sd") {
      const pair = document.createElement("select");
      for (const sample of samples) pair.append(new Option(`SD of ${sample.header}`, sample.index));
      pair.value = column.sd_for ?? "";
      pair.addEventListener("change", () => { column.sd_for = Number(pair.value); });
      details.append(pair);
    }
  }
}

function importAssignment(form) {
  const data = new FormData(form);
  const value = (name) => (data.get(name) ?? "").trim();
  const settings = {
    technique: value("technique"), measurement_basis: value("measurement_basis"), unit: value("unit"),
    analytical_method: value("analytical_method"), run_metadata: runMetadata(form),
    ri_tolerance: Number(value("ri_tolerance") || 20),
  };
  if (value("ri_ref_polarity")) settings.ri_ref_polarity = value("ri_ref_polarity");
  const assignment = {
    sheet: value("sheet"), header_row: Number(value("header_row")), settings, row_overrides: importState.rowOverrides,
    columns: importState.columns.map((column) => {
      const entry = {index: column.index, role: column.role};
      if (column.role === "sample") {
        if (column.preparation_id) entry.preparation_id = column.preparation_id;
        if (column.run_code.trim()) entry.run_code = column.run_code.trim();
      }
      if (column.role === "sd") entry.sd_for = column.sd_for;
      return entry;
    }),
  };
  if (value("save_template")) assignment.save_template = value("save_template");
  return assignment;
}

function compoundCell(match) {
  const cell = document.createElement("td");
  if (!match) {
    cell.textContent = "No match";
    return cell;
  }
  const image = document.createElement("img");
  image.src = match.structure_image;
  image.alt = `Structure of ${match.title}`;
  image.loading = "lazy";
  const facts = node("div");
  facts.append(node("strong", match.title), node("div", `CID ${match.cid} · ${match.molecular_formula ?? ""}`
    + (match.monoisotopic_mass ? ` · ${Number(match.monoisotopic_mass).toFixed(4)}` : "")),
    node("div", match.inchikey ?? "", "break"), node("div", match.smiles ?? "", "break muted"));
  cell.append(image, facts);
  return cell;
}

async function reviewAction(number, body) {
  const record = importState.record;
  const updated = await request(`/api/chemistry/imports/${endpoint(record.id)}/rows/${number}/compound`,
    {method: "PUT", json: body});
  importState.review = importState.review.map((row) => row.row === updated.row ? updated : row);
  renderImportReview();
}

function renderImportReview() {
  const table = find("import-review");
  table.replaceChildren();
  const head = table.insertRow();
  head.append(node("th", "Row"), node("th", "Name in table"), node("th", "Status"), node("th", "Assigned compound"),
    node("th", "Change"));
  const methods = {alias: "your earlier choice", registry_name: "registry name", registry_synonym: "registry synonym",
    pubchem_name: "PubChem name search", cas: "CAS in table", cid: "CID in table", inchikey: "InChIKey in table",
    manual: "chosen", parent: "parent compound"};
  for (const item of importState.review) {
    const row = table.insertRow();
    row.insertCell().textContent = item.row;
    row.insertCell().textContent = item.name;
    const statusCell = row.insertCell();
    statusCell.className = `status-${item.status}`;
    statusCell.textContent = item.status.replace("_", " ") + (item.method ? ` (${methods[item.method] ?? item.method})` : "")
      + (item.problem ? ` — ${item.problem}` : "");
    row.append(compoundCell(item.status === "unidentified" ? null : item.match));
    const actions = row.insertCell();
    const button = (label, handler) => {
      const element = node("button", label, "secondary");
      element.type = "button";
      element.addEventListener("click", () => handler().catch((error) => { statusCell.textContent = error.message; }));
      actions.append(element);
    };
    if (item.match && item.status !== "confirmed") button("Accept", () => reviewAction(item.row, {action: "accept"}));
    if (item.candidates.length > 1) {
      const pick = document.createElement("select");
      for (const candidate of item.candidates) pick.append(new Option(`${candidate.title} (CID ${candidate.cid})`, candidate.cid));
      actions.append(pick);
      button("Use", () => reviewAction(item.row, {action: "choose", cid: Number(pick.value)}));
    }
    const namespace = document.createElement("select");
    for (const value of ["name", "cas", "cid", "inchikey"]) namespace.append(new Option(value, value));
    const query = document.createElement("input");
    query.placeholder = "Search PubChem";
    query.value = item.name;
    actions.append(namespace, query);
    button("Search", async () => {
      const found = await request(`/api/chemistry/compounds/search?namespace=${namespace.value}&q=${endpoint(query.value.trim())}`);
      if (!found.length) throw new Error("No PubChem match.");
      item.candidates = found;
      renderImportReview();
    });
    if (item.match && item.status !== "unidentified") button("Parent", () => reviewAction(item.row, {action: "parent"}));
    if (item.status !== "unidentified") button("Unidentified", () => reviewAction(item.row, {action: "unidentified"}));
  }
  const open = importState.review.filter((item) => !["confirmed", "unidentified"].includes(item.status)).length;
  find("import-confirm").disabled = open > 0 || !importState.ready || busy;
  status(find("import-confirm-status"), open ? `${open} rows still need a decision.` : "");
}

function renderImportPreview(result) {
  const preview = result.preview;
  importState.review = result.review;
  importState.ready = !preview.errors.length;
  find("import-preview").hidden = false;
  const problems = find("import-problems");
  problems.hidden = !preview.errors.length;
  problems.replaceChildren(...preview.errors.map((error) => node("p", error)));
  const notes = find("import-notes");
  notes.hidden = !preview.warnings.length;
  notes.replaceChildren(...preview.warnings.map((warning) => node("p", warning)));
  const labels = Object.fromEntries(preparationOptions().map((option) => [option.id, option.label]));
  const samples = find("import-samples");
  samples.replaceChildren();
  const head = samples.insertRow();
  head.append(node("th", "Column"), node("th", "Preparation"), node("th", "Run code"), node("th", "Detected"), node("th", "Total"));
  for (const profile of preview.profiles) {
    const row = samples.insertRow();
    for (const text of [profile.header, labels[profile.preparation_id] ?? "Not chosen", profile.run_code,
                        profile.detected, `${profile.total} ${profile.settings.unit}`]) row.insertCell().textContent = text;
  }
  const excluded = preview.rows.filter((row) => row.summary || !row.included);
  const list = find("import-excluded");
  list.replaceChildren(...(excluded.length ? [node("h3", "Summary and excluded rows")] : []), ...excluded.map((row) => {
    const label = node("label", ` Row ${row.row}: ${row.name}`);
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = row.included;
    box.addEventListener("change", () => {
      importState.rowOverrides[row.row] = box.checked;
      find("import-assign").requestSubmit();
    });
    label.prepend(box);
    return label;
  }));
  renderImportReview();
}

find("import-sheet").addEventListener("change", () => resetImportColumns());
find("import-header-row").addEventListener("change", () => resetImportColumns());
find("import-template").addEventListener("change", async (event) => {
  if (!event.target.value) return;
  const proposed = await request(`/api/chemistry/imports/${endpoint(importState.record.id)}/templates/${endpoint(event.target.value)}`);
  find("import-sheet").value = proposed.sheet;
  find("import-header-row").value = proposed.header_row;
  const form = find("import-assign");
  for (const [name, value] of Object.entries(proposed.settings)) {
    if (name === "run_metadata") {
      for (const [key, run] of Object.entries(value ?? {})) if (form.elements[`run.${key}`]) form.elements[`run.${key}`].value = run;
    } else if (form.elements[name] && value !== null) form.elements[name].value = value;
  }
  form.querySelector(".technique").dispatchEvent(new Event("change"));
  resetImportColumns(proposed);
  status(form.querySelector(".feedback"), proposed.missing_headers.length
    ? `Columns not found in this table: ${proposed.missing_headers.join(", ")}.` : "Layout applied. Check the sample columns.");
});
bindForm("import-assign", async (data, form) => {
  const result = await request(`/api/chemistry/imports/${endpoint(importState.record.id)}/assignment`,
    {method: "PUT", json: importAssignment(form)});
  renderImportPreview(result);
  if (result.preview.errors.length) find("import-problems").focus();
  return result.preview.errors.length ? "Preview has problems to fix." : "Preview ready. Review the compounds below.";
}, {fieldName: (path) => path.filter((part) => part !== "settings").join(".")});

function startProgress(total, label) {
  stopRequested = false;
  busy = true;
  for (const id of ["import-match", "import-accept-all", "import-confirm"]) find(id).disabled = true;
  find("import-stop").hidden = false;
  find("import-stop").disabled = false;
  find("import-progress").hidden = false;
  showProgress(0, total, label);
}

function showProgress(done, total, label) {
  const bar = find("import-progress-bar");
  bar.max = Math.max(total, 1);
  bar.value = done;
  find("import-progress-label").textContent = `${label}: ${done} of ${total}`;
}

function endProgress() {
  busy = false;
  for (const id of ["import-match", "import-accept-all"]) find(id).disabled = false;
  renderImportReview();  // sets Confirm from the rows still open
  find("import-stop").hidden = true;
  find("import-progress").hidden = true;
}

find("import-stop").addEventListener("click", () => {
  stopRequested = true;
  find("import-stop").disabled = true;
  find("import-progress-label").textContent += " · stopping after this batch…";
});

find("import-match").addEventListener("click", async () => {
  const feedback = find("import-match-status");
  status(feedback);
  const total = importState.review.filter((row) => row.status === "pending").length;
  if (!total) return status(feedback, "Every name has already been looked up.");
  startProgress(total, "Names looked up in PubChem");
  try {
    for (;;) {
      const result = await request(
        `/api/chemistry/imports/${endpoint(importState.record.id)}/match?limit=${LOOKUP_BATCH}`, {method: "POST"});
      importState.review = result.review;
      renderImportReview();
      showProgress(total - Math.min(result.pending, total), total, "Names looked up in PubChem");
      if (result.problem) return status(feedback, result.problem, true);
      if (!result.pending) return status(feedback, "All names looked up.");
      if (stopRequested) return status(feedback, `Stopped. ${result.pending} name${result.pending === 1 ? "" : "s"} left; look them up later from here.`);
    }
  } catch (error) {
    status(feedback, error.message, true);
  } finally {
    endProgress();
  }
});
find("import-accept-all").addEventListener("click", async () => {
  const feedback = find("import-match-status");
  status(feedback);
  const rows = importState.review.filter((row) => row.status === "needs_review" && row.match);
  if (!rows.length) return status(feedback, "No proposed matches are waiting.");
  startProgress(rows.length, "Matches accepted");
  let done = 0;
  try {
    for (const item of rows) {
      if (stopRequested) return status(feedback, `Stopped after ${done} of ${rows.length}.`);
      await reviewAction(item.row, {action: "accept"});
      showProgress(++done, rows.length, "Matches accepted");
    }
    status(feedback, `Accepted ${done} match${done === 1 ? "" : "es"}.`);
  } catch (error) {
    status(feedback, error.message, true);
  } finally {
    endProgress();
  }
});
find("import-confirm").addEventListener("click", async () => {
  const feedback = find("import-confirm-status");
  find("import-confirm").disabled = true;
  try {
    await request(`/api/chemistry/imports/${endpoint(importState.record.id)}/confirm`, {method: "POST"});
    window.location.assign(`/researcher/studies/${endpoint(studyId)}`);
  } catch (error) {
    status(feedback, error.message, true);
    find("import-confirm").disabled = false;
  }
});

function applySettings(form, settings) {
  for (const [name, value] of Object.entries(settings ?? {})) {
    if (name === "run_metadata") {
      for (const [key, run] of Object.entries(value ?? {})) if (form.elements[`run.${key}`]) form.elements[`run.${key}`].value = run;
    } else if (form.elements[name] && value !== null && value !== undefined) form.elements[name].value = value;
  }
  form.querySelector(".technique").dispatchEvent(new Event("change"));
}

async function startImport() {
  const form = find("import-assign");
  bindRunFields(form);
  const [record, study, templates] = await Promise.all([
    request(`/api/chemistry/imports/${endpoint(importId)}`), request(`/api/chemistry/studies/${endpoint(studyId)}`),
    request("/api/chemistry/import-templates")]);
  importState.record = record;
  importState.sheets = record.sheets;
  importState.study = study;
  if (record.status !== "draft") {
    find("import-work").hidden = true;
    const notice = find("import-status");
    notice.replaceChildren("This import was confirmed. ");
    const link = node("a", "Open the study");
    link.href = `/researcher/studies/${endpoint(studyId)}`;
    notice.append(link);
    notice.hidden = false;
    return;
  }
  selectOptions(find("import-template"), templates.map((template) => ({id: template.id, label: template.name})), "None");
  const saved = record.assignment;
  selectOptions(find("import-sheet"), record.sheets.map((sheet) => ({id: sheet.name, label: sheet.name})), "Select a sheet",
    saved?.sheet ?? record.sheets[0].name);
  if (saved) {
    find("import-header-row").value = saved.header_row;
    applySettings(form, saved.settings);
    if (saved.save_template) form.elements.save_template.value = saved.save_template;
    resetImportColumns(saved);
    importState.rowOverrides = Object.fromEntries(Object.entries(saved.row_overrides ?? {}));
    if (record.preview) renderImportPreview(record);
  } else {
    const firstHeader = record.sheets[0].rows.findIndex((row) => row.filter((cell) => cell !== null).length >= 2);
    find("import-header-row").value = Math.max(firstHeader, 0) + 1;
    resetImportColumns();
  }
}

startImport().catch((error) => {
  const notice = find("import-status");
  notice.textContent = error.message;
  notice.classList.add("warning");
  notice.hidden = false;
});

"use strict";

const find = (id) => document.getElementById(id);
const endpoint = (value) => encodeURIComponent(value);
const draftForm = find("save-draft");
const state = {
  token: null,
  curator: false,
  voucher: null,
  studies: [],
  study: null,
  draft: null,
  dirty: true,
  approval: null,
  sampleVouchers: [],
};
const VOUCHER_ROLES = [
  ["sampled_from_voucher", "Sampled from the voucher"],
  ["same_individual", "Same individual"],
  ["same_population", "Same population"],
  ["collected_alongside", "Collected alongside"],
  ["cultivated_from", "Cultivated from the voucher"],
  ["reference_for_commercial_material", "Reference for commercial material"],
];

function node(tag, text = "", className = "") {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

async function request(path, {method = "GET", json, multipart} = {}) {
  const headers = {};
  if (state.token) headers.Authorization = "Bearer " + state.token;
  if (json !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {
    method,
    headers,
    body: multipart ?? (json === undefined ? undefined : JSON.stringify(json)),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = result.detail;
    const message = Array.isArray(detail)
      ? detail.map((error) => `${error.loc.slice(1).join(" ")} ${error.msg}`).join(". ")
      : detail;
    throw new Error(message || `Request failed (HTTP ${response.status}).`);
  }
  return result;
}

function status(element, message = "", error = false) {
  element.textContent = message;
  element.toggleAttribute("data-error", error);
}

function bindForm(id, handler) {
  const form = find(id);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button:not([type='button'])");
    const feedback = form.querySelector(".feedback");
    submit.disabled = true;
    status(feedback, "Working…");
    try {
      const message = await handler(new FormData(form), form);
      status(feedback, message);
    } catch (error) {
      status(feedback, error.message || "Request failed.", true);
    } finally {
      submit.disabled = false;
      updateReview();
    }
  });
}

function selectOptions(select, options, placeholder, value = "") {
  select.replaceChildren(new Option(placeholder, ""), ...options.map(({label, id}) => new Option(label, id)));
  select.value = value;
}

function requiredSelection(value, message) {
  if (!value) throw new Error(message);
  return value;
}

function renderRunFields(form) {
  const technique = form.querySelector(".technique").value;
  const kind = technique.startsWith("GC") ? "gc" : "lc";
  for (const field of form.querySelectorAll(".run-fields [data-for]")) field.hidden = field.dataset.for !== kind;
}

function runMetadata(form) {
  const run = {};
  for (const field of form.querySelectorAll(".run-fields label:not([hidden]) [name^='run.']")) {
    if (field.value.trim()) run[field.name.slice(4)] = field.value.trim();
  }
  return run;
}

function voucherLabel(voucher) {
  return voucher.accession || voucher.reg_no || voucher.specimen_id;
}

function renderSampleVouchers() {
  const rows = state.sampleVouchers.map((link, index) => {
    const row = node("div", "", "credit-row");
    const voucher = link.voucher;
    row.append(node("p", [voucher.subnomen, voucherLabel(voucher)].filter(Boolean).join(" · ")));
    const label = node("label", "Role");
    const role = document.createElement("select");
    for (const [value, text] of VOUCHER_ROLES) role.append(new Option(text, value));
    role.value = link.role;
    role.addEventListener("change", () => { link.role = role.value; });
    label.append(role);
    const remove = node("button", "Remove", "secondary");
    remove.type = "button";
    remove.addEventListener("click", () => { state.sampleVouchers.splice(index, 1); renderSampleVouchers(); });
    row.append(label, remove);
    return row;
  });
  find("sample-vouchers").replaceChildren(...rows);
  const site = find("create-sample").elements.site_specimen_id;
  selectOptions(site, state.sampleVouchers.map(({voucher}) => ({id: voucher.specimen_id, label: voucherLabel(voucher)})),
    "Select a linked voucher", site.value);
}

function renderSiteFields() {
  const site = find("sample-site").value;
  find("site-voucher-field").hidden = site !== "voucher";
  find("site-location-field").hidden = site !== "field_location";
}

function renderSampleNotice() {
  const sample = (state.study?.samples ?? []).find((item) => item.id === find("choose-sample").value);
  const changed = (sample?.vouchers ?? []).filter((link) => link.redetermined);
  const notice = find("sample-notice");
  notice.hidden = !changed.length;
  notice.replaceChildren(...changed.map((link) => {
    const before = link.determination_at_link, now = link.current_determination;
    const name = (value) => value.name_as_recorded || value.taxon_name || "undetermined";
    return node("p", `Voucher ${link.accession || link.reg_no || link.specimen_id} was redetermined after this sample `
      + `was linked. Recorded then: ${name(before)}. Now: ${name(now)}`);
  }));
}

function voucherSelected(voucher) {
  state.voucher = voucher;
  const number = voucher.accession || voucher.reg_no;
  const description = [voucher.subnomen, voucher.holding_institution, voucher.collection, number].filter(Boolean);
  find("voucher-selection").textContent = `${description.join(" · ") || "Voucher selected"} — ${voucher.specimen_id}`;
  find("find-voucher").elements.specimen_id.value = voucher.specimen_id;
}

function renderStudies(selected = "") {
  selectOptions(find("choose-study"), state.studies.map((study) => ({id: study.id, label: study.title})),
    "Select a study", selected);
}

function renderStudy(sampleId = "", preparationId = "") {
  find("study-work").hidden = !state.study;
  for (const format of ["long", "wide"]) {
    find(`export-${format}`).href = state.study
      ? `/api/chemistry/public/export?study_id=${endpoint(state.study.id)}&format=${format}` : "#";
  }
  const samples = state.study?.samples ?? [];
  selectOptions(find("choose-sample"), samples.map((sample) => ({
    id: sample.id,
    label: [sample.code, ...(sample.vouchers ?? []).map(voucherLabel)].join(" · ")
      + (sample.redetermined ? " · voucher redetermined" : ""),
  })), "Select a sample", sampleId);
  renderPreparations(preparationId);
  renderSampleNotice();
  const profiles = state.study?.profiles ?? [];
  selectOptions(find("choose-profile"), profiles.map((profile) => ({
    id: profile.id,
    label: `${profile.run_code} · ${profile.source_name}` + (profile.redetermined ? " · voucher redetermined" : ""),
  })), "Select a profile");
  find("profile-picker").hidden = !profiles.length;
}

function renderPreparations(selected = "") {
  const sampleId = find("choose-sample").value;
  const preparations = (state.study?.preparations ?? []).filter((preparation) => preparation.sample_id === sampleId);
  selectOptions(find("choose-preparation"), preparations.map((preparation) => ({
    id: preparation.id,
    label: preparation.batch_code,
  })), "Select a preparation", selected);
}

function clearPreview() {
  state.approval = null;
  find("publish").reset();
  find("preview").hidden = true;
}

function updateReview() {
  find("validate").querySelector("button").disabled = !state.draft?.draft_revision || state.dirty;
  find("publish").querySelector("button").disabled = !state.approval || !state.curator;
}

function markDirty() {
  state.dirty = true;
  clearPreview();
  updateReview();
}

function idList(field) {
  return [...new Set(draftForm.elements[field].value.split(/[\s,]+/).filter(Boolean))];
}

function profileIds() {
  return idList("profile_ids");
}

function attachProfile(id) {
  draftForm.elements.profile_ids.value = [...new Set([...profileIds(), id])].join("\n");
  markDirty();
}

function addCredit(credit = {}) {
  const row = node("div", "", "credit-row");
  for (const [name, value] of [["Name", credit.name], ["Role", credit.role], ["ORCID", credit.orcid]]) {
    const label = node("label", name);
    const input = node("input");
    input.value = value ?? "";
    input.maxLength = 200;
    input.dataset.credit = name.toLowerCase();
    label.append(input);
    row.append(label);
  }
  const remove = node("button", "Remove", "secondary");
  remove.type = "button";
  remove.addEventListener("click", () => { row.remove(); markDirty(); });
  row.append(remove);
  find("credit-rows").append(row);
}

function draftPayload(data) {
  const metadata = Object.fromEntries(data);
  metadata.contributors = [...find("credit-rows").children].map((row) => ({
    name: row.querySelector("[data-credit='name']").value.trim(),
    role: row.querySelector("[data-credit='role']").value.trim(),
    orcid: row.querySelector("[data-credit='orcid']").value.trim() || null,
  })).filter((credit) => credit.name || credit.role || credit.orcid);
  if (metadata.contributors.some((credit) => !credit.name || !credit.role)) {
    throw new Error("Each contributor needs both a name and a role.");
  }
  metadata.profile_ids = profileIds();
  metadata.specimen_ids = idList("specimen_ids");
  metadata.include_determiner_names = data.has("include_determiner_names");
  metadata.include_collector_names = data.has("include_collector_names");
  for (const name of ["title", "license", "correction_reason"]) {
    metadata[name] = metadata[name]?.trim() || null;
  }
  return metadata;
}

function setDraft(draft, loadFields) {
  state.draft = draft;
  state.dirty = false;
  clearPreview();
  const form = draftForm;
  form.elements.institution.value = draft.institution;
  form.elements.institution.readOnly = true;
  find("open-draft").elements.deposition_id.value = draft.id;
  const version = draft.latest_version ? ` · Published version ${draft.latest_version}` : "";
  find("draft-selection").textContent = `${draft.institution} ${draft.accession}${version} — Deposition ID ${draft.id}`;
  find("new-draft").hidden = false;
  find("correction-field").hidden = !draft.latest_version;
  form.elements.correction_reason.required = Boolean(draft.latest_version);
  if (loadFields) {
    const data = draft.draft ?? {};
    for (const field of ["title", "license", "description", "rights_statement", "correction_reason"]) {
      form.elements[field].value = data[field] ?? "";
    }
    form.elements.profile_ids.value = (data.profile_ids ?? []).join("\n");
    form.elements.specimen_ids.value = (data.specimen_ids ?? []).join("\n");
    form.elements.include_determiner_names.checked = data.include_determiner_names ?? false;
    form.elements.include_collector_names.checked = data.include_collector_names ?? false;
    find("credit-rows").replaceChildren();
    for (const credit of (data.contributors?.length ? data.contributors : [{}])) addCredit(credit);
  }
  updateReview();
}

async function refreshInputs() {
  const panel = find("release-inputs");
  panel.replaceChildren();
  status(find("inputs-status"));
  if (!state.draft?.draft_revision) return;
  const draftId = state.draft.id;
  try {
    const result = await request(`/api/depositions/${endpoint(draftId)}/draft/inputs`);
    if (state.draft?.id !== draftId) return;
    if (result.unavailable) {
      status(find("inputs-status"), `${result.unavailable} selected profile(s) or voucher(s) are unavailable.`, true);
    } else if (result.inputs.length || result.vouchers?.length) {
      status(find("inputs-status"), "Release prerequisites");
    }
    for (const voucher of result.vouchers ?? []) panel.append(renderVoucher(voucher));
    for (const entry of result.inputs) panel.append(renderInput(entry));
  } catch (error) {
    status(find("inputs-status"), error.message, true);
  }
}

function releaseButton(label, path, data) {
  const button = node("button", label, "secondary");
  button.type = "button";
  button.addEventListener("click", async () => {
    const dialog = find("confirm-release");
    find("confirm-title").textContent = label;
    dialog.returnValue = "";
    const response = new Promise((resolve) => {
      dialog.addEventListener("close", () => resolve(dialog.returnValue), {once: true});
    });
    dialog.showModal();
    if (await response !== "release") return;
    button.disabled = true;
    clearPreview();
    try {
      await request(path, {method: "PUT", json: data()});
      await refreshInputs();
    } catch (error) {
      status(find("inputs-status"), error.message, true);
    } finally {
      button.disabled = false;
      updateReview();
    }
  });
  return button;
}

function voucherRelease(voucher, controls) {
  const location = node("label", "Public locality");
  const choice = node("select");
  choice.append(new Option("Withheld", "withheld"), new Option("Country and region", "region"));
  choice.value = voucher.public_location === "region" ? "region" : "withheld";
  location.append(choice);
  controls.append(location, releaseButton("Release voucher", `/api/specimen/${endpoint(voucher.id)}/visibility`,
    () => ({is_public: true, public_location: choice.value})));
}

function renderVoucher(voucher) {
  const card = node("article", "", "requirement");
  card.append(node("h3", [voucher.name, voucher.accession].filter(Boolean).join(" · ") || voucher.id),
    node("p", `Voucher · ${voucher.is_public ? "Released" : "Private"}`));
  if (state.curator && !voucher.is_public) {
    const controls = node("div", "", "requirement-actions");
    voucherRelease(voucher, controls);
    card.append(controls);
  }
  return card;
}

function renderInput({profile, study, voucher}) {
  const card = node("article", "", "requirement");
  const visibility = (item) => item.is_public ? "Released" : "Private";
  card.append(
    node("h3", profile.name),
    node("p", `Voucher ${[voucher.name, voucher.accession].filter(Boolean).join(" · ") || voucher.id} · ${visibility(voucher)}`),
    node("p", `Study ${study.title} · ${visibility(study)}`),
    node("p", `Profile · ${visibility(profile)}`),
  );
  if (!state.curator) return card;
  const controls = node("div", "", "requirement-actions");
  if (!voucher.is_public) voucherRelease(voucher, controls);
  for (const [item, label, group] of [[study, "study", "studies"], [profile, "profile", "profiles"]]) {
    if (!item.is_public) {
      controls.append(releaseButton(`Release ${label}`, `/api/chemistry/${group}/${endpoint(item.id)}/visibility`,
        () => ({is_public: true})));
    }
  }
  if (controls.children.length) card.append(controls);
  return card;
}

bindForm("login", async (data, form) => {
  const login = await request("/api/users/login", {method: "POST", json: Object.fromEntries(data)});
  state.token = login.access_token;
  let details;
  try {
    details = await request("/api/chemistry/studies");
  } catch (error) {
    state.token = null;
    throw error;
  }
  state.curator = details.can_publish;
  state.studies = details.studies;
  renderStudies();
  for (const control of document.querySelectorAll(".curator-only")) control.hidden = !state.curator;
  find("role").textContent = state.curator ? "Curator" : "Researcher";
  form.reset();
  find("sign-in").hidden = true;
  find("session").hidden = false;
  find("workspace").hidden = false;
  find("find-voucher").elements.specimen_id.focus();
});

find("sign-out").addEventListener("click", () => window.location.reload());
bindForm("find-voucher", async (data) => {
  voucherSelected(await request(`/api/specimen/get-specimen-by-id?specimen_id=${endpoint(data.get("specimen_id").trim())}`));
  return "Voucher linked to this workspace.";
});
bindForm("register", async (data, form) => {
  const payload = Object.fromEntries([...data].filter(([, value]) => value.trim()));
  voucherSelected(await request("/api/specimen/create-new-specimen", {method: "POST", json: payload}));
  form.reset();
  return "Voucher registered.";
});

find("choose-study").addEventListener("change", async (event) => {
  const id = event.target.value;
  state.study = null;
  renderStudy();
  status(find("study-feedback"), id ? "Loading study…" : "");
  if (!id) return;
  try {
    const study = await request(`/api/chemistry/studies/${endpoint(id)}`);
    if (find("choose-study").value !== id) return;
    state.study = study;
    renderStudy();
    status(find("study-feedback"));
  } catch (error) {
    if (find("choose-study").value === id) status(find("study-feedback"), error.message, true);
  }
});
bindForm("create-study", async (data, form) => {
  const study = await request("/api/chemistry/studies", {method: "POST", json: Object.fromEntries(data)});
  state.studies.push(study);
  state.study = {...study, samples: [], preparations: [], profiles: []};
  renderStudies(study.id);
  renderStudy();
  form.reset();
  return "Study created.";
});
find("choose-sample").addEventListener("change", () => { renderPreparations(); renderSampleNotice(); });
find("add-sample-voucher").addEventListener("click", () => {
  const feedback = find("create-sample").querySelector(".feedback");
  if (!state.voucher) return status(feedback, "Use a voucher in the Voucher section first.", true);
  if (state.sampleVouchers.some(({voucher}) => voucher.specimen_id === state.voucher.specimen_id)) {
    return status(feedback, "That voucher is already in the list.", true);
  }
  const role = state.sampleVouchers.length ? "same_population" : "sampled_from_voucher";
  state.sampleVouchers.push({voucher: state.voucher, role});
  renderSampleVouchers();
  status(feedback);
});
find("sample-site").addEventListener("change", renderSiteFields);
bindForm("create-sample", async (data, form) => {
  const study = requiredSelection(state.study, "Select a study first.");
  if (!state.sampleVouchers.length) throw new Error("Add at least one voucher to the sample.");
  const site = data.get("site");
  const payload = Object.fromEntries([...data].filter(([name, value]) =>
    !["site", "site_specimen_id", "field_loc_id"].includes(name) && value.trim()));
  if (site === "voucher") payload.site_specimen_id = requiredSelection(data.get("site_specimen_id"), "Select the site voucher.");
  if (site === "field_location") payload.field_loc_id = requiredSelection(data.get("field_loc_id").trim(), "Enter a field location ID.");
  payload.vouchers = state.sampleVouchers.map(({voucher, role}) => ({specimen_id: voucher.specimen_id, role}));
  await request(`/api/chemistry/studies/${endpoint(study.id)}/samples`, {method: "POST", json: payload});
  const refreshed = await request(`/api/chemistry/studies/${endpoint(study.id)}`);
  if (state.study === study) {
    state.study = refreshed;
    renderStudy(refreshed.samples.find((sample) => sample.code === payload.code.trim())?.id ?? "");
  }
  form.reset();
  state.sampleVouchers = [];
  renderSampleVouchers();
  renderSiteFields();
  return "Sample added.";
});
bindForm("create-preparation", async (data, form) => {
  const study = requiredSelection(state.study, "Select a study first.");
  const sampleId = requiredSelection(find("choose-sample").value, "Select a sample first.");
  const payload = Object.fromEntries([...data].filter(([, value]) => value.trim()));
  const preparation = await request(`/api/chemistry/samples/${endpoint(sampleId)}/preparations`,
    {method: "POST", json: payload});
  study.preparations.push({...payload, ...preparation, sample_id: sampleId});
  if (state.study === study) renderStudy(sampleId, preparation.id);
  form.reset();
  return "Preparation saved.";
});
for (const form of document.querySelectorAll("form")) {
  const technique = form.querySelector(".technique");
  if (technique) {
    technique.addEventListener("change", () => renderRunFields(form));
    renderRunFields(form);
  }
}
find("measurement-basis").addEventListener("change", (event) => {
  find("upload").elements.unit.value = event.target.value === "peak_area_percent" ? "%" : "";
});
bindForm("upload", async (data, form) => {
  const study = requiredSelection(state.study, "Select a study first.");
  const sampleId = find("choose-sample").value;
  const preparationId = requiredSelection(find("choose-preparation").value, "Select a preparation first.");
  for (const name of [...data.keys()].filter((key) => key.startsWith("run."))) data.delete(name);
  data.set("run_metadata", JSON.stringify(runMetadata(form)));
  const profile = await request(`/api/chemistry/preparations/${endpoint(preparationId)}/profiles`,
    {method: "POST", multipart: data});
  const warnings = find("upload-warnings");
  warnings.hidden = !profile.warnings?.length;
  warnings.textContent = (profile.warnings ?? []).join(" ");
  study.profiles.push(profile);
  attachProfile(profile.id);
  if (state.study === study) renderStudy(sampleId, preparationId);
  form.elements.file.value = "";
  form.elements.run_code.value = "";
  return "CSV validated, original saved, and profile added to the draft form.";
});

addCredit();
find("add-credit").addEventListener("click", () => { addCredit(); markDirty(); });
draftForm.addEventListener("input", markDirty);
find("attach-profile").addEventListener("click", () => {
  const id = find("choose-profile").value;
  if (id) attachProfile(id);
});
bindForm("open-draft", async (data) => {
  const draft = await request(`/api/depositions/${endpoint(data.get("deposition_id").trim())}/draft`);
  setDraft(draft, true);
  await refreshInputs();
  return draft.draft ? "Draft opened." : "Deposition opened. Save a new draft to prepare a correction.";
});
find("new-draft").addEventListener("click", () => {
  state.draft = null;
  draftForm.reset();
  draftForm.elements.institution.readOnly = false;
  draftForm.elements.correction_reason.required = false;
  find("correction-field").hidden = true;
  find("new-draft").hidden = true;
  find("draft-selection").textContent = "New deposition";
  find("open-draft").reset();
  find("open-draft").querySelector(".feedback").textContent = "";
  find("credit-rows").replaceChildren();
  addCredit();
  find("publication-result").hidden = true;
  markDirty();
  void refreshInputs();
  draftForm.elements.institution.focus();
});
bindForm("save-draft", async (data) => {
  const payload = draftPayload(data);
  const existing = state.draft;
  if (existing) {
    delete payload.institution;
    payload.expected_revision = existing.draft_revision;
  }
  const draft = await request(existing ? `/api/depositions/${endpoint(existing.id)}/draft` : "/api/depositions",
    {method: existing ? "PUT" : "POST", json: payload});
  setDraft(draft, false);
  find("publication-result").hidden = true;
  await refreshInputs();
  return "Draft saved.";
});
bindForm("validate", async () => {
  const draft = requiredSelection(state.draft, "Save a draft first.");
  const preview = await request(`/api/depositions/${endpoint(draft.id)}/draft/preview`);
  if (state.dirty || state.draft !== draft) throw new Error("The draft changed. Save and preview it again.");
  state.approval = {draft_revision: preview.draft_revision, snapshot_sha256: preview.snapshot_sha256};
  const snapshot = preview.snapshot;
  const summary = find("preview-summary");
  const profiles = node("ul");
  for (const profile of snapshot.profiles) {
    profiles.append(node("li", `${profile.file.name} · ${profile.analytical_method} · ${profile.unit}`));
  }
  for (const voucher of snapshot.vouchers ?? []) {
    if (!snapshot.profiles.some((profile) => profile.voucher.id === voucher.id)) {
      profiles.append(node("li", `Voucher ${voucher.accession ?? voucher.reg_no ?? voucher.id}`));
    }
  }
  summary.replaceChildren(node("h4", snapshot.title),
    node("p", `${snapshot.institution_name} · Version ${snapshot.version} · ${snapshot.license}`), profiles,
    node("p", `Identifier ${snapshot.identifier}`, "break"),
    node("p", `Snapshot SHA-256 ${preview.snapshot_sha256}`, "break"));
  find("preview-json").textContent = JSON.stringify(snapshot, null, 2);
  find("preview").hidden = false;
  find("awaiting-curator").hidden = state.curator;
  return "Validation passed.";
});
bindForm("publish", async () => {
  const approval = requiredSelection(state.approval, "Validate and preview the saved draft first.");
  const result = await request(`/api/depositions/${endpoint(state.draft.id)}/publish`, {method: "POST", json: approval});
  setDraft({...state.draft, latest_version: result.version, draft_revision: null, draft: null}, false);
  await refreshInputs();
  const message = find("publication-result");
  const link = node("a", `Open published version ${result.version}`);
  link.href = result.url.replace("/api/depositions/public/", "/depositions/");
  message.replaceChildren(link);
  message.hidden = false;
});

// Spreadsheet import -----------------------------------------------------------------------------------------

const IMPORT_ROLES = [
  ["ignore", "Ignore"], ["name", "Compound name"], ["sample", "Sample values"], ["sd", "SD of a sample"],
  ["rt", "RT (min)"], ["ri_exp", "Experimental RI"], ["ri_ref", "Reference RI"], ["ri_ref_source", "RI reference source"],
  ["id_basis", "Identification basis"], ["id_level", "Identification level"], ["cid", "PubChem CID"],
  ["cas", "CAS"], ["inchikey", "InChIKey"],
];
const importState = {record: null, sheets: [], columns: [], rowOverrides: {}, review: []};

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
  const samples = Object.fromEntries((state.study?.samples ?? []).map((sample) => [sample.id, sample.code]));
  return (state.study?.preparations ?? []).map((preparation) => ({
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
  find("import-confirm").disabled = open > 0 || !importState.ready;
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

bindForm("import-upload", async (data, form) => {
  const study = requiredSelection(state.study, "Select a study first.");
  const record = await request(`/api/chemistry/studies/${endpoint(study.id)}/imports`, {method: "POST", multipart: data});
  importState.record = record;
  importState.sheets = record.sheets;
  selectOptions(find("import-sheet"), record.sheets.map((sheet) => ({id: sheet.name, label: sheet.name})), "Select a sheet",
    record.sheets[0].name);
  const firstHeader = record.sheets[0].rows.findIndex((row) => row.filter((cell) => cell !== null).length >= 2);
  find("import-header-row").value = Math.max(firstHeader, 0) + 1;
  const templates = await request("/api/chemistry/import-templates");
  selectOptions(find("import-template"), templates.map((template) => ({id: template.id, label: template.name})), "None");
  find("import-assign").hidden = false;
  find("import-preview").hidden = true;
  resetImportColumns();
  form.reset();
  return `Uploaded ${record.source_name}. Choose the header row and assign the columns.`;
});
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
  renderRunFields(form);
  resetImportColumns(proposed);
  status(form.querySelector(".feedback"), proposed.missing_headers.length
    ? `Columns not found in this table: ${proposed.missing_headers.join(", ")}.` : "Layout applied. Check the sample columns.");
});
bindForm("import-assign", async (data, form) => {
  const result = await request(`/api/chemistry/imports/${endpoint(importState.record.id)}/assignment`,
    {method: "PUT", json: importAssignment(form)});
  renderImportPreview(result);
  return result.preview.errors.length ? "Preview has problems to fix." : "Preview ready. Review the compounds below.";
});
find("import-match").addEventListener("click", async () => {
  const feedback = find("import-match-status");
  try {
    for (;;) {
      const result = await request(`/api/chemistry/imports/${endpoint(importState.record.id)}/match`, {method: "POST"});
      importState.review = result.review;
      renderImportReview();
      if (result.problem) return status(feedback, result.problem, true);
      status(feedback, result.pending ? `Looking up… ${result.pending} names left.` : "All names looked up.");
      if (!result.pending) return;
    }
  } catch (error) {
    status(feedback, error.message, true);
  }
});
find("import-accept-all").addEventListener("click", async () => {
  for (const item of importState.review.filter((row) => row.status === "needs_review" && row.match)) {
    await reviewAction(item.row, {action: "accept"}).catch((error) => status(find("import-match-status"), error.message, true));
  }
});
find("import-confirm").addEventListener("click", async () => {
  const feedback = find("import-confirm-status");
  try {
    const result = await request(`/api/chemistry/imports/${endpoint(importState.record.id)}/confirm`, {method: "POST"});
    const study = await request(`/api/chemistry/studies/${endpoint(state.study.id)}`);
    state.study = study;
    renderStudy();
    find("import-assign").hidden = true;
    find("import-preview").hidden = true;
    status(find("import-upload").querySelector(".feedback"),
      `Imported ${result.profiles.length} profiles: ${result.profiles.map((profile) => profile.run_code).join(", ")}.`);
  } catch (error) {
    status(feedback, error.message, true);
  }
});

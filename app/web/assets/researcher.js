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
};

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
  const samples = state.study?.samples ?? [];
  selectOptions(find("choose-sample"), samples.map((sample) => ({
    id: sample.id,
    label: `${sample.code} · ${sample.accession || sample.reg_no || sample.specimen_id}`,
  })), "Select a sample", sampleId);
  renderPreparations(preparationId);
  const profiles = state.study?.profiles ?? [];
  selectOptions(find("choose-profile"), profiles.map((profile) => ({
    id: profile.id,
    label: `${profile.run_code} · ${profile.source_name}`,
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
find("choose-sample").addEventListener("change", () => renderPreparations());
bindForm("create-sample", async (data, form) => {
  const voucher = requiredSelection(state.voucher, "Select a voucher first.");
  const study = requiredSelection(state.study, "Select a study first.");
  const payload = {...Object.fromEntries(data), specimen_id: voucher.specimen_id};
  const sample = await request(`/api/chemistry/studies/${endpoint(study.id)}/samples`, {method: "POST", json: payload});
  study.samples.push({...payload, ...sample, accession: voucher.accession, reg_no: voucher.reg_no});
  if (state.study === study) renderStudy(sample.id);
  form.reset();
  return "Sample linked.";
});
bindForm("create-preparation", async (data, form) => {
  const study = requiredSelection(state.study, "Select a study first.");
  const sampleId = requiredSelection(find("choose-sample").value, "Select a sample first.");
  const payload = Object.fromEntries(data);
  const preparation = await request(`/api/chemistry/samples/${endpoint(sampleId)}/preparations`,
    {method: "POST", json: payload});
  study.preparations.push({...payload, ...preparation, sample_id: sampleId});
  if (state.study === study) renderStudy(sampleId, preparation.id);
  form.reset();
  return "Preparation saved.";
});
find("measurement-basis").addEventListener("change", (event) => {
  find("upload").elements.unit.value = event.target.value === "peak_area_percent" ? "%" : "";
});
bindForm("upload", async (data, form) => {
  const study = requiredSelection(state.study, "Select a study first.");
  const sampleId = find("choose-sample").value;
  const preparationId = requiredSelection(find("choose-preparation").value, "Select a preparation first.");
  const profile = await request(`/api/chemistry/preparations/${endpoint(preparationId)}/profiles`,
    {method: "POST", multipart: data});
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

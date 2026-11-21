// Deposition page: edit the draft, release its records, preview the public snapshot and (curators) publish.
import {VOUCHER_ROLES, bindForm, endpoint, find, node, request, requiredSelection, selectOptions, status, voucherLabel,
        voucherPicker} from "./core.js";

const page = find("deposition");
const draftForm = find("save-draft");
const state = {draft: null, dirty: true, approval: null, curator: page.dataset.curator === "true"};
const names = new Map();

function ensureInstitution(code) {
  const select = draftForm.elements.institution;
  if (![...select.options].some((option) => option.value === code)) select.append(new Option(code, code));
}

async function nameOf(kind, id) {
  const key = `${kind}:${id}`;
  if (!names.has(key)) {
    names.set(key, (async () => {
      try {
        if (kind === "profile") {
          const profile = await request(`/api/chemistry/profiles/${endpoint(id)}`);
          return `Run ${profile.run_code} · ${profile.technique ?? profile.analytical_method}`;
        }
        const voucher = await request(`/api/specimen/get-specimen-by-id?specimen_id=${endpoint(id)}`);
        return [voucher.subnomen, voucherLabel(voucher)].filter(Boolean).join(" · ");
      } catch {
        return `Unavailable record ${id}`;
      }
    })());
  }
  return names.get(key);
}

function renderList(list, field, kind) {
  const ids = idList(field);
  list.replaceChildren(...ids.map((id) => {
    const item = node("li");
    const label = node("span", "…");
    void nameOf(kind, id).then((name) => { label.textContent = name; });
    const remove = node("button", "Remove", "secondary");
    remove.type = "button";
    remove.addEventListener("click", () => {
      draftForm.elements[field].value = idList(field).filter((value) => value !== id).join("\n");
      markDirty();
    });
    item.append(label, remove);
    return item;
  }));
}

function renderSelections() {
  renderList(find("profile-list"), "profile_ids", "profile");
  renderList(find("voucher-list"), "specimen_ids", "voucher");
}

function addId(field, id) {
  const ids = idList(field);
  if (!ids.includes(id)) draftForm.elements[field].value = [...ids, id].join("\n");
  markDirty();
}

function clearPreview() {
  state.approval = null;
  find("publish").reset();
  find("preview").hidden = true;
}

function updateReview() {
  find("validate").querySelector("button").disabled = !state.draft?.draft_revision || state.dirty;
  find("publish").querySelector("button").disabled = !state.approval || !state.curator;
  renderSubmission();
}

/** Researchers hand a saved draft to the curators; curators publish directly, so they don't see this. */
function renderSubmission() {
  const box = find("submission");
  if (!box) return;
  const draft = state.draft;
  box.hidden = !draft?.draft_revision;
  if (box.hidden) return;
  const submitted = draft.submitted_at;
  find("submission-text").textContent = submitted
    ? `Submitted on ${submitted.slice(0, 10)}. Curators see it in their review list. You can keep editing; they review the latest saved draft.`
    : "When the draft is saved and its records are released, submit it. Curators then preview and publish it.";
  find("submit-review").hidden = Boolean(submitted);
  find("submit-review").disabled = state.dirty;
  find("take-back").hidden = !submitted;
}

async function changeSubmission(method) {
  const feedback = find("submission").querySelector(".feedback");
  try {
    const summary = await request(`/api/depositions/${endpoint(state.draft.id)}/submission`, {method});
    state.draft = {...state.draft, submitted_at: summary.submitted_at};
    status(feedback, method === "POST" ? "Submitted for review." : "Taken back from review.");
  } catch (error) {
    status(feedback, error.message, true);
  }
  renderSubmission();
}

function markDirty() {
  state.dirty = true;
  renderSelections();
  clearPreview();
  updateReview();
}

function idList(field) {
  return [...new Set(draftForm.elements[field].value.split(/[\s,]+/).filter(Boolean))];
}

function profileIds() {
  return idList("profile_ids");
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
  ensureInstitution(draft.institution);
  form.elements.institution.value = draft.institution;
  form.elements.institution.disabled = true;
  const version = draft.latest_version ? ` · published version ${draft.latest_version}` : " · not yet published";
  find("draft-selection").textContent = `${draft.institution} ${draft.accession}${version}`;
  find("deposition-title").textContent = draft.draft?.title || (draft.latest_version ? "Deposition" : "New deposition");
  if (window.location.pathname.endsWith("/new")) history.replaceState(null, "", `/researcher/depositions/${endpoint(draft.id)}`);
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
  renderSelections();
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

function voucherRelease(voucher, controls, label = "Release voucher") {
  const location = node("label", "Public locality");
  const choice = node("select");
  choice.append(new Option("Withheld", "withheld"), new Option("Country and region", "region"));
  choice.value = voucher.public_location === "region" ? "region" : "withheld";
  location.append(choice);
  controls.append(location, releaseButton(label, `/api/specimen/${endpoint(voucher.id)}/visibility`,
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

function renderInput({profile, study, vouchers}) {
  const card = node("article", "", "requirement");
  const visibility = (item) => item.is_public ? "Released" : "Private";
  const roles = Object.fromEntries(VOUCHER_ROLES);
  card.append(
    node("h3", profile.name),
    ...vouchers.map((voucher) => node("p", `Voucher ${[voucher.name, voucher.accession].filter(Boolean).join(" · ")
      || voucher.id} (${roles[voucher.role] ?? voucher.role}) · ${visibility(voucher)}`)),
    node("p", `Study ${study.title} · ${visibility(study)}`),
    node("p", `Profile · ${visibility(profile)}`),
  );
  if (!state.curator) return card;
  const controls = node("div", "", "requirement-actions");
  for (const voucher of vouchers.filter((item) => !item.is_public)) {
    voucherRelease(voucher, controls, `Release voucher ${voucher.accession || voucher.id}`);
  }
  for (const [item, label, group] of [[study, "study", "studies"], [profile, "profile", "profiles"]]) {
    if (!item.is_public) {
      controls.append(releaseButton(`Release ${label}`, `/api/chemistry/${group}/${endpoint(item.id)}/visibility`,
        () => ({is_public: true})));
    }
  }
  if (controls.children.length) card.append(controls);
  return card;
}

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
    const linked = (profile) => profile.voucher
      ? profile.voucher.id === voucher.id : profile.sample.vouchers.some((link) => link.id === voucher.id);
    if (!snapshot.profiles.some(linked)) {
      profiles.append(node("li", `Voucher ${voucher.accession ?? voucher.reg_no ?? voucher.id}`));
    }
  }
  summary.replaceChildren(node("h4", snapshot.title),
    node("p", `${snapshot.institution_name} · Version ${snapshot.version} · ${snapshot.license}`), profiles,
    node("p", `Identifier ${snapshot.identifier}`, "break"),
    node("p", `Snapshot SHA-256 ${preview.snapshot_sha256}`, "break"));
  find("preview-json").textContent = JSON.stringify(snapshot, null, 2);
  find("preview").hidden = false;
  updateReview();
  return "Validation passed.";
});
bindForm("publish", async () => {
  const approval = requiredSelection(state.approval, "Validate and preview the saved draft first.");
  const result = await request(`/api/depositions/${endpoint(state.draft.id)}/publish`, {method: "POST", json: approval});
  setDraft({...state.draft, latest_version: result.version, draft_revision: null, draft: null}, false);
  await refreshInputs();
  const message = find("publication-result");
  const link = node("a", `Open published version ${result.version}`);
  link.href = new URL(result.url).pathname.replace("/api/depositions/public/", "/depositions/");
  message.replaceChildren(link);
  message.hidden = false;
});

find("add-credit").addEventListener("click", () => { addCredit(); markDirty(); });
draftForm.addEventListener("input", markDirty);
find("choose-study").addEventListener("change", async (event) => {
  const profiles = event.target.value ? (await request(`/api/chemistry/studies/${endpoint(event.target.value)}`)).profiles : [];
  selectOptions(find("choose-profile"), profiles.map((profile) => ({id: profile.id,
    label: `Sample ${profile.sample_code} · run ${profile.run_code}${profile.is_public ? "" : " (private)"}`})), "Select a run");
});
find("attach-profile").addEventListener("click", () => {
  const id = find("choose-profile").value;
  if (id) addId("profile_ids", id);
});
find("submit-review")?.addEventListener("click", () => changeSubmission("POST"));
find("take-back")?.addEventListener("click", () => changeSubmission("DELETE"));
voucherPicker(find("draft-voucher-picker"), (voucher) => addId("specimen_ids", voucher.specimen_id));

async function startDeposition() {
  const [institutions, studies] = await Promise.all([request("/api/institutions"), request("/api/chemistry/studies")]);
  selectOptions(draftForm.elements.institution, institutions.map((item) => ({id: item.code, label: `${item.code} · ${item.name}`})),
    institutions.length ? "Choose an institution" : "No institution registered yet");
  selectOptions(find("choose-study"), studies.studies.map((study) => ({id: study.id, label: study.title})), "Select a study");
  if (page.dataset.deposition) {
    setDraft(await request(`/api/depositions/${endpoint(page.dataset.deposition)}/draft`), true);
    await refreshInputs();
  } else {
    addCredit();
    find("draft-selection").textContent = "Not saved yet";
    renderSelections();
    updateReview();
  }
}

startDeposition().catch((error) => status(draftForm.querySelector(":scope > .feedback"), error.message, true));

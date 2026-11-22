// Shared helpers for HERBAR staff pages. Requests use the browser session; writes send the CSRF token.

export const find = (id) => document.getElementById(id);
export const endpoint = (value) => encodeURIComponent(value);

export function csrfToken() {
  const match = document.cookie.split("; ").find((item) => item.startsWith("herbar_csrf="));
  return match ? decodeURIComponent(match.slice("herbar_csrf=".length)) : "";
}

export function node(tag, text = "", className = "") {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

export async function request(path, {method = "GET", json, multipart} = {}) {
  const headers = {};
  if (method !== "GET") headers["X-CSRF-Token"] = csrfToken();
  if (json !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {
    method,
    headers,
    body: multipart ?? (json === undefined ? undefined : JSON.stringify(json)),
  });
  if (response.status === 403 && !document.cookie.includes("herbar_csrf=")) {
    window.location.assign(`/sign-in?next=${encodeURIComponent(location.pathname + location.search)}`);
  }
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = result.detail;
    const message = Array.isArray(detail)
      ? detail.map((error) => `${error.loc.slice(1).join(" ")} ${error.msg}`).join(". ")
      : detail;
    const error = new Error(message || `Request failed (HTTP ${response.status}).`);
    error.status = response.status;
    if (Array.isArray(detail)) error.issues = detail;
    throw error;
  }
  return result;
}

export function status(element, message = "", error = false) {
  element.textContent = message;
  element.toggleAttribute("data-error", error);
}

/** Handle a form's submit with fetch; `target` is a form element or its id. */
export function bindForm(target, handler, {fieldName} = {}) {
  const form = typeof target === "string" ? find(target) : target;
  const feedback = form.querySelector(":scope > .feedback") ?? form.querySelector(".feedback");
  const errors = new Map();
  const clearError = (field) => {
    const previous = errors.get(field);
    if (!previous) return;
    previous.message.remove();
    field.removeAttribute("aria-invalid");
    if (previous.description) field.setAttribute("aria-describedby", previous.description);
    else field.removeAttribute("aria-describedby");
    errors.delete(field);
  };
  const showErrors = (entries) => {
    for (const [field, text] of entries) {
      clearError(field);
      const message = node("span", text, "field-error");
      message.id = `${form.id}-error-${Array.from(form.elements).indexOf(field)}`;
      const description = field.getAttribute("aria-describedby");
      field.insertAdjacentElement("afterend", message);
      field.setAttribute("aria-invalid", "true");
      field.setAttribute("aria-describedby", [description, message.id].filter(Boolean).join(" "));
      errors.set(field, {message, description});
    }
    const first = Array.from(form.elements).find((field) => errors.has(field));
    if (!first) return;
    for (let parent = first.parentElement; parent && parent !== form; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS") parent.open = true;
    }
    status(feedback, "Check the highlighted fields.", true);
    requestAnimationFrame(() => first.focus());
  };
  if (fieldName) {
    form.noValidate = true;
    const clearOnEdit = (event) => clearError(event.target);
    form.addEventListener("input", clearOnEdit);
    form.addEventListener("change", clearOnEdit);
    form.addEventListener("reset", () => {
      for (const field of errors.keys()) clearError(field);
    });
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button:not([type='button'])");
    if (fieldName) {
      for (const field of errors.keys()) clearError(field);
      const invalid = [];
      for (const field of form.elements) {
        if (!field.willValidate) continue;
        if (!field.validity.valid) invalid.push([field, field.validationMessage]);
        else if (field.required && ["text", "textarea"].includes(field.type) && !field.value.trim()) {
          invalid.push([field, "Enter a value."]);
        }
      }
      if (invalid.length) {
        showErrors(invalid);
        return;
      }
    }
    submit.disabled = true;
    status(feedback, "Working…");
    try {
      const message = await handler(new FormData(form), form);
      status(feedback, message);
    } catch (error) {
      const entries = fieldName && error.issues?.flatMap(({loc, msg}) => {
        const name = fieldName(loc.slice(1));
        const field = Array.from(form.elements).find((item) =>
          item.willValidate && (item.name === name || item.dataset.errorField === name));
        return field ? [[field, msg.replace(/^Value error, /, "")]] : [];
      });
      if (entries?.length && entries.length === error.issues.length) showErrors(entries);
      else {
        if (entries?.length) showErrors(entries);
        status(feedback, error.message || "Request failed.", true);
      }
    } finally {
      submit.disabled = false;
      document.dispatchEvent(new CustomEvent("herbar:form-settled", {detail: {form}}));
    }
  });
}

export function selectOptions(select, options, placeholder, value = "") {
  select.replaceChildren(new Option(placeholder, ""), ...options.map(({label, id}) => new Option(label, id)));
  select.value = value;
}

export function requiredSelection(value, message) {
  if (!value) throw new Error(message);
  return value;
}

const RECORD_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function voucherLabel(voucher) {
  return voucher.accession || voucher.reg_no || voucher.specimen_id;
}

/**
 * A voucher search inside `root` (.picker-query, .picker-search, .feedback, .picker-results).
 * Searches recorded names, accessions and registration numbers, private vouchers included; a pasted
 * record ID opens that voucher directly. Calls onPick(voucher) for the chosen record.
 */
export function voucherPicker(root, onPick, {pageSize = 8} = {}) {
  const query = root.querySelector(".picker-query");
  const button = root.querySelector(".picker-search");
  const feedback = root.querySelector(".feedback");
  const list = root.querySelector(".picker-results");
  let page = 1;

  function row(voucher) {
    const item = node("li");
    const text = node("span");
    text.append(node("strong", voucher.subnomen || "Name not recorded"),
      node("span", [voucherLabel(voucher), voucher.holding_institution, voucher.collection].filter(Boolean).join(" · "), "muted small"));
    const use = node("button", "Use voucher", "secondary");
    use.type = "button";
    use.addEventListener("click", () => {
      onPick(voucher);
      list.replaceChildren();
      query.value = "";
      status(feedback, `Selected ${voucherLabel(voucher)}.`);
      query.focus();
    });
    item.append(text, use);
    return item;
  }

  async function search(more = false) {
    const text = query.value.trim();
    if (!text) return status(feedback, "Enter a name, accession or registration number.", true);
    page = more ? page + 1 : 1;
    button.disabled = true;
    try {
      if (RECORD_ID.test(text)) {
        const voucher = await request(`/api/specimen/get-specimen-by-id?specimen_id=${endpoint(text)}`);
        list.replaceChildren(row(voucher));
        return status(feedback, "1 voucher.");
      }
      const result = await request(`/api/specimen/search-specimens-by-keyword?keyword=${endpoint(text)}&page=${page}&size=${pageSize}`);
      const rows = result.items.map(row);
      if (more) list.querySelector(".picker-more")?.remove();
      more ? list.append(...rows) : list.replaceChildren(...rows);
      const shown = list.querySelectorAll("li:not(.picker-more)").length;
      status(feedback, result.total ? `${result.total} voucher${result.total === 1 ? "" : "s"}.` : "No vouchers match.", !result.total);
      if (shown < result.total) {
        const item = node("li", "", "picker-more");
        const next = node("button", "Show more", "text-button");
        next.type = "button";
        next.addEventListener("click", () => search(true));
        item.append(next);
        list.append(item);
      }
    } catch (error) {
      status(feedback, error.message, true);
    } finally {
      button.disabled = false;
    }
  }

  button.addEventListener("click", () => search());
  query.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      search();
    }
  });
}

export const VOUCHER_ROLES = [
  ["sampled_from_voucher", "Sampled from the voucher"],
  ["same_individual", "Same individual"],
  ["same_population", "Same population"],
  ["collected_alongside", "Collected alongside"],
  ["cultivated_from", "Cultivated from the voucher"],
  ["reference_for_commercial_material", "Reference for commercial material"],
];

// Common GC columns by stationary-phase polarity. Matched on the name without spaces, dashes or case.
const COLUMN_POLARITY = [
  [/wax|ffap|carbowax|innowax|stabilwax|supelcowax|bp20|peg|cpwax|zbwax|dbwax/, "polar"],
  [/1701|17|35|225|624|1301|vf200|ov17|bpx50|rxi17|rtx200|mxt200|cyclodex|bdex|chirasil/, "semi-polar"],
  [/^(hp|db|rtx|rxi|zb|vf|bpx|bp|elite|tg|slb|spb|sps|cpsil|ov|se|ab|mega|optima|equity|hpultra)?(1|5|30|52|101|8|5ms|5sil|1ms|5ht|5amine|xlb)/, "non-polar"],
];

/** The polarity class of a GC column from its name, e.g. HP-5MS → non-polar, DB-WAX → polar; null if unknown. */
export function columnPolarity(name) {
  // Only the name counts: drop dimensions such as "30 m × 0.25 mm, 0.25 µm" and anything in brackets.
  const key = (name ?? "").toLowerCase().split(/[(,;]/)[0]
    .replace(/(\d)\s*[x×]\s*(\d)/g, "$1 $2").replace(/\d+(\.\d+)?\s*(m|mm|µm|um|μm)\b/g, "")
    .replace(/[\s\-_./®™×]/g, "");
  if (!key) return null;
  return COLUMN_POLARITY.find(([pattern]) => pattern.test(key))?.[1] ?? null;
}

/** Show the GC or LC run fields of a form that has a .technique select and a .run-fields fieldset. */
export function bindRunFields(form) {
  // The polarity follows the column's name until someone chooses it.
  const column = form.querySelector("[name='run.column']");
  const polarity = form.querySelector("[name='run.polarity_class']");
  if (column && polarity) {
    let guessed = !polarity.value;
    polarity.addEventListener("change", () => { guessed = false; });
    column.addEventListener("input", () => {
      const guess = columnPolarity(column.value);
      if ((guessed || !polarity.value) && guess) {
        polarity.value = guess;
        guessed = true;
      }
    });
  }
  const technique = form.querySelector(".technique");
  const render = () => {
    const kind = technique.value.startsWith("GC") ? "gc" : technique.value === "isolation" ? "isolation" : "lc";
    for (const field of form.querySelectorAll(".run-fields [data-for]")) {
      field.hidden = !field.dataset.for.split(" ").includes(kind);
      field.querySelector("input, select, textarea").disabled = field.hidden;
    }
  };
  technique.addEventListener("change", render);
  render();
}

export function runMetadata(form) {
  const run = {};
  for (const field of form.querySelectorAll(".run-fields label:not([hidden]) [name^='run.']")) {
    if (field.value.trim()) run[field.name.slice(4)] = field.value.trim();
  }
  return run;
}

/** Form data without empty fields and without run.* fields. */
export function filledFields(data) {
  return Object.fromEntries([...data].filter(([name, value]) => !name.startsWith("run.") && String(value).trim()));
}

/** Buttons with data-put (URL) and data-body (JSON) send a PUT after confirmation, then reload the page. */
export function bindPutButtons(root = document) {
  for (const button of root.querySelectorAll("button[data-put]")) {
    button.addEventListener("click", async () => {
      if (button.dataset.confirm && !window.confirm(button.dataset.confirm)) return;
      button.disabled = true;
      try {
        await request(button.dataset.put, {method: "PUT", json: JSON.parse(button.dataset.body)});
        window.location.reload();
      } catch (error) {
        button.textContent = error.message;
        button.disabled = false;
      }
    });
  }
}

/** Ask before an action that can't be taken back. Resolves true when the person confirms. */
export function confirmAction(title, body, action = "Confirm") {
  const dialog = document.createElement("dialog");
  const form = node("form", "", "stack");
  form.method = "dialog";
  const row = node("div", "", "link-row");
  const cancel = node("button", "Cancel", "secondary");
  cancel.value = "cancel";
  cancel.autofocus = true;
  const confirm = node("button", action, "primary");
  confirm.value = "confirm";
  row.append(cancel, confirm);
  form.append(node("h2", title), node("p", body), row);
  dialog.append(form);
  document.body.append(dialog);
  return new Promise((resolve) => {
    dialog.addEventListener("close", () => { resolve(dialog.returnValue === "confirm"); dialog.remove(); }, {once: true});
    dialog.showModal();
  });
}

/**
 * A taxon lookup inside `root` (.taxon-query, .taxon-search, .feedback, .taxon-results, .taxon-choice).
 * Lists taxa already in this herbarium first, then, for a name of two or more words, GBIF's best match for the name
 * as written (with match type, confidence and anything to check), then GBIF names. Choosing a GBIF name imports it
 * with its parents; nothing is added until the curator chooses.
 * Calls onPick({taxon_id, name, rank, authority}) with the local taxon, or onPick(null) when the choice is cleared.
 */
export function taxonPicker(root, onPick) {
  const query = root.querySelector(".taxon-query");
  const feedback = root.querySelector(".feedback");
  const list = root.querySelector(".taxon-results");
  const choice = root.querySelector(".taxon-choice");

  function choose(taxon, note = "") {
    list.replaceChildren();
    const change = node("button", "Change", "text-button");
    change.type = "button";
    change.addEventListener("click", () => { choice.replaceChildren(); choice.hidden = true; query.hidden = false;
      root.querySelector(".taxon-search").hidden = false; query.focus(); onPick(null); });
    choice.replaceChildren(node("strong", taxon.name), node("span", taxon.rank, "muted small"), change);
    choice.hidden = false;
    query.hidden = true;
    root.querySelector(".taxon-search").hidden = true;
    status(feedback, note);
    onPick(taxon);
  }

  function row(title, detail, label, action, notes = []) {
    const item = node("li");
    const text = node("span");
    text.append(node("strong", title), node("span", detail, "muted small"));
    for (const note of notes) text.append(node("span", note, "small warning-text"));
    const use = node("button", label, "secondary");
    use.type = "button";
    use.addEventListener("click", async () => {
      use.disabled = true;
      try { await action(); } catch (error) { status(feedback, error.message, true); use.disabled = false; }
    });
    item.append(text, use);
    return item;
  }

  async function search() {
    const term = query.value.trim();
    if (term.length < 2) return status(feedback, "Type at least two letters of the name.", true);
    status(feedback, "Searching…");
    list.replaceChildren();
    const local = (await request(`/api/taxonomy?query=${endpoint(term)}&size=8`)).items;
    const known = new Set(local.map((taxon) => taxon.gbif_key));
    if (local.length) list.append(node("li", "In this herbarium", "list-heading"));
    for (const taxon of local) {
      list.append(row(taxon.name, `${taxon.rank} · GBIF ${taxon.gbif_key}`, "Use",
        async () => choose({taxon_id: taxon.taxon_id, name: taxon.name, rank: taxon.rank})));
    }
    const gbifRow = (item, detail, notes = [], matchedName = null) =>
      row(item.name, detail, item.taxon_id ? "Use" : "Add and use", async () => {
        const params = matchedName ? `&matched_name=${endpoint(matchedName)}` : "";
        const taxon = await request(`/api/taxonomy/import-from-gbif?gbif_key=${endpoint(item.gbif_key)}${params}`, {method: "POST"});
        choose(taxon, taxon.note || (item.taxon_id ? "" : `Added ${taxon.name} and its parent taxa from GBIF.`));
      }, notes);
    let source = null;
    let matched = 0;
    if (term.split(/\s+/).length > 1) {
      try {
        const result = await request(`/api/taxonomy/gbif-match?name=${endpoint(term)}`);
        source = result.source;
        const proposals = result.match ? [result.match] : result.alternatives;
        const usable = proposals.filter((item) => item.importable);
        if (usable.length || result.review.length) list.append(node("li", "GBIF match for the name as written", "list-heading"));
        for (const item of usable) {
          const confidence = (result.match ? result.confidence : item.confidence);
          const how = [result.match ? `${result.match_type} match` : "alternative", confidence != null ? `${confidence}% confidence` : null];
          known.add(item.gbif_key);
          list.append(gbifRow(item, [...how, item.rank, item.family].filter(Boolean).join(" · "), result.match ? result.review : [], term));
          matched += 1;
        }
        if (!usable.length && result.review.length) list.append(node("li", result.review.join(" "), "small warning-text"));
      } catch (error) {
        if (error.status !== 503) list.append(node("li", error.message, "small warning-text"));
      }
    }
    let remote = [];
    try {
      remote = await request(`/api/taxonomy/gbif-search?q=${endpoint(term)}`);
    } catch (error) {
      status(feedback, error.message, true);
      return;
    }
    remote = remote.filter((item) => !known.has(item.gbif_key));
    if (remote.length) list.append(node("li", "Other GBIF names", "list-heading"));
    for (const item of remote) {
      const detail = [item.rank, item.status !== "accepted" && item.status, item.family || item.phylum, item.kingdom]
        .filter(Boolean).join(" · ");
      list.append(gbifRow(item, detail));
    }
    if (matched || remote.length) {
      const credit = node("li", "", "list-heading small");
      const link = node("a", (source && source.name) || "GBIF Backbone Taxonomy");
      link.href = (source && source.url) || "https://www.gbif.org/";
      link.rel = "noopener";
      link.target = "_blank";
      credit.append("Names from ", link, ` (${(source && source.license) || "CC BY 4.0"}).`);
      list.append(credit);
    }
    const found = local.length || matched || remote.length;
    status(feedback, found ? "" : "No match here or in GBIF. Check the spelling.", !found);
  }

  root.querySelector(".taxon-search").addEventListener("click", () => search().catch((error) => status(feedback, error.message, true)));
  query.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      search().catch((error) => status(feedback, error.message, true));
    }
  });
  return {
    clear() { choice.replaceChildren(); choice.hidden = true; query.hidden = false; root.querySelector(".taxon-search").hidden = false;
      list.replaceChildren(); status(feedback); },
  };
}

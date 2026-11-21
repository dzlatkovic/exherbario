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
    throw new Error(message || `Request failed (HTTP ${response.status}).`);
  }
  return result;
}

export function status(element, message = "", error = false) {
  element.textContent = message;
  element.toggleAttribute("data-error", error);
}

/** Handle a form's submit with fetch; `target` is a form element or its id. */
export function bindForm(target, handler) {
  const form = typeof target === "string" ? find(target) : target;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button:not([type='button'])");
    // The form's own message line; nested widgets (such as a voucher picker) have their own.
    const feedback = form.querySelector(":scope > .feedback") ?? form.querySelector(".feedback");
    submit.disabled = true;
    status(feedback, "Working…");
    try {
      const message = await handler(new FormData(form), form);
      status(feedback, message);
    } catch (error) {
      status(feedback, error.message || "Request failed.", true);
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

/** Show the GC or LC run fields of a form that has a .technique select and a .run-fields fieldset. */
export function bindRunFields(form) {
  const technique = form.querySelector(".technique");
  const render = () => {
    const kind = technique.value.startsWith("GC") ? "gc" : "lc";
    for (const field of form.querySelectorAll(".run-fields [data-for]")) field.hidden = field.dataset.for !== kind;
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

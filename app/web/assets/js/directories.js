// Curation › Directories: list, add, edit and delete shared reference records through the curator API.
import {bindForm, confirmAction, endpoint, find, node, request, status} from "./core.js";

const text = (name, label, extra = {}) => ({name, label, type: "text", ...extra});
const number = (name, label, extra = {}) => ({name, label, type: "number", step: "any", ...extra});
const join = (...parts) => parts.filter((part) => part !== null && part !== undefined && part !== "").join(" · ");

const DIRECTORIES = {
  institutions: {
    note: "Institution codes are permanent: they form part of every published accession, so codes can be added but not changed or removed.",
    key: "code",
    list: () => request("/api/institutions"),
    label: (item) => `${item.code} · ${item.name}`,
    detail: (item) => join(item.index_herbariorum_code && `Index Herbariorum ${item.index_herbariorum_code}`, item.ror),
    fields: [text("code", "Code", {required: true, maxLength: 40, placeholder: "e.g. BEOU"}), text("name", "Name", {required: true, maxLength: 200}),
             text("index_herbariorum_code", "Index Herbariorum code", {maxLength: 20}), text("ror_id", "ROR ID", {placeholder: "e.g. 02qsmb048"})],
    create: (data) => request("/api/institutions", {method: "POST", json: data}),
  },
  storage: {
    note: "A box label is fixed once created; its room and shelf can change.",
    filter: true,
    key: "storage_id",
    list: () => request("/api/storage/get-all"),
    label: (item) => `Box ${item.box}`,
    detail: (item) => join(item.room && `Room ${item.room}`, item.shelf && `Shelf ${item.shelf}`),
    fields: [text("box", "Box", {required: true, maxLength: 100, createOnly: true}), text("room", "Room", {maxLength: 100}),
             text("shelf", "Shelf", {maxLength: 100})],
    create: (data) => request("/api/storage/create-new-storage", {method: "POST", json: data}),
    update: (id, data) => request(`/api/storage/update-storage?storage_id=${endpoint(id)}`, {method: "PUT", json: data}),
    remove: (id) => request(`/api/storage/delete-storage?storage_id=${endpoint(id)}`, {method: "DELETE"}),
  },
  locations: {
    note: "Edits to a field location are kept in its correction history, with the reason you give.",
    filter: true,
    key: "field_loc_id",
    list: () => request("/api/field-locations/get-all-field-locations"),
    label: (item) => item.locality,
    detail: (item) => join(`${item.region}, ${item.country}`, item.gps_lat != null && `${item.gps_lat}, ${item.gps_long}`,
                           item.altitude != null && `${item.altitude} m`),
    fields: [text("country", "Country", {required: true, maxLength: 100}), text("region", "Region", {required: true, maxLength: 150}),
             text("locality", "Locality", {required: true, maxLength: 500}), text("habitat", "Habitat", {maxLength: 255}),
             number("altitude", "Altitude (m)", {step: "1"}), number("gps_lat", "Latitude", {min: -90, max: 90}),
             number("gps_long", "Longitude", {min: -180, max: 180}), number("coordinate_uncertainty_m", "Uncertainty (m)", {step: "1", min: 0}),
             text("geodetic_datum", "Geodetic datum", {maxLength: 20, placeholder: "e.g. WGS84"}),
             text("georeference_source", "Georeference source", {maxLength: 200}),
             text("correction_reason", "Reason for the change", {maxLength: 1000, editOnly: true, required: true})],
    create: (data) => request("/api/field-locations/create-new-field-loc", {method: "POST", json: data}),
    update: (id, data) => request(`/api/field-locations/update-field-loc?field_loc_id=${endpoint(id)}`, {method: "PUT", json: data}),
    remove: (id) => request(`/api/field-locations/delete-field-loc?field_loc_id=${endpoint(id)}`, {method: "DELETE"}),
  },
  bibliography: {
    note: "Publications that vouchers can be linked to.",
    filter: true,
    key: "pub_id",
    list: () => request("/api/publication/get-all"),
    label: (item) => item.title,
    detail: (item) => join(item.journal, String(item.year).slice(0, 4), item.doi && `doi:${item.doi}`),
    value: (item, name) => (name === "year" ? String(item.year).slice(0, 4) : item[name]),
    fields: [text("title", "Title", {required: true, maxLength: 500}), text("journal", "Journal", {required: true, maxLength: 300}),
             text("year", "Year", {required: true, pattern: "[0-9]{4}", placeholder: "YYYY"}), text("doi", "DOI", {required: true, maxLength: 200}),
             {name: "abstract", label: "Abstract", type: "textarea", required: true}],
    create: (data) => request("/api/publication/create-new-publication", {method: "POST", json: data}),
    update: (id, data) => request(`/api/publication/update-publication?pub_id=${endpoint(id)}`, {method: "PUT", json: data}),
    remove: (id) => request(`/api/publication/delete-publication?pub_id=${endpoint(id)}`, {method: "DELETE"}),
  },
  taxonomy: {
    note: "Taxa come from GBIF. Adding a GBIF key also adds its parent taxa up to the kingdom. Search shows matching names; with no search, the kingdoms.",
    search: true,
    key: "taxon_id",
    list: async (query) => (await request(`/api/taxonomy?query=${endpoint(query)}&size=50`)).items,
    label: (item) => item.name,
    detail: (item) => join(item.rank, `GBIF ${item.gbif_key}`),
    fields: [text("gbif_key", "GBIF key", {required: true, pattern: "[0-9]+", placeholder: "e.g. 3120060"})],
    create: async (data) => {
      const added = await request(`/api/taxonomy/build-taxonomic-tree?gbif_key=${endpoint(data.gbif_key)}`, {method: "POST"});
      return `Added ${added.length} tax${added.length === 1 ? "on" : "a"}.`;
    },
    remove: (id) => request(`/api/taxonomy/delete-taxon?taxon_id=${endpoint(id)}`, {method: "DELETE"}),
  },
};

const section = find("directory");
const config = DIRECTORIES[section.dataset.kind];
const form = find("entry-form");
const list = find("directory-list");
const listStatus = find("directory-status");
let items = [];
let editing = null;

find("directory-note").textContent = config.note;
const searchForm = find("directory-search");
searchForm.hidden = !(config.filter || config.search);
find("directory-query").placeholder = config.search ? "Search by name" : "Filter this list";

function valueOf(item, name) {
  return config.value ? config.value(item, name) : item[name];
}

function buildFields(item) {
  const box = find("entry-fields");
  box.replaceChildren();
  for (const field of config.fields) {
    if ((field.createOnly && item) || (field.editOnly && !item)) continue;
    const label = node("label", field.label);
    const input = node(field.type === "textarea" ? "textarea" : "input");
    if (field.type !== "textarea") input.type = field.type;
    input.name = field.name;
    for (const key of ["required", "maxLength", "placeholder", "pattern", "step", "min", "max"]) {
      if (field[key] !== undefined) input[key] = field[key];
    }
    if (field.type === "textarea") input.rows = 4;
    if (item && valueOf(item, field.name) != null) input.value = valueOf(item, field.name);
    label.append(input);
    if (field.type === "textarea" || field.name === "locality" || field.name === "title") label.classList.add("full");
    box.append(label);
  }
}

function openForm(item = null) {
  editing = item;
  find("entry-title").textContent = item ? `Edit ${config.label(item)}` : `Add to ${find("directory-title").textContent.toLowerCase()}`;
  buildFields(item);
  status(form.querySelector(":scope > .feedback"));
  form.hidden = false;
  form.querySelector("input, textarea")?.focus();
}

function closeForm() {
  form.hidden = true;
  editing = null;
}

/** Field values as the API expects them; on edit, only the fields that changed. */
function payload(data) {
  const result = {};
  for (const field of config.fields) {
    if (!data.has(field.name)) continue;
    const raw = String(data.get(field.name)).trim();
    const value = raw === "" ? null : field.type === "number" ? Number(raw) : raw;
    if (editing) {
      const before = valueOf(editing, field.name) ?? null;
      if (field.editOnly || value !== (before === null ? null : field.type === "number" ? Number(before) : String(before))) {
        result[field.name] = value;
      }
    } else if (value !== null) {
      result[field.name] = value;
    }
  }
  return result;
}

function render() {
  const query = config.filter ? find("directory-query").value.trim().toLocaleLowerCase() : "";
  const shown = query ? items.filter((item) => `${config.label(item)} ${config.detail(item)}`.toLocaleLowerCase().includes(query)) : items;
  list.replaceChildren(...shown.map((item) => {
    const row = node("li");
    const body = node("div");
    body.append(node("strong", config.label(item)), node("span", config.detail(item), "muted small"));
    const actions = node("div", "", "link-row");
    if (config.update) {
      const edit = node("button", "Edit", "text-button");
      edit.type = "button";
      edit.addEventListener("click", () => openForm(item));
      actions.append(edit);
    }
    if (config.remove) {
      const remove = node("button", "Delete", "text-button");
      remove.type = "button";
      remove.addEventListener("click", () => removeItem(item, row));
      actions.append(remove);
    }
    const message = node("p", "", "feedback");
    row.append(body, actions, message);
    return row;
  }));
  if (!items.length) status(listStatus, config.search ? "No taxa match this search." : "Nothing recorded yet.");
  else if (!shown.length) status(listStatus, "Nothing matches this filter.");
  else status(listStatus);
}

async function removeItem(item, row) {
  if (!await confirmAction(`Delete ${config.label(item)}?`, "This can't be undone. Records that still use it keep it, and the delete is refused.", "Delete")) return;
  const message = row.querySelector(".feedback");
  try {
    await config.remove(item[config.key]);
    items = items.filter((entry) => entry !== item);
    render();
    status(listStatus, `Deleted ${config.label(item)}.`);
  } catch (error) {
    status(message, error.message, true);  // the record stays on screen with the server's reason
  }
}

async function load() {
  items = await config.list(config.search ? find("directory-query").value.trim() : "");
  render();
}

find("add-entry").hidden = !config.create;
find("add-entry").addEventListener("click", () => openForm());
find("entry-cancel").addEventListener("click", closeForm);
bindForm(form, async (data) => {
  const body = payload(data);
  let message;
  if (editing) {
    if (Object.keys(body).every((key) => config.fields.find((field) => field.name === key)?.editOnly)) {
      throw new Error("Nothing changed.");
    }
    await config.update(editing[config.key], body);
    message = "Changes saved.";
  } else {
    const result = await config.create(body);
    message = typeof result === "string" ? result : "Added.";
  }
  closeForm();
  await load();
  status(listStatus, message);
  return message;
});
searchForm.addEventListener("submit", (event) => { event.preventDefault(); config.search ? load().catch(fail) : render(); });
find("directory-query").addEventListener("input", () => { if (config.filter) render(); });

function fail(error) {
  status(listStatus, error.message, true);
}

load().catch(fail);

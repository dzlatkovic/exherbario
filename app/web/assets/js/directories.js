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
    lookup: {
      label: "Find in ROR and Index Herbariorum", placeholder: "Institution name, herbarium code or ROR ID", button: "Search",
      run: async (query) => {
        const found = await request(`/api/institutions/lookup?q=${endpoint(query)}`);
        const where = (...parts) => join(...parts);
        const taken = (item) => (item.registered_code ? [`Already registered here as ${item.registered_code}.`] : []);
        const choices = [
          ...found.ror.map((item) => ({
            title: item.name, detail: where("ROR", item.ror_id, item.acronyms.join(", "), item.city, item.country, item.status !== "active" ? item.status : null),
            values: {name: item.name, ror_id: item.ror_id}, notes: taken(item),
            source: {...found.sources.ror, external_id: item.ror_id, url: item.ror},
          })),
          ...found.index_herbariorum.map((item) => ({
            title: `${item.code} · ${item.organization}`, detail: where("Index Herbariorum", item.division, item.city, item.country, item.status),
            // The herbarium code is suggested as this registry's code only when none has been typed yet.
            values: {index_herbariorum_code: item.code}, ifEmpty: {code: item.code, name: item.organization}, notes: taken(item),
            source: {...found.sources.index_herbariorum, external_id: item.code, url: item.url},
          })),
        ];
        const notes = [...Object.values(found.errors), ...(choices.length ? [] : ["Neither registry has a match. Check the spelling, or enter the details by hand."])];
        return {choices, notes, credits: Object.values(found.sources)};
      },
      attach: (body, sources) => {
        const used = sources.filter((item) => (item.provider === "ror" && item.external_id === body.ror_id)
          || (item.provider === "index_herbariorum" && item.external_id === (body.index_herbariorum_code || "").toUpperCase()));
        if (used.length) body.sources = used.map((item) => ({provider: item.provider, external_id: item.external_id, retrieved_at: item.retrieved_at}));
      },
    },
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
    lookup: {
      label: "Look up a DOI", placeholder: "e.g. 10.3390/plants13010001", button: "Fill from Crossref",
      run: async (doi) => {
        const found = await request(`/api/publication/doi-lookup?doi=${endpoint(doi)}`);
        const notes = [...(found.existing_pub_id ? ["This DOI is already in the bibliography."] : []), ...found.warnings];
        return {values: found.fields, notes, source: {...found.source, external_id: found.fields.doi}};
      },
      // Saved with the entry only while the DOI field still holds the DOI that was looked up.
      attach: (body, sources) => {
        const source = sources.find((item) => item.provider === "crossref");
        if (source && (body.doi || "").toLowerCase().endsWith(source.external_id)) {
          body.source = {provider: "crossref", external_id: source.external_id, retrieved_at: source.retrieved_at};
        }
      },
    },
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
let sources = [];  // attribution of values filled from a lookup, sent with the new entry

find("directory-note").textContent = config.note;
const searchForm = find("directory-search");
searchForm.hidden = !(config.filter || config.search);
find("directory-query").placeholder = config.search ? "Search by name" : "Filter this list";

function valueOf(item, name) {
  return config.value ? config.value(item, name) : item[name];
}

function credit(source) {
  const line = node("p", "", "muted small");
  const link = node("a", source.name);
  link.href = source.url;
  link.rel = "noopener";
  link.target = "_blank";
  const when = source.retrieved_at ? `, retrieved ${source.retrieved_at.slice(0, 10)}${source.stale ? " (an older copy: the registry is unreachable)" : ""}` : "";
  line.append("From ", link, `${when}. ${source.license}. Check every value before saving.`);
  return line;
}

/** Fill the form from a lookup: one proposal ({values, notes, source}) or a list to choose from ({choices}). */
function lookupBar() {
  const wrap = node("div", "", "lookup full");
  const row = node("div", "", "inline-form");
  const label = node("label", config.lookup.label);
  const input = node("input");
  input.type = "search";
  input.placeholder = config.lookup.placeholder;
  input.maxLength = 300;
  label.append(input);
  const run = node("button", config.lookup.button, "secondary");
  run.type = "button";
  row.append(label, run);
  const results = node("div", "", "lookup-results");
  const fill = (proposal) => {
    const set = (values, onlyEmpty) => {
      for (const [name, value] of Object.entries(values || {})) {
        const field = form.elements.namedItem(name);
        if (field && value !== null && value !== undefined && value !== "" && !(onlyEmpty && field.value.trim())) field.value = value;
      }
    };
    set(proposal.values, false);
    set(proposal.ifEmpty, true);
    sources = [...sources.filter((item) => item.provider !== proposal.source.provider), proposal.source];
  };
  const show = (found) => {
    if (found.choices) {
      const list = node("ul", "", "picker-results");
      for (const choice of found.choices) {
        const item = node("li");
        const text = node("span");
        text.append(node("strong", choice.title), node("span", choice.detail, "muted small"));
        const use = node("button", "Use", "secondary");
        use.type = "button";
        use.addEventListener("click", () => { fill(choice); results.replaceChildren(...(choice.notes || []).map((note) => node("p", note, "small warning-text")), credit(choice.source)); });
        item.append(text, use);
        list.append(item);
      }
      results.replaceChildren(...found.notes.map((note) => node("p", note, "small warning-text")), list,
        ...found.credits.map((source) => credit({...source, retrieved_at: null})));
    } else {
      fill(found);
      results.replaceChildren(...found.notes.map((note) => node("p", note, "small warning-text")), credit(found.source));
    }
  };
  const go = async () => {
    if (input.value.trim().length < 2) return;
    run.disabled = true;
    results.replaceChildren(node("p", "Looking up…", "muted small"));
    try { show(await config.lookup.run(input.value.trim())); }
    catch (error) { results.replaceChildren(node("p", error.message, "small warning-text")); }
    finally { run.disabled = false; }
  };
  run.addEventListener("click", go);
  input.addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); go(); } });
  wrap.append(row, results);
  return wrap;
}

function buildFields(item) {
  const box = find("entry-fields");
  box.replaceChildren();
  sources = [];
  if (config.lookup && !item) box.append(lookupBar());
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
    if (config.lookup) config.lookup.attach(body, sources);
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

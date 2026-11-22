// Saved run conditions and preparation methods: pick one to fill in the form, or save what is entered.
import {confirmAction, endpoint, request, status} from "./core.js";

const lists = {};
const controls = {run: [], preparation: []};

function load(kind) {
  lists[kind] ??= request(`/api/chemistry/condition-presets?kind=${endpoint(kind)}`);
  return lists[kind];
}

async function refresh(kind) {
  delete lists[kind];
  const presets = await load(kind);
  for (const control of controls[kind]) control.render(presets);
}

/**
 * Bind a .preset-control element. `read()` returns the values to save; `apply(values)` fills the form.
 * Several controls of one kind on a page share the list and update together.
 */
export function bindPresetControl(root, {read, apply}) {
  const kind = root.dataset.kind;
  const select = root.querySelector(".preset-select");
  const name = root.querySelector(".preset-name");
  const remove = root.querySelector(".preset-delete");
  const feedback = root.querySelector(".feedback");
  let presets = [];
  const control = {
    render(list) {
      presets = list;
      const current = select.value;
      select.replaceChildren(new Option(list.length ? "Choose saved entry" : "None saved yet", ""),
        ...list.map((preset) => new Option(preset.name, preset.id)));
      select.value = list.some((preset) => preset.id === current) ? current : "";
      select.disabled = !list.length;
      remove.hidden = !select.value;
    },
  };
  controls[kind].push(control);
  load(kind).then((list) => control.render(list)).catch((error) => status(feedback, error.message, true));

  select.addEventListener("change", () => {
    const preset = presets.find((item) => item.id === select.value);
    remove.hidden = !preset;
    if (!preset) return;
    apply(preset.values);
    name.value = preset.name;
    status(feedback, `Filled in from “${preset.name}”. Check the fields before saving.`);
  });

  async function save() {
    if (!name.value.trim()) {
      status(feedback, "Enter a name to save these conditions under.", true);
      name.focus();
      return;
    }
    try {
      const saved = await request("/api/chemistry/condition-presets", {
        method: "PUT", json: {kind, name: name.value.trim(), values: read()}});
      await refresh(kind);
      select.value = saved.id;
      remove.hidden = false;
      status(feedback, `Saved as “${saved.name}”.`);
    } catch (error) {
      status(feedback, error.message, true);
    }
  }

  root.querySelector(".preset-save").addEventListener("click", save);
  name.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      save();
    }
  });
  remove.addEventListener("click", async () => {
    const preset = presets.find((item) => item.id === select.value);
    if (!preset || !await confirmAction(`Delete “${preset.name}”?`,
      "Results already entered keep their own conditions.", "Delete")) return;
    try {
      await request(`/api/chemistry/condition-presets/${endpoint(preset.id)}`, {method: "DELETE"});
      select.value = "";
      await refresh(kind);
      status(feedback, `Deleted “${preset.name}”.`);
    } catch (error) {
      status(feedback, error.message, true);
    }
  });
}

const filled = (entries) => Object.fromEntries(entries.filter(([, value]) => value !== undefined && String(value).trim() !== ""));

/** Read and fill the preparation method fields (type, method reference, method and parameters) of `root`. */
export function preparationPreset(root) {
  const field = (name) => root.querySelector(`[name="${name}"]`);
  return {
    read: () => filled(["kind", "method_reference", "method_parameters"].map((name) => [name, field(name).value.trim()])),
    apply(values) {
      for (const name of ["kind", "method_reference", "method_parameters"]) field(name).value = values[name] ?? "";
      field("kind").dispatchEvent(new Event("change", {bubbles: true}));
    },
  };
}

/** Read and fill the technique, run fields, analytical method, basis and unit of `form`. */
export function runPreset(form, runMetadata) {
  const field = (name) => form.elements.namedItem(name);
  return {
    read: () => ({
      ...filled(["technique", "analytical_method", "measurement_basis", "unit"]
        .map((name) => [name, field(name)?.disabled ? "" : field(name)?.value.trim()])),
      run_metadata: runMetadata(form),
    }),
    apply(values) {
      for (const input of form.querySelectorAll("[name^='run.']")) input.value = "";
      field("technique").value = values.technique;
      field("technique").dispatchEvent(new Event("change", {bubbles: true}));
      for (const name of ["analytical_method", "measurement_basis", "unit"]) {
        if (values[name] !== undefined && field(name)) {
          field(name).value = values[name];
          field(name).dispatchEvent(new Event("change", {bubbles: true}));
        }
      }
      for (const [key, value] of Object.entries(values.run_metadata ?? {})) {
        if (field(`run.${key}`)) field(`run.${key}`).value = value;
      }
    },
  };
}

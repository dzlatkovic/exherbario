// Study page: samples with their vouchers, preparations, and the start of a results-table import.
import {bindForm, bindPutButtons, endpoint, filledFields, find, request} from "./core.js";
import {bindPresetControl, preparationPreset} from "./presets.js";
import {bindSampleFields} from "./sample-form.js";

const studyId = find("study").dataset.study;
const reload = () => window.location.reload();
const sampleFields = bindSampleFields(find("create-sample"));

bindForm("create-sample", async (data) => {
  await request(`/api/chemistry/studies/${endpoint(studyId)}/samples`, {method: "POST", json: sampleFields.payload(data)});
  reload();
  return "Sample added.";
}, {fieldName: (path) => path.join(".")});

bindForm("import-upload", async (data) => {
  const record = await request(`/api/chemistry/studies/${endpoint(studyId)}/imports`, {method: "POST", multipart: data});
  window.location.assign(`/researcher/studies/${endpoint(studyId)}/imports/${endpoint(record.id)}`);
  return "Uploaded.";
});

for (const form of document.querySelectorAll("form.add-preparation")) {
  bindPresetControl(form.querySelector(".preset-control"), preparationPreset(form));
  bindForm(form, async (data) => {
    await request(`/api/chemistry/samples/${endpoint(form.dataset.sample)}/preparations`, {method: "POST", json: filledFields(data)});
    reload();
    return "Preparation added.";
  });
}

for (const form of document.querySelectorAll("form.edit-preparation")) {
  bindPresetControl(form.querySelector(".preset-control"), preparationPreset(form));
  bindForm(form, async (data) => {
    // Every field is sent, so a cleared value is cleared; an empty batch code keeps the current one.
    const payload = Object.fromEntries([...data].filter(([name]) => !name.startsWith("run."))
      .map(([name, value]) => [name, String(value).trim() === "" ? null : value]));
    await request(`/api/chemistry/preparations/${endpoint(form.dataset.preparation)}`, {method: "PUT", json: payload});
    reload();
    return "Preparation saved.";
  });
}

find("copy-ai-prompt")?.addEventListener("click", async () => {
  const feedback = find("copy-ai-prompt-status");
  try {
    await navigator.clipboard.writeText(find("ai-prompt").textContent.trim());
    feedback.textContent = "Copied.";
  } catch {
    feedback.textContent = "Copying is blocked here: select the text and copy it.";
  }
});

bindPutButtons();

// Links to a collapsed section (#add-import, #add-manual) open it.
function openLinkedDetails() {
    const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (target instanceof HTMLDetailsElement) {
        target.open = true;
        target.querySelector("summary")?.focus();
    }
}
window.addEventListener("hashchange", openLinkedDetails);
openLinkedDetails();

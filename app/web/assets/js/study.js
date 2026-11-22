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

bindPutButtons();

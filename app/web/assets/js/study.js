// Study page: samples with their vouchers, preparations, and the start of a results-table import.
import {VOUCHER_ROLES, bindForm, bindPutButtons, endpoint, filledFields, find, node, request,
        requiredSelection, selectOptions, voucherLabel, voucherPicker} from "./core.js";

const studyId = find("study").dataset.study;
const reload = () => window.location.reload();
const sampleVouchers = [];

function renderSampleVouchers() {
  const rows = sampleVouchers.map((link, index) => {
    const row = node("div", "", "credit-row");
    row.append(node("p", [link.voucher.subnomen, voucherLabel(link.voucher)].filter(Boolean).join(" · ")));
    const label = node("label", "Role");
    const role = document.createElement("select");
    for (const [value, text] of VOUCHER_ROLES) role.append(new Option(text, value));
    role.value = link.role;
    role.addEventListener("change", () => { link.role = role.value; });
    label.append(role);
    const remove = node("button", "Remove", "secondary");
    remove.type = "button";
    remove.addEventListener("click", () => { sampleVouchers.splice(index, 1); renderSampleVouchers(); });
    row.append(label, remove);
    return row;
  });
  find("sample-vouchers").replaceChildren(...rows);
  const site = find("create-sample").elements.site_specimen_id;
  selectOptions(site, sampleVouchers.map(({voucher}) => ({id: voucher.specimen_id, label: voucherLabel(voucher)})),
    "Select a linked voucher", site.value);
}

function renderSiteFields() {
  const site = find("sample-site").value;
  find("site-voucher-field").hidden = site !== "voucher";
  find("site-location-field").hidden = site !== "field_location";
}

voucherPicker(find("sample-voucher-picker"), (voucher) => {
  if (sampleVouchers.some((link) => link.voucher.specimen_id === voucher.specimen_id)) return;
  sampleVouchers.push({voucher, role: sampleVouchers.length ? "same_population" : "sampled_from_voucher"});
  renderSampleVouchers();
});
find("sample-site").addEventListener("change", renderSiteFields);

bindForm("create-sample", async (data) => {
  if (!sampleVouchers.length) throw new Error("Add at least one voucher to the sample.");
  const site = data.get("site");
  const payload = filledFields(data);
  for (const name of ["site", "site_specimen_id", "field_loc_id"]) delete payload[name];
  if (site === "voucher") payload.site_specimen_id = requiredSelection(data.get("site_specimen_id"), "Select the site voucher.");
  if (site === "field_location") payload.field_loc_id = requiredSelection(data.get("field_loc_id").trim(), "Enter a field location ID.");
  payload.vouchers = sampleVouchers.map(({voucher, role}) => ({specimen_id: voucher.specimen_id, role}));
  await request(`/api/chemistry/studies/${endpoint(studyId)}/samples`, {method: "POST", json: payload});
  reload();
  return "Sample added.";
});

bindForm("import-upload", async (data) => {
  const record = await request(`/api/chemistry/studies/${endpoint(studyId)}/imports`, {method: "POST", multipart: data});
  window.location.assign(`/researcher/studies/${endpoint(studyId)}/imports/${endpoint(record.id)}`);
  return "Uploaded.";
});

for (const form of document.querySelectorAll("form.add-preparation")) {
  bindForm(form, async (data) => {
    await request(`/api/chemistry/samples/${endpoint(form.dataset.sample)}/preparations`, {method: "POST", json: filledFields(data)});
    reload();
    return "Preparation added.";
  });
}

bindPutButtons();

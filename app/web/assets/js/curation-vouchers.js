// Curation › Vouchers: find any voucher, or register a new one; both open the staff record.
import {bindForm, endpoint, filledFields, find, request, taxonPicker, voucherPicker} from "./core.js";

const open = (id) => window.location.assign(`/researcher/specimens/${endpoint(id)}`);

voucherPicker(find("voucher-picker"), (voucher) => open(voucher.specimen_id), {pageSize: 20});

const register = find("register");
const site = find("registration-site");
const newLocation = find("new-location");
function showLocationFields() {
  newLocation.hidden = newLocation.disabled = site.value !== "new";
}
site.addEventListener("change", showLocationFields);
showLocationFields();

taxonPicker(find("register-taxon"), (taxon) => {
  register.elements.taxon_id.value = taxon?.taxon_id ?? "";
});

bindForm("register", async (data) => {
  const payload = filledFields(data);
  if (payload.field_loc_id === "new") {
    delete payload.field_loc_id;
    payload.field_location = {};
    for (const [name, value] of Object.entries(payload)) {
      if (name.startsWith("site.")) {
        payload.field_location[name.slice("site.".length)] = value.trim();
        delete payload[name];
      }
    }
  }
  const voucher = await request("/api/specimen/create-new-specimen", {method: "POST", json: payload});
  open(voucher.specimen_id);
  return "Voucher registered.";
});

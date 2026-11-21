// My work: create a study or find a voucher. Each opens its own page.
import {bindForm, endpoint, filledFields, find, request, voucherPicker} from "./core.js";

bindForm("create-study", async (data) => {
  const study = await request("/api/chemistry/studies", {method: "POST", json: filledFields(data)});
  window.location.assign(`/researcher/studies/${endpoint(study.id)}`);
  return "Study created.";
});

voucherPicker(find("voucher-picker"), (voucher) => {
  window.location.assign(`/researcher/specimens/${endpoint(voucher.specimen_id)}`);
});


// My work: create a study (the first step for analytical results) or find a voucher. Each opens its own page.
import {bindForm, endpoint, filledFields, find, request, voucherPicker} from "./core.js";

bindForm("create-study", async (data) => {
  const study = await request("/api/chemistry/studies", {method: "POST", json: filledFields(data)});
  window.location.assign(`/researcher/studies/${endpoint(study.id)}`);
  return "Study created.";
});

voucherPicker(find("voucher-picker"), (voucher) => {
  window.location.assign(`/researcher/specimens/${endpoint(voucher.specimen_id)}`);
});


// The header's "New study" link opens the form beside the study list.
function openNewStudy() {
  if (location.hash !== "#new-study") return;
  const details = find("new-study");
  if (details?.tagName === "DETAILS") details.open = true;
  find("create-study")?.elements.title.focus();
}
window.addEventListener("hashchange", openNewStudy);
openNewStudy();

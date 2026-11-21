// Curation › Vouchers: find any voucher, or register a new one; both open the staff record.
import {bindForm, endpoint, filledFields, find, request, voucherPicker} from "./core.js";

const open = (id) => window.location.assign(`/researcher/specimens/${endpoint(id)}`);

voucherPicker(find("voucher-picker"), (voucher) => open(voucher.specimen_id), {pageSize: 20});

bindForm("register", async (data) => {
  const voucher = await request("/api/specimen/create-new-specimen", {method: "POST", json: filledFields(data)});
  open(voucher.specimen_id);
  return "Voucher registered.";
});

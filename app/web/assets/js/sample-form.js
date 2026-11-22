import {VOUCHER_ROLES, filledFields, node, requiredSelection, selectOptions, status, voucherLabel, voucherPicker} from "./core.js";

export function bindSampleFields(root) {
  const vouchers = [];
  const list = root.querySelector("#sample-vouchers");
  const picker = root.querySelector("#sample-voucher-picker");
  const site = root.querySelector("#sample-site");
  const siteVoucher = root.querySelector("#site-voucher-field");
  const siteLocation = root.querySelector("#site-location-field");
  const sameSite = siteVoucher.querySelector("select");
  const location = siteLocation.querySelector("input");
  const plantPart = root.querySelector('[name="plant_part"]');
  const note = root.querySelector('[name="plant_part_note"]');

  function renderVouchers() {
    list.replaceChildren(...vouchers.map((link, index) => {
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
      remove.addEventListener("click", () => { vouchers.splice(index, 1); renderVouchers(); });
      row.append(label, remove);
      return row;
    }));
    selectOptions(sameSite, vouchers.map(({voucher}) => ({id: voucher.specimen_id, label: voucherLabel(voucher)})),
      "Select a linked voucher", sameSite.value);
  }

  function renderRequirements() {
    siteVoucher.hidden = sameSite.disabled = site.value !== "voucher";
    siteLocation.hidden = location.disabled = site.value !== "field_location";
    note.required = plantPart.value === "other";
    root.querySelector("#plant-part-note-required").hidden = !note.required;
  }

  voucherPicker(picker, (voucher) => {
    if (vouchers.some((link) => link.voucher.specimen_id === voucher.specimen_id)) return;
    vouchers.push({voucher, role: vouchers.length ? "same_population" : "sampled_from_voucher"});
    renderVouchers();
  });
  site.addEventListener("change", renderRequirements);
  plantPart.addEventListener("change", renderRequirements);
  renderRequirements();

  return {
    payload(data) {
      if (!vouchers.length) {
        picker.querySelector(".picker-query").focus();
        status(picker.querySelector(".feedback"), "Select at least one voucher.", true);
        throw new Error("Select at least one voucher for the sample.");
      }
      const payload = filledFields(data);
      delete payload.site;
      if (site.value === "voucher") payload.site_specimen_id = requiredSelection(payload.site_specimen_id, "Select the site voucher.");
      if (site.value === "field_location") payload.field_loc_id = requiredSelection(payload.field_loc_id, "Enter a field location ID.");
      payload.vouchers = vouchers.map(({voucher, role}) => ({specimen_id: voucher.specimen_id, role}));
      return payload;
    },
    reset() {
      vouchers.length = 0;
      picker.querySelector(".picker-results").replaceChildren();
      status(picker.querySelector(".feedback"));
      renderVouchers();
      renderRequirements();
    },
  };
}

// Curator actions on the staff specimen record. Photographs update in place; other changes reload to show the saved state.
import {bindForm, endpoint, find, node, request, status, taxonPicker} from "./core.js";

const record = find("record");
const specimenId = record?.dataset.specimen;
const reload = () => window.location.reload();

if (find("release")) {
  bindForm("release", async (data) => {
    await request(`/api/specimen/${endpoint(specimenId)}/visibility`, {method: "PUT", json: {
      is_public: data.get("is_public") === "true", public_location: data.get("public_location"),
    }});
    reload();
    return "Saved.";
  });
}

if (find("redetermine")) {
  const form = find("redetermine");
  taxonPicker(find("redetermine-taxon"), (taxon) => {
    form.elements.taxon_id.value = taxon?.taxon_id ?? "";
    if (taxon && !form.elements.subnomen.value.trim()) form.elements.subnomen.value = taxon.name;
  });
  bindForm("redetermine", async (data) => {
    if (!data.get("taxon_id")) throw new Error("Choose a taxon first.");
    const payload = {specimen_id: specimenId, taxon_id: data.get("taxon_id")};
    for (const name of ["subnomen", "determiner_name", "determination_date"]) {
      if (data.get(name).trim()) payload[name] = data.get(name).trim();
    }
    await request("/api/revision/create-revision", {method: "POST", json: payload});
    reload();
    return "Determination saved.";
  });
}

// Collection details: only the fields the curator changed are sent, so untouched values are never rewritten.
const NUMBERS = new Set(["altitude", "gps_lat", "gps_long", "coordinate_uncertainty_m"]);

function changedFields(elements) {
  const changes = {};
  for (const element of elements) {
    const initial = element.tagName === "SELECT"
      ? [...element.options].find((option) => option.defaultSelected)?.value ?? ""
      : element.defaultValue;
    if (element.value === initial) continue;
    const value = element.value.trim();
    changes[element.name] = value === "" ? null : NUMBERS.has(element.name) ? Number(value) : value;
  }
  return changes;
}

if (find("edit-collection")) {
  bindForm("edit-collection", async (data, form) => {
    const site = form.querySelector("fieldset[data-field-loc]");
    const fields = [...form.querySelectorAll("input[name], select[name], textarea[name]")]
      .filter((element) => element.name !== "correction_reason");
    const specimenChanges = changedFields(fields.filter((element) => !site?.contains(element)));
    const siteChanges = site ? changedFields(fields.filter((element) => site.contains(element))) : {};
    if (!Object.keys(specimenChanges).length && !Object.keys(siteChanges).length) {
      throw new Error("Nothing has changed.");
    }
    const reason = data.get("correction_reason").trim() || undefined;
    if (Object.keys(specimenChanges).length) {
      await request(`/api/specimen/update-specimen?specimen_id=${endpoint(specimenId)}`,
        {method: "PUT", json: {...specimenChanges, correction_reason: reason}});
    }
    if (Object.keys(siteChanges).length) {
      await request(`/api/field-locations/update-field-loc?field_loc_id=${endpoint(site.dataset.fieldLoc)}`,
        {method: "PUT", json: {...siteChanges, correction_reason: reason}});
    }
    reload();
    return "Corrections saved.";
  });
}

// Photographs.
const gallery = find("photo-gallery");
const photoFeedback = find("photo-feedback");

function showState(figure, isPublic) {
  const chip = figure.querySelector(".photo-state");
  chip.textContent = isPublic ? "Approved" : "Not public";
  chip.classList.toggle("released", isPublic);
  const button = figure.querySelector(".photo-visibility");
  if (button) {
    button.textContent = isPublic ? "Withdraw" : "Approve";
    button.dataset.public = isPublic ? "false" : "true";
  }
}

function photoFigure(photo) {
  const figure = node("figure", "", "photo");
  figure.dataset.image = photo.image_id;
  const url = `/api/image/${endpoint(photo.image_id)}/original`;
  const link = node("a");
  link.href = url;
  const image = node("img");
  image.src = url;
  image.alt = `${photo.image_type ?? "Photograph"} photograph`;
  link.append(image);
  const caption = node("figcaption");
  const button = node("button", "", "text-button photo-visibility");
  button.type = "button";
  caption.append(node("span", "", "status-chip photo-state"), node("span", photo.image_type ?? "", "muted small"), button);
  figure.append(link, caption);
  showState(figure, Boolean(photo.is_public));
  return figure;
}

gallery?.addEventListener("click", async (event) => {
  const button = event.target.closest(".photo-visibility");
  if (!button) return;
  const figure = button.closest("figure");
  const makePublic = button.dataset.public === "true";
  button.disabled = true;
  status(photoFeedback, makePublic ? "Approving…" : "Withdrawing…");
  try {
    const result = await request(`/api/image/${endpoint(figure.dataset.image)}/visibility`,
      {method: "PUT", json: {is_public: makePublic}});
    showState(figure, result.is_public);
    status(photoFeedback, result.is_public
      ? "Photograph approved. It appears on the public page while this voucher is released."
      : "Photograph withdrawn from the public page.");
  } catch (error) {
    status(photoFeedback, error.message || "Request failed.", true);
  } finally {
    button.disabled = false;
  }
});

if (find("upload-photo")) {
  bindForm("upload-photo", async (data, form) => {
    const file = data.get("file");
    if (!(file instanceof File) || !file.size) throw new Error("Choose a JPEG image first.");
    const body = new FormData();
    body.append("file", file);
    const query = `specimen_id=${endpoint(specimenId)}&image_type=${endpoint(data.get("image_type"))}`;
    const photo = await request(`/api/image/upload-image?${query}`, {method: "POST", multipart: body});
    gallery.append(photoFigure(photo));
    gallery.hidden = false;
    find("photo-empty")?.remove();
    form.reset();
    status(photoFeedback, "");
    return `Uploaded ${file.name}. It is not public until you approve it.`;
  });
}

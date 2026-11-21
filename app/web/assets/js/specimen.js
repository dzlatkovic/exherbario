// Curator actions on the staff specimen record. After a change the page reloads to show the saved state.
import {bindForm, endpoint, find, request, taxonPicker} from "./core.js";

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

// Curator actions on the staff specimen record. After a change the page reloads to show the saved state.
import {bindForm, endpoint, find, request, selectOptions, status} from "./core.js";

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
  const query = find("taxon-query");
  async function searchTaxa() {
    const feedback = form.querySelector(".feedback");
    if (!query.value.trim()) return status(feedback, "Enter part of a taxon name.", true);
    const result = await request(`/api/taxonomy?query=${endpoint(query.value.trim())}&size=20`);
    selectOptions(form.elements.taxon_id, result.items.map((taxon) => ({id: taxon.taxon_id, label: `${taxon.name} (${taxon.rank})`})),
      result.total ? "Choose a taxon" : "No taxon matches", result.items.length === 1 ? result.items[0].taxon_id : "");
    status(feedback, result.total ? `${result.total} taxa.` : "No taxon matches. Add it to the taxonomy first.", !result.total);
  }
  find("taxon-search").addEventListener("click", () => searchTaxa().catch((error) => status(form.querySelector(".feedback"), error.message, true)));
  query.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchTaxa().catch((error) => status(form.querySelector(".feedback"), error.message, true));
    }
  });
  bindForm("redetermine", async (data) => {
    const payload = {specimen_id: specimenId, taxon_id: data.get("taxon_id")};
    for (const name of ["subnomen", "determiner_name", "determination_date"]) {
      if (data.get(name).trim()) payload[name] = data.get(name).trim();
    }
    await request("/api/revision/create-revision", {method: "POST", json: payload});
    reload();
    return "Determination saved.";
  });
}

for (const button of document.querySelectorAll(".photo-visibility")) {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await request(`/api/image/${endpoint(button.dataset.image)}/visibility`, {method: "PUT", json: {is_public: button.dataset.public === "true"}});
      reload();
    } catch (error) {
      button.textContent = error.message;
      button.disabled = false;
    }
  });
}

if (find("upload-photo")) {
  bindForm("upload-photo", async (data) => {
    const type = data.get("image_type");
    const body = new FormData();
    body.set("file", data.get("file"));
    await request(`/api/image/upload-image?specimen_id=${endpoint(specimenId)}&image_type=${endpoint(type)}`, {method: "POST", multipart: body});
    reload();
    return "Uploaded.";
  });
}

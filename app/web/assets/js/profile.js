// Private run page: correct a compound assignment (with a reason) and, for curators, release the run.
import {bindForm, bindPutButtons, endpoint, find, request, status} from "./core.js";

const profileId = find("profile").dataset.profile;
const form = find("correct");

find("compound-search").addEventListener("click", async () => {
  const feedback = form.querySelector(".feedback");
  const query = find("compound-query").value.trim();
  if (!query) return status(feedback, "Enter a name, CAS, CID or InChIKey.", true);
  status(feedback, "Searching…");
  try {
    const found = await request(`/api/chemistry/compounds/search?namespace=${find("compound-namespace").value}&q=${endpoint(query)}`);
    const select = form.elements.cid;
    select.replaceChildren(new Option("Mark as unidentified", ""),
      ...found.map((item) => new Option(`${item.title} · CID ${item.cid} · ${item.molecular_formula ?? ""}`, item.cid)));
    if (found.length) select.value = found[0].cid;
    status(feedback, found.length ? `${found.length} match${found.length === 1 ? "" : "es"}.` : "No PubChem match.", !found.length);
  } catch (error) {
    status(feedback, error.message, true);
  }
});

bindForm(form, async (data) => {
  const cid = data.get("cid") ? Number(data.get("cid")) : null;
  await request(`/api/chemistry/profiles/${endpoint(profileId)}/measurements/${endpoint(data.get("feature"))}/compound`,
    {method: "PUT", json: {cid, reason: data.get("reason").trim()}});
  window.location.reload();
  return "Saved.";
});

bindPutButtons();

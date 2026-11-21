// Published version page, for curators: link an article, register the dataset DOI, or withdraw the version.
import {bindForm, confirmAction, endpoint, filledFields, find, request} from "./core.js";

const panel = find("manage-version");
const base = `/api/depositions/${endpoint(panel.dataset.deposition)}/versions/${endpoint(panel.dataset.version)}`;
const reload = () => window.location.reload();

bindForm("link-article", async (data) => {
  await request(`${base}/article-doi`, {method: "PUT", json: {doi: data.get("doi").trim()}});
  reload();
  return "Article linked.";
});

if (find("dataset-doi")) {
  bindForm("dataset-doi", async (data) => {
    await request(`${base}/doi`, {method: "PUT", json: filledFields(data)});
    reload();
    return "Dataset DOI registered.";
  });
}

if (find("withdraw-version")) {
  bindForm("withdraw-version", async (data) => {
    if (!await confirmAction(`Withdraw version ${panel.dataset.version}?`,
      "Its data stop being served and the page shows your reason instead. This can't be undone.", "Withdraw")) {
      return "";
    }
    await request(`${base}/withdraw`, {method: "POST", json: {reason: data.get("reason").trim()}});
    reload();
    return "Version withdrawn.";
  });
}

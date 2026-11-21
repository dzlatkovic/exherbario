// Staff voucher page: look up compounds LOTUS reports for the voucher's taxon, review them, and publish them.
import {endpoint, node, request, status} from "./core.js";

const panel = document.getElementById("lotus");
if (panel) {
  const taxon = endpoint(panel.dataset.taxon);
  const feedback = panel.querySelector(".feedback");
  const results = document.getElementById("lotus-results");
  const button = document.getElementById("lotus-lookup");

  const reference = (item) => {
    const link = node("a", item.year || (item.doi ? "article" : "source"));
    link.href = item.doi ? `https://doi.org/${item.doi}` : `https://www.wikidata.org/wiki/${item.wikidata_id}`;
    link.rel = "noopener";
    link.target = "_blank";
    if (item.title) link.title = item.title;
    return link;
  };

  const show = (found) => {
    results.replaceChildren();
    if (!found.compounds.length) {
      status(feedback, "LOTUS reports no compounds for this taxon in Wikidata.");
      return;
    }
    const intro = `${found.compounds.length} compound${found.compounds.length === 1 ? "" : "s"} reported`
      + (found.truncated ? " (the list was cut at the first 1,500 rows)" : "")
      + (found.published_at ? `. A list was published on ${found.published_at.slice(0, 10)}; publishing again replaces it.` : ".");
    status(feedback, intro);
    const list = node("ul", "", "picker-results");
    for (const compound of found.compounds) {
      const item = node("li");
      const label = node("label", "", "check");
      const box = node("input");
      box.type = "checkbox";
      box.checked = true;
      box.value = compound.wikidata_id;
      const text = node("span");
      text.append(node("strong", compound.name));
      const detail = node("span", "", "muted small");
      detail.append([compound.inchikey !== compound.name && compound.inchikey, compound.cid && `CID ${compound.cid}`, compound.in_registry && "in your compound registry",
        `${compound.references.length} reference${compound.references.length === 1 ? "" : "s"}`].filter(Boolean).join(" · "));
      for (const ref of compound.references.slice(0, 3)) detail.append(" · ", reference(ref));
      text.append(detail);
      label.append(box, text);
      item.append(label);
      list.append(item);
    }
    const credit = node("p", "", "muted small");
    const source = node("a", found.source.name);
    source.href = found.source.url;
    source.rel = "noopener";
    source.target = "_blank";
    credit.append("From ", source, `, retrieved ${found.source.retrieved_at.slice(0, 10)}${found.source.stale ? " (an older copy: Wikidata is unreachable)" : ""}. ${found.source.license}. Cite: ${found.source.citation}`);
    const actions = node("div", "", "link-row");
    const publish = node("button", "Publish the checked compounds", "primary");
    publish.type = "button";
    publish.addEventListener("click", async () => {
      const boxes = [...list.querySelectorAll("input[type=checkbox]")];
      const chosen = boxes.filter((box) => box.checked).map((box) => box.value);
      publish.disabled = true;
      try {
        const done = await request(`/api/chemistry/lotus/taxa/${taxon}/published`, {method: "PUT",
          json: {review_id: found.review_id, wikidata_ids: chosen.length === boxes.length ? null : chosen}});
        status(feedback, `Published ${done.published} compound${done.published === 1 ? "" : "s"} for this taxon's public voucher pages.`);
      } catch (error) {
        status(feedback, error.message, true);
      } finally {
        publish.disabled = false;
      }
    });
    actions.append(publish);
    if (found.published_at) {
      const remove = node("button", "Remove the published list", "secondary");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        try {
          await request(`/api/chemistry/lotus/taxa/${taxon}/published`, {method: "DELETE"});
          status(feedback, "The published list was removed. Public pages no longer show it.");
        } catch (error) {
          status(feedback, error.message, true);
        }
      });
      actions.append(remove);
    }
    results.append(list, credit, actions);
  };

  button.addEventListener("click", async () => {
    button.disabled = true;
    status(feedback, "Looking up… Wikidata can take a few seconds.");
    try {
      show(await request(`/api/chemistry/lotus/taxa/${taxon}`));
    } catch (error) {
      status(feedback, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

"""Natural products reported in the literature for a taxon: LOTUS structure-organism pairs held in Wikidata.

The taxon is found through its GBIF key (Wikidata property P846). Compounds are items with a referenced
"found in taxon" (P703) statement for it. Since the May 2025 Wikidata Query Service split, the cited
articles live in the scholarly graph, so their DOIs and titles come from a second query.

Lookups are cached and only proposed; a curator publishes a taxon's list, which copies it into
taxon_literature_compound. Nothing here is a measurement on a voucher.
"""

import re

from fastapi import HTTPException
from sqlalchemy import delete, select

from app.chemistry.models import Compound, TaxonLiteratureCompound
from app.external.lookups import attribution, cached, http_get, peek, record_import, utc_now
from app.taxonomy.models import Taxonomy

WDQS = "https://query.wikidata.org/sparql"
WDQS_SCHOLARLY = "https://query-scholarly.wikidata.org/sparql"
QID = re.compile(r"^Q[1-9][0-9]{0,11}$")
MAX_ROWS = 1500
REFERENCE_BATCH = 200

COMPOUNDS = """
SELECT ?compound ?compoundLabel ?inchikey ?cid ?reference ?taxonName WHERE {{
  ?taxon wdt:P846 "{gbif_key}" .
  OPTIONAL {{ ?taxon wdt:P225 ?taxonName }}
  ?compound p:P703 ?statement .
  ?statement ps:P703 ?taxon ;
             prov:wasDerivedFrom/pr:P248 ?reference .
  OPTIONAL {{ ?compound wdt:P235 ?inchikey }}
  OPTIONAL {{ ?compound wdt:P662 ?cid }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,mul" . }}
}} LIMIT {limit}
"""

REFERENCES = """
SELECT ?reference ?doi ?title ?date WHERE {{
  VALUES ?reference {{ {items} }}
  OPTIONAL {{ ?reference wdt:P356 ?doi }}
  OPTIONAL {{ ?reference wdt:P1476 ?title }}
  OPTIONAL {{ ?reference wdt:P577 ?date }}
}}
"""


def _qid(uri) -> str | None:
    value = str(uri or "").rsplit("/", 1)[-1]
    return value if QID.match(value) else None


def _bindings(answer) -> list[dict]:
    rows = ((answer or {}).get("results") or {}).get("bindings") if isinstance(answer, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Wikidata returned an unexpected answer.")
    return [{key: (value or {}).get("value") for key, value in row.items()} for row in rows if isinstance(row, dict)]


def _sparql(endpoint: str, query: str):
    return http_get(endpoint, params={"query": query, "format": "json"},
                    headers={"Accept": "application/sparql-results+json"})


def _fetch(gbif_key: str):
    rows = _bindings(_sparql(WDQS, COMPOUNDS.format(gbif_key=gbif_key, limit=MAX_ROWS)))
    if not rows:
        return None
    compounds, references, taxon_name = {}, set(), None
    for row in rows:
        compound, reference = _qid(row.get("compound")), _qid(row.get("reference"))
        if not compound or not reference:
            continue
        taxon_name = taxon_name or row.get("taxonName")
        entry = compounds.setdefault(compound, {"wikidata_id": compound, "name": None, "inchikey": None, "cid": None,
                                                "references": []})
        label = row.get("compoundLabel")
        if label and label != compound:
            entry["name"] = entry["name"] or label
        entry["inchikey"] = entry["inchikey"] or row.get("inchikey")
        if row.get("cid", "").isdigit():
            entry["cid"] = entry["cid"] or int(row["cid"])
        if reference not in entry["references"]:
            entry["references"].append(reference)
        references.add(reference)
    details = {}
    ordered = sorted(references)
    for start in range(0, len(ordered), REFERENCE_BATCH):
        items = " ".join(f"wd:{qid}" for qid in ordered[start:start + REFERENCE_BATCH])
        for row in _bindings(_sparql(WDQS_SCHOLARLY, REFERENCES.format(items=items))):
            qid = _qid(row.get("reference"))
            if qid:
                found = details.setdefault(qid, {"wikidata_id": qid, "doi": None, "title": None, "year": None})
                found["doi"] = found["doi"] or (row.get("doi") or "").lower() or None
                found["title"] = found["title"] or row.get("title")
                found["year"] = found["year"] or (row.get("date") or "")[:4] or None
    for entry in compounds.values():
        entry["name"] = entry["name"] or entry["inchikey"] or entry["wikidata_id"]
        entry["references"] = [details.get(qid) or {"wikidata_id": qid, "doi": None, "title": None, "year": None}
                               for qid in entry["references"]]
    return {"taxon_name": taxon_name, "truncated": len(rows) >= MAX_ROWS,
            "compounds": sorted(compounds.values(), key=lambda item: (-len(item["references"]), item["name"].lower()))}


def _taxon(db, taxon_id: str) -> Taxonomy:
    taxon = db.get(Taxonomy, taxon_id)
    if taxon is None:
        raise HTTPException(404, "Taxon not found.")
    return taxon


def _key(taxon) -> str:
    return f"taxon:{taxon.gbif_key}"


def lookup(db, taxon_id: str) -> dict:
    """The compounds LOTUS reports for a taxon, for a curator to review. Nothing is stored except the cache."""
    taxon = _taxon(db, taxon_id)
    result = cached("lotus", _key(taxon), lambda: _fetch(taxon.gbif_key))
    data = result.data or {"compounds": [], "taxon_name": None, "truncated": False}
    registered = set(db.scalars(select(Compound.cid).where(
        Compound.cid.in_([item["cid"] for item in data["compounds"] if item["cid"]])))) if data["compounds"] else set()
    published = db.scalars(select(TaxonLiteratureCompound.confirmed_at)
                           .where(TaxonLiteratureCompound.taxon_id == taxon.taxon_id).limit(1)).first()
    return {"taxon": {"taxon_id": taxon.taxon_id, "name": taxon.taxon_name, "gbif_key": taxon.gbif_key},
            "wikidata_taxon_name": data["taxon_name"], "truncated": data["truncated"],
            "compounds": [{**item, "in_registry": item["cid"] in registered} for item in data["compounds"]],
            "published_at": published.isoformat() + "Z" if published else None,
            "source": attribution(result)}


def publish(db, taxon_id: str, wikidata_ids: list[str] | None, actor) -> dict:
    """Copy the reviewed lookup (all compounds, or the chosen ones) to the taxon's public list."""
    taxon = _taxon(db, taxon_id)
    result = peek("lotus", _key(taxon))
    if result is None or not result.found:
        raise HTTPException(409, "Look up this taxon in LOTUS first, then publish what you reviewed.")
    compounds = result.data["compounds"]
    if wikidata_ids is not None:
        chosen = set(wikidata_ids)
        unknown = chosen - {item["wikidata_id"] for item in compounds}
        if unknown:
            raise HTTPException(422, f"Not in the reviewed lookup: {', '.join(sorted(unknown))}.")
        compounds = [item for item in compounds if item["wikidata_id"] in chosen]
    if not compounds:
        raise HTTPException(422, "Choose at least one compound to publish.")
    now = utc_now()
    db.execute(delete(TaxonLiteratureCompound).where(TaxonLiteratureCompound.taxon_id == taxon.taxon_id))
    db.add_all(TaxonLiteratureCompound(
        taxon_id=taxon.taxon_id, wikidata_id=item["wikidata_id"], name=item["name"][:500], inchikey=item["inchikey"],
        cid=item["cid"], references=item["references"], retrieved_at=result.retrieved_at, confirmed_by=actor.user_id,
        confirmed_at=now) for item in compounds)
    record_import(db, provider="lotus", external_id=f"GBIF {taxon.gbif_key}", record_type="taxon_literature",
                  record_id=taxon.taxon_id, fields={"compounds": len(compounds), "of": len(result.data["compounds"])},
                  confirmed_by=actor.user_id, retrieved_at=result.retrieved_at)
    db.commit()
    return {"taxon_id": taxon.taxon_id, "published": len(compounds)}


def withdraw(db, taxon_id: str):
    taxon = _taxon(db, taxon_id)
    db.execute(delete(TaxonLiteratureCompound).where(TaxonLiteratureCompound.taxon_id == taxon.taxon_id))
    db.commit()


def published(db, taxon_id: str | None) -> dict | None:
    """The curator-published list for a taxon, for public pages, with registry links and attribution."""
    if not taxon_id:
        return None
    rows = db.scalars(select(TaxonLiteratureCompound).where(TaxonLiteratureCompound.taxon_id == taxon_id)
                      .order_by(TaxonLiteratureCompound.name)).all()
    if not rows:
        return None
    registered = set(db.scalars(select(Compound.cid).where(Compound.cid.in_([row.cid for row in rows if row.cid]))))
    return {"taxon_id": taxon_id, "retrieved_at": rows[0].retrieved_at, "source": attribution("lotus"),
            "compounds": [{"wikidata_id": row.wikidata_id, "name": row.name, "inchikey": row.inchikey, "cid": row.cid,
                           "in_registry": row.cid in registered, "references": row.references} for row in rows]}

"""Find an institution in ROR and Index Herbariorum to fill the registration form.

The lookup proposes names and identifiers; the curator still chooses the permanent code and saves the form.
Published deposition versions keep the institution details they were published with.
"""

import re

from sqlalchemy import select

from app.config import settings
from app.external.lookups import LookupUnavailable, attribution, cached, enabled_providers, http_get

from .models import Institution

ROR_API = "https://api.ror.org/v2/organizations"
IH_API = "https://sweetgum.nybg.org/science/api/v1/institutions"
ROR_ID = re.compile(r"^(?:https?://ror\.org/)?(0[a-hj-km-np-tv-z0-9]{6}[0-9]{2})$", re.IGNORECASE)
IH_CODE = re.compile(r"^[A-Za-z]{1,8}$")
MAX_RESULTS = 10


def ror_id(value: str | None) -> str | None:
    match = ROR_ID.match((value or "").strip())
    return match.group(1).lower() if match else None


def _first(values):
    return next((value for value in values if isinstance(value, str) and value.strip()), None)


def _ror_record(item: dict) -> dict | None:
    identifier = ror_id(item.get("id"))
    if identifier is None:
        return None
    names = [name for name in item.get("names") or [] if isinstance(name, dict) and name.get("value")]
    by_type = lambda kind: [name["value"] for name in names if kind in (name.get("types") or [])]
    place = next((location.get("geonames_details") or {} for location in item.get("locations") or []
                  if isinstance(location, dict)), {})
    website = _first(link.get("value") for link in item.get("links") or []
                     if isinstance(link, dict) and link.get("type") == "website")
    return {"ror_id": identifier, "ror": f"https://ror.org/{identifier}",
            "name": _first(by_type("ror_display")) or _first(by_type("label")) or names[0]["value"] if names else None,
            "acronyms": by_type("acronym"), "aliases": by_type("alias") + by_type("label"),
            "city": place.get("name"), "country": place.get("country_name"),
            "types": [kind for kind in item.get("types") or [] if isinstance(kind, str)],
            "status": item.get("status"), "website": website}


def _ror_fetch(query: str):
    headers = {"Client-Id": settings.ROR_CLIENT_ID.strip()} if settings.ROR_CLIENT_ID.strip() else None
    identifier = ror_id(query)
    if identifier:
        data = http_get(f"{ROR_API}/{identifier}", headers=headers)
        return None if data is None else {"items": [data]}
    data = http_get(ROR_API, params={"query": query}, headers=headers)
    if not isinstance(data, dict) or not isinstance(data.get("items", []), list):
        raise ValueError("ROR returned an unexpected answer.")
    return {"items": data.get("items", [])[:MAX_RESULTS]} if data.get("items") else None


def _ih_record(item: dict) -> dict | None:
    code = item.get("code")
    if not isinstance(code, str) or not IH_CODE.match(code.strip()):
        return None
    address = item.get("address") or {}
    contact = item.get("contact") or {}
    return {"code": code.strip().upper(), "organization": item.get("organization"),
            "division": item.get("division") or None, "department": item.get("department") or None,
            "city": address.get("physicalCity") or address.get("postalCity") or None,
            "country": address.get("physicalCountry") or address.get("postalCountry") or None,
            "status": item.get("currentStatus"), "website": contact.get("webUrl") or None,
            "url": f"https://sweetgum.nybg.org/science/ih/herbarium-details/?irn={item['irn']}" if item.get("irn")
            else "https://sweetgum.nybg.org/science/ih/"}


def _ih_fetch(params: dict):
    """Search Index Herbariorum by `code` or `organization`. A code search keeps exact matches only."""
    data = http_get(f"{IH_API}/search", params=params)
    if data is None:
        return None
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Index Herbariorum returned an unexpected answer.")
    if "code" in params:
        rows = [row for row in rows if isinstance(row, dict) and str(row.get("code", "")).upper() == params["code"]]
    return {"data": rows[:MAX_RESULTS]} if rows else None


def _search(provider, key, fetch, parse, rows_key):
    result = cached(provider, key, fetch)
    rows = (result.data or {}).get(rows_key, []) if result.found else []
    return [record for record in (parse(row) for row in rows if isinstance(row, dict)) if record], result


def lookup(db, query: str) -> dict:
    """Candidates from ROR and Index Herbariorum. One registry failing does not hide the other's results."""
    query = " ".join(query.split())
    on = enabled_providers() & {"ror", "index_herbariorum"}
    if not on:
        raise LookupUnavailable("ror", "ROR and Index Herbariorum lookups are turned off on this instance.", 503)
    answer = {"query": query, "ror": [], "index_herbariorum": [], "errors": {}, "sources": {}}
    searches = []
    if "ror" in on:
        searches.append(("ror", lambda: [_search("ror", f"q:{query.lower()}", lambda: _ror_fetch(query),
                                                 _ror_record, "items")]))
    if "index_herbariorum" in on:
        def herbaria():
            found = []
            if IH_CODE.match(query):
                found.append(_search("index_herbariorum", f"code:{query.upper()}",
                                     lambda: _ih_fetch({"code": query.upper()}), _ih_record, "data"))
            found.append(_search("index_herbariorum", f"organization:{query.lower()}",
                                 lambda: _ih_fetch({"organization": query}), _ih_record, "data"))
            return found
        searches.append(("index_herbariorum", herbaria))
    for provider, run in searches:
        try:
            parts = run()
        except LookupUnavailable as error:
            answer["errors"][provider] = error.message
            continue
        seen = set()
        for records, result in parts:
            for record in records:
                key = record.get("ror_id") or record.get("code")
                if key not in seen:
                    seen.add(key)
                    answer[provider].append(record)
            answer["sources"][provider] = attribution(result)
    registered_ror = dict(db.execute(select(Institution.ror_id, Institution.code).where(Institution.ror_id.is_not(None))).all())
    registered_ih = dict(db.execute(select(Institution.index_herbariorum_code, Institution.code)
                                    .where(Institution.index_herbariorum_code.is_not(None))).all())
    for record in answer["ror"]:
        record["registered_code"] = registered_ror.get(record["ror_id"])
    for record in answer["index_herbariorum"]:
        record["registered_code"] = registered_ih.get(record["code"])
    if not answer["ror"] and not answer["index_herbariorum"] and len(answer["errors"]) == len(searches):
        raise LookupUnavailable("ror", "ROR and Index Herbariorum can't be reached right now.")
    return answer

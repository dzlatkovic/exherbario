"""Check that this machine reaches each enabled provider and that its answers still parse.

    python -m app.external.check

Each provider is queried once, live and without the cache, with a known record. Nothing is stored.
"""

import sys
import time

from app.deposition import registries
from app.external.lookups import enabled_providers, timeout
from app.publication import crossref

CHECKS = {
    "gbif": "Achillea millefolium",
    "crossref": "10.5555/12345678",  # Crossref's own test DOI
    "ror": "University of Belgrade",
    "index_herbariorum": "NY",
}


def check(provider: str) -> str:
    if provider == "gbif":
        from pygbif import species
        answer = species.name_backbone(scientificName=CHECKS["gbif"], verbose=True, timeout=timeout())
        usage = (answer.get("usage") or {}) if isinstance(answer, dict) else {}
        if not usage.get("key"):
            raise ValueError(f"no usage in the answer: {str(answer)[:200]}")
        return f"{usage.get('name')} (key {usage['key']}, {answer.get('diagnostics', {}).get('matchType')})"
    if provider == "crossref":
        message = crossref._fetch(CHECKS["crossref"])
        if message is None:
            raise ValueError("the test DOI was not found")
        return crossref.fields_from(message, CHECKS["crossref"])["title"] or "(no title)"
    if provider == "ror":
        answer = registries._ror_fetch(CHECKS["ror"]) or {"items": []}
        records = [registries._ror_record(item) for item in answer["items"]]
        if not any(records):
            raise ValueError("no parsable organization in the answer")
        return f"{records[0]['name']} ({records[0]['ror']})"
    answer = registries._ih_fetch({"code": CHECKS["index_herbariorum"]}) or {"data": []}  # exact code matches
    records = [registries._ih_record(item) for item in answer["data"]]
    if not any(records):
        raise ValueError("no parsable herbarium in the answer")
    search = registries._ih_fetch({"organization": "New York Botanical"}) or {"data": []}
    return f"{records[0]['code']} · {records[0]['organization']}; name search found {len(search['data'])}"


def main() -> int:
    failed = 0
    on = enabled_providers()
    for provider in CHECKS:
        if provider not in on:
            print(f"{provider}: turned off (EXTERNAL_LOOKUPS)")
            continue
        started = time.monotonic()
        try:
            result = check(provider)
            print(f"{provider}: ok in {time.monotonic() - started:.1f} s — {result}")
        except Exception as error:  # report every provider, whatever went wrong
            failed += 1
            print(f"{provider}: FAILED after {time.monotonic() - started:.1f} s — {type(error).__name__}: {error}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

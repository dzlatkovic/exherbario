"""Fill a bibliography entry from Crossref. The lookup proposes values; the curator edits and saves them."""

import html
import re
from urllib.parse import quote

from app.config import settings
from app.external.lookups import attribution, cached, http_get

DOI = re.compile(r"^10\.\d{4,9}/\S+$")
PREFIXES = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
TAGS = re.compile(r"<[^>]+>")
# The bibliography form's limits; longer values are proposed in full with a warning, never cut.
LIMITS = {"title": 500, "journal": 300}
FIELDS = ("doi", "title", "journal", "year", "abstract")


class DOINotFound(Exception):
    pass


def normalize_doi(value: str) -> str:
    doi = PREFIXES.sub("", value.strip()).strip().lower()
    if not DOI.match(doi):
        raise ValueError("Enter a DOI such as 10.3390/plants13010001.")
    return doi


def _text(value) -> str | None:
    if isinstance(value, list):
        value = next((item for item in value if isinstance(item, str) and item.strip()), None)
    if not isinstance(value, str):
        return None
    text = " ".join(html.unescape(TAGS.sub(" ", value)).split())
    return text or None


def _abstract(value) -> str | None:
    text = _text(value)
    if text and text.lower().startswith("abstract "):
        text = text[len("abstract "):].lstrip(" :.")
    return text or None


def _year(message: dict) -> str | None:
    for field in ("published-print", "published-online", "published", "issued"):
        parts = (message.get(field) or {}).get("date-parts") or []
        if parts and parts[0] and isinstance(parts[0][0], int):
            return f"{parts[0][0]:04d}"
    return None


def _fetch(doi: str):
    params = {"mailto": settings.EXTERNAL_CONTACT_EMAIL.strip()} if settings.EXTERNAL_CONTACT_EMAIL.strip() else None
    data = http_get(f"https://api.crossref.org/works/{quote(doi, safe='/')}", params=params)
    if data is None:
        return None
    message = data.get("message") if isinstance(data, dict) else None
    if not isinstance(message, dict):
        raise ValueError("Crossref returned an unexpected answer.")
    return message


def fields_from(message: dict, doi: str) -> dict:
    """Bibliography fields from a Crossref work record."""
    return {"doi": normalize_doi(message.get("DOI") or doi), "title": _text(message.get("title")),
            "journal": _text(message.get("container-title")) or _text(message.get("short-container-title")),
            "year": _year(message), "abstract": _abstract(message.get("abstract"))}


def lookup(value: str, existing_dois: dict[str, str]) -> dict:
    """Proposed bibliography fields for a DOI, with warnings and attribution. `existing_dois` maps normalized
    DOIs already in the bibliography to their publication IDs."""
    doi = normalize_doi(value)
    result = cached("crossref", f"work:{doi}", lambda: _fetch(doi))
    if not result.found:
        raise DOINotFound(f"Crossref has no record of {doi}. It may be registered with another agency, such as "
                          "DataCite for datasets; check the DOI, or enter the details by hand.")
    message = result.data
    fields = fields_from(message, doi)
    warnings = []
    if message.get("type") and message["type"] != "journal-article":
        warnings.append(f"Crossref lists this DOI as a {message['type'].replace('-', ' ')}, not a journal article.")
    for name, label in (("title", "title"), ("journal", "journal"), ("year", "year")):
        if not fields[name]:
            warnings.append(f"Crossref gives no {label}; enter it before saving.")
    if not fields["abstract"]:
        warnings.append("Crossref has no abstract for this DOI; enter one before saving.")
    else:
        warnings.append("The abstract is the publisher's text; check that you may store and show it.")
    for name, limit in LIMITS.items():
        if fields[name] and len(fields[name]) > limit:
            warnings.append(f"The {name} is longer than {limit} characters; shorten it before saving.")
    authors = [{"given": author.get("given"), "family": author.get("family") or author.get("name"),
                "orcid": author.get("ORCID")} for author in message.get("author") or [] if isinstance(author, dict)]
    return {"fields": fields, "authors": authors, "type": message.get("type"), "publisher": message.get("publisher"),
            "existing_pub_id": existing_dois.get(fields["doi"]), "warnings": warnings,
            "source": attribution(result, f"https://doi.org/{fields['doi']}")}

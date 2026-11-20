from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as RoutePath
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.db import get_db
from app.deposition.services import DepositionService


ROOT = Path(__file__).resolve().parent
router = APIRouter(include_in_schema=False)
templates = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
}


def page_url(api_url):
    return api_url.replace("/api/depositions/public/", "/depositions/", 1) if api_url else None


@router.get("/researcher", response_class=HTMLResponse)
def researcher():
    # Structure images in the PubChem review come from PubChem; other pages keep the stricter policy.
    headers = {**PAGE_HEADERS, "Content-Security-Policy": PAGE_HEADERS["Content-Security-Policy"]
               + "; img-src 'self' https://pubchem.ncbi.nlm.nih.gov"}
    return HTMLResponse(templates.get_template("researcher.html").render(), headers=headers)


def profile_vouchers(snapshot):
    """Pair each profile with its vouchers: one per profile up to schema 2, the sample's links from schema 3."""
    by_id = {voucher["id"]: voucher for voucher in snapshot.get("vouchers") or []}
    pairs = {}
    for profile in snapshot["profiles"]:
        if "voucher" in profile:
            pairs[profile["id"]] = [(profile["voucher"], {"role": profile["sample"].get("voucher_relationship")})]
        else:
            pairs[profile["id"]] = [(by_id[link["id"]], link) for link in profile["sample"]["vouchers"]]
    linked = {voucher["id"] for vouchers in pairs.values() for voucher, _ in vouchers}
    return pairs, [voucher for voucher in snapshot.get("vouchers") or [] if voucher["id"] not in linked]


@router.get("/depositions/{institution}/{accession}/versions/{number}", response_class=HTMLResponse)
def public_deposition(institution: str, accession: str, number: int = RoutePath(ge=1, le=2_147_483_647),
                      db: Session = Depends(get_db)):
    try:
        status, record = DepositionService(db).public_version(institution, accession, number)
    except HTTPException as error:
        page = templates.get_template("deposition.html").render(problem=error.detail)
        return HTMLResponse(page, status_code=error.status_code, headers=PAGE_HEADERS)
    snapshot = record.get("snapshot")
    credits = ", ".join(credit["name"] for credit in snapshot["contributors"]) if snapshot else None
    citation = (
        f"{credits or record['institution_name']}. ({record['published_at'][:4]}). "
        f"{record['title']} (Version {record['version']}) [Data set]. "
        f"{record['institution_name']}. {record['institution']} {record['accession']}."
    )
    link = record["dataset_doi"]["url"] if record.get("dataset_doi") else record.get("identifier")
    if link:
        citation += f" {link}"
    linked, unprofiled = profile_vouchers(snapshot) if snapshot else ({}, [])
    page = templates.get_template("deposition.html").render(
        record=record, snapshot=snapshot, citation=citation, linked=linked, unprofiled=unprofiled,
        current_url=page_url(record["url"]), latest_url=page_url(record["latest_version_url"]),
        previous_url=page_url(snapshot["supersedes"]) if snapshot else None,
    )
    return HTMLResponse(page, status_code=status, headers=PAGE_HEADERS)

from pathlib import Path

from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi import Path as RoutePath
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deposition.models import Deposition
from app.deposition.services import DepositionService
from app.users.exceptions import UserDoesNotExist, UserInvalidPassword
from app.users.services import UserServices
from app.users.session import (CSRF_COOKIE, csrf_valid, end_session, role_of, safe_next, same_origin,
                               session_payload, start_session)


ROOT = Path(__file__).resolve().parent
router = APIRouter(include_in_schema=False)
templates = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
}


def page_url(api_url):
    return api_url.replace("/api/depositions/public/", "/depositions/", 1) if api_url else None


def viewer(request: Request) -> dict | None:
    """The signed-in account for page chrome, or None. Pages never decide visibility from this."""
    payload = session_payload(request)
    user = UserServices.get_user_by_id(payload["user_id"]) if payload else None
    if not user or not user.is_active or payload.get("role") != role_of(user):
        return None
    return {"id": user.user_id, "name": f"{user.name} {user.surname}".strip() or user.email, "email": user.email,
            "curator": bool(user.is_superuser)}


def render(request: Request, name: str, *, status: int = 200, headers: dict | None = None, **context):
    page = templates.get_template(name).render(viewer=viewer(request), csrf=request.cookies.get(CSRF_COOKIE, ""),
                                               path=request.url.path, **context)
    return HTMLResponse(page, status_code=status, headers={**PAGE_HEADERS, **(headers or {})})


def sign_in_redirect(request: Request):
    target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    return RedirectResponse(f"/sign-in?next={quote(target, safe='')}", status_code=303)


from . import catalog_pages, chemistry_pages, curation_pages, staff_pages, work_pages  # noqa: E402  (their pages use render above)

router.include_router(catalog_pages.router)
router.include_router(chemistry_pages.router)
router.include_router(curation_pages.router)
router.include_router(staff_pages.router)
router.include_router(work_pages.router)


@router.get("/sign-in", response_class=HTMLResponse)
def sign_in_page(request: Request, next: str | None = None):
    if viewer(request):
        return RedirectResponse(safe_next(next), status_code=303)
    return render(request, "sign-in.html", next=safe_next(next))


@router.post("/sign-in", response_class=HTMLResponse)
def sign_in(request: Request, email: str = Form(..., max_length=320), password: str = Form(..., max_length=500),
            next: str = Form("/researcher", max_length=2000)):
    target = safe_next(next)
    if not same_origin(request):
        return render(request, "sign-in.html", status=403, next=target, problem="Sign in from this site's own page.")
    try:
        user = UserServices.login_user(email.strip(), password)
    except (UserDoesNotExist, UserInvalidPassword):
        return render(request, "sign-in.html", status=401, next=target, email=email,
                      problem="The email or password is not correct.")
    if not user.is_active:
        return render(request, "sign-in.html", status=403, next=target, problem="This account is not active.")
    response = RedirectResponse(target, status_code=303)
    start_session(request, response, user)
    return response


@router.post("/sign-out")
def sign_out(request: Request, csrf_token: str = Form("", max_length=200)):
    response = RedirectResponse("/sign-in", status_code=303)
    # A forged sign-out is harmless but refused anyway; an expired page just signs out again later.
    if csrf_valid(request, csrf_token) and same_origin(request):
        end_session(request, response)
    return response


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
def public_deposition(request: Request, institution: str, accession: str,
                      number: int = RoutePath(ge=1, le=2_147_483_647), db: Session = Depends(get_db)):
    try:
        status, record = DepositionService(db).public_version(institution, accession, number)
    except HTTPException as error:
        return render(request, "deposition.html", status=error.status_code, problem=error.detail)
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
    viewing = viewer(request)
    manage = None
    if viewing and viewing["curator"]:
        manage = db.scalar(select(Deposition.id).where(Deposition.institution == record["institution"],
                                                       Deposition.accession == record["accession"]))
    return render(request, "deposition.html", status=status, manage=manage,
                  record=record, snapshot=snapshot, citation=citation, linked=linked, unprofiled=unprofiled,
                  current_url=page_url(record["url"]), latest_url=page_url(record["latest_version_url"]),
                  previous_url=page_url(snapshot["supersedes"]) if snapshot else None)

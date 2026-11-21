"""ORCID linking and sign-in pages. See app/users/orcid.py for the flow."""

import hmac
import secrets

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.external.lookups import record_import, utc_now
from app.users import orcid
from app.users.models import User
from app.users.session import _secure, csrf_valid, safe_next, same_origin, start_session

router = APIRouter(include_in_schema=False)
FLOW_COOKIE = "herbar_orcid_flow"
PENDING_COOKIE = "herbar_orcid_pending"


def _web():
    from app.web import routes
    return routes


def _redirect_uri(request: Request) -> str:
    origin = settings.PUBLIC_BASE_URL.strip().rstrip("/") or str(request.base_url).rstrip("/")
    return f"{origin}/orcid/callback"


def _cookie(request, response, name, value, minutes=orcid.FLOW_MINUTES):
    response.set_cookie(name, value, max_age=minutes * 60, path="/", httponly=True, samesite="lax",
                        secure=_secure(request))


def _drop(request, response, *names):
    for name in names:
        response.delete_cookie(name, path="/", samesite="lax", secure=_secure(request))


def _page(request, status=200, **context):
    return _web().render(request, "orcid.html", status=status, orcid_url=orcid.base_url(), **context)


def _signed_in_user(request, db) -> User | None:
    viewer = _web().viewer(request)
    return db.get(User, viewer["id"]) if viewer else None


def _start(request, mode, **values):
    state = secrets.token_urlsafe(24)
    response = RedirectResponse(orcid.authorize_url(state, _redirect_uri(request)), status_code=303)
    _cookie(request, response, FLOW_COOKIE, orcid.seal("orcid-flow", state=state, mode=mode, **values))
    return response


@router.get("/account/orcid/link")
def start_link(request: Request, db: Session = Depends(get_db)):
    if not orcid.enabled():
        return _page(request, 404, problem="ORCID linking is not set up on this instance.")
    user = _signed_in_user(request, db)
    if user is None:
        return _web().sign_in_redirect(request)
    return _start(request, "link", user_id=user.user_id)


@router.get("/sign-in/orcid")
def start_sign_in(request: Request, next: str | None = None):
    if not (orcid.enabled() and settings.ORCID_SIGN_IN):
        return _page(request, 404, problem="Signing in with ORCID is not set up on this instance.")
    return _start(request, "sign-in", next=safe_next(next))


@router.get("/orcid/callback")
def callback(request: Request, state: str = "", code: str = "", error: str = "", db: Session = Depends(get_db)):
    flow = orcid.unseal(request.cookies.get(FLOW_COOKIE), "orcid-flow")
    if flow is None or not state or not hmac.compare_digest(flow["state"], state):
        response = _page(request, 400, problem="This ORCID sign-in expired or was not started here. Please start again.")
        _drop(request, response, FLOW_COOKIE)
        return response
    if error or not code:
        response = _page(request, 400, problem="ORCID did not confirm an iD"
                         + (" because access was not granted." if error == "access_denied" else ".")
                         + " Nothing was changed.")
        _drop(request, response, FLOW_COOKIE)
        return response
    try:
        identity = orcid.exchange(code, _redirect_uri(request))
    except orcid.ORCIDError as problem:
        response = _page(request, 502, problem=str(problem))
        _drop(request, response, FLOW_COOKIE)
        return response

    if flow["mode"] == "sign-in":
        user = db.scalar(select(User).where(User.orcid == identity["orcid"]))
        if user is None or not user.is_active:
            response = _web().render(request, "sign-in.html", status=403, next=flow.get("next", "/researcher"),
                                     problem="No active account here is linked to that ORCID iD. "
                                     "Sign in with your email, then link your iD from My work.")
        else:
            response = RedirectResponse(safe_next(flow.get("next")), status_code=303)
            start_session(request, response, user)
        _drop(request, response, FLOW_COOKIE)
        return response

    user = _signed_in_user(request, db)
    if user is None or user.user_id != flow.get("user_id"):
        response = _page(request, 403, problem="Sign in to the account you started from, then link your iD again.")
        _drop(request, response, FLOW_COOKIE)
        return response
    response = RedirectResponse("/account/orcid/confirm", status_code=303)
    _cookie(request, response, PENDING_COOKIE, orcid.seal("orcid-pending", user_id=user.user_id, **identity))
    _drop(request, response, FLOW_COOKIE)
    return response


def _pending(request, db):
    pending = orcid.unseal(request.cookies.get(PENDING_COOKIE), "orcid-pending")
    user = _signed_in_user(request, db)
    if pending is None or user is None or user.user_id != pending.get("user_id"):
        return None, user, None
    holder = db.scalar(select(User).where(User.orcid == pending["orcid"], User.user_id != user.user_id))
    return pending, user, holder


@router.get("/account/orcid/confirm")
def confirm_page(request: Request, db: Session = Depends(get_db)):
    pending, user, holder = _pending(request, db)
    if user is None:
        return _web().sign_in_redirect(request)
    if pending is None:
        return _page(request, 400, problem="There is no ORCID iD waiting to be linked. Start again from My work.")
    return _page(request, pending=pending, account=user,
                 problem="That ORCID iD is already linked to another account here." if holder else None)


@router.post("/account/orcid/confirm")
def confirm(request: Request, csrf_token: str = Form("", max_length=200), db: Session = Depends(get_db)):
    if not (csrf_valid(request, csrf_token) and same_origin(request)):
        return _page(request, 403, problem="This form expired. Start again from My work.")
    pending, user, holder = _pending(request, db)
    if pending is None or holder is not None:
        return _page(request, 409 if holder else 400,
                     problem="That ORCID iD is already linked to another account here." if holder
                     else "There is no ORCID iD waiting to be linked. Start again from My work.")
    previous = user.orcid
    user.orcid, user.orcid_name, user.orcid_linked_at = pending["orcid"], pending.get("name"), utc_now()
    record_import(db, provider="orcid", external_id=pending["orcid"], record_type="account", record_id=user.user_id,
                  fields={"name": pending.get("name"), "replaced": previous}, confirmed_by=user.user_id,
                  retrieved_at=user.orcid_linked_at)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _page(request, 409, problem="That ORCID iD is already linked to another account here.")
    response = RedirectResponse("/researcher", status_code=303)
    _drop(request, response, PENDING_COOKIE)
    return response


@router.post("/account/orcid/unlink")
def unlink(request: Request, csrf_token: str = Form("", max_length=200), db: Session = Depends(get_db)):
    user = _signed_in_user(request, db)
    if user is None:
        return _web().sign_in_redirect(request)
    if csrf_valid(request, csrf_token) and same_origin(request):
        user.orcid = user.orcid_name = user.orcid_linked_at = None
        db.commit()
    return RedirectResponse("/researcher", status_code=303)

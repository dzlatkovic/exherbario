"""Browser sessions: the signed token in an HttpOnly cookie, plus a CSRF token for writes.

API clients keep using `Authorization: Bearer`. A request authenticated by the cookie must send the CSRF
cookie's value in the X-CSRF-Token header (or a csrf_token form field) for anything other than GET or HEAD.
"""

import hmac
import secrets
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import Response

from app.config import settings
from app.users.services import decodeJWT, signJWT

SESSION_COOKIE = "herbar_session"
CSRF_COOKIE = "herbar_csrf"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _secure(request: Request) -> bool:
    return request.url.scheme == "https" or settings.PUBLIC_BASE_URL.startswith("https://")


def role_of(user) -> str:
    return "super_user" if user.is_superuser else "classic_user"


def start_session(request: Request, response: Response, user) -> str:
    token = signJWT(user.user_id, role_of(user))["access_token"]
    csrf = secrets.token_urlsafe(32)
    options = {"max_age": settings.TOKEN_DURATION, "path": "/", "samesite": "lax", "secure": _secure(request)}
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **options)
    # Readable by the page's scripts, which echo it back in X-CSRF-Token.
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **options)
    return csrf


def end_session(request: Request, response: Response):
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/", samesite="lax", secure=_secure(request))


def session_payload(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    payload = decodeJWT(token) if token else None
    return payload if payload and isinstance(payload.get("user_id"), str) else None


def csrf_valid(request: Request, submitted: str | None = None) -> bool:
    expected = request.cookies.get(CSRF_COOKIE)
    given = submitted if submitted is not None else request.headers.get(CSRF_HEADER)
    return bool(expected and given) and hmac.compare_digest(expected, given)


def same_origin(request: Request) -> bool:
    """For form posts: a browser-sent Origin (or Referer) must be this site."""
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return True
    origin = urlsplit(source)
    return (origin.scheme, origin.netloc) == (request.url.scheme, request.url.netloc)


def safe_next(target: str | None, default: str = "/researcher") -> str:
    """Only local paths, so the sign-in redirect cannot send anyone to another site."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return default
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return default
    return target

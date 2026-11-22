"""An optional shared password in front of the whole site, for an alpha or a private trial.

Set SITE_PASSWORD in .env to turn it on; leave it empty (the default) to keep the site open. A visitor enters the
password once on /site-password, and a cookie keeps the site open in that browser for SITE_PASSWORD_DAYS. Changing
the password signs every browser out of the lock. API clients that send a valid `Authorization: Bearer` token pass.
"""

import hashlib
import hmac

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.users.services import decodeJWT

SITE_COOKIE = "herbar_site"
OPEN_PATHS = ("/site-password", "/assets/herbar/", "/favicon.ico")


def enabled() -> bool:
    return bool(settings.SITE_PASSWORD)


def cookie_value() -> str:
    return hmac.new(settings.USER_SECRET.encode(), b"site-password:" + settings.SITE_PASSWORD.encode(),
                    hashlib.sha256).hexdigest()


def password_matches(given: str) -> bool:
    return enabled() and hmac.compare_digest(given.encode(), settings.SITE_PASSWORD.encode())


def unlocked(request: Request) -> bool:
    if not enabled() or request.url.path.startswith(OPEN_PATHS):
        return True
    if hmac.compare_digest(request.cookies.get(SITE_COOKIE, ""), cookie_value()):
        return True
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    return scheme.lower() == "bearer" and bool(token) and bool(decodeJWT(token))


def locked_response(request: Request):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "This site is password-protected."}, status_code=401)
    from urllib.parse import quote
    target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    return RedirectResponse(f"/site-password?next={quote(target, safe='')}", status_code=303)

"""Link an account to the ORCID iD its holder authenticates at ORCID, and sign in with a linked iD.

Uses ORCID's three-legged OAuth with the /authenticate scope: ORCID confirms who the person is and returns
their iD and public name. The access token is not kept; the iD is written only after the account holder
confirms the link on this site.
"""

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
import requests

from app.config import settings
from app.external.lookups import http_post_form

ORCID_ID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
FLOW_MINUTES = 10


class ORCIDError(Exception):
    pass


def enabled() -> bool:
    return bool(settings.ORCID_CLIENT_ID.strip() and settings.ORCID_CLIENT_SECRET.strip())


def base_url() -> str:
    return settings.ORCID_URL.strip().rstrip("/") or "https://orcid.org"


def valid_orcid(value: str) -> bool:
    """Format and ISO 7064 11,2 check digit."""
    if not isinstance(value, str) or not ORCID_ID.match(value):
        return False
    digits = value.replace("-", "")
    total = 0
    for digit in digits[:-1]:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return digits[-1] == ("X" if check == 10 else str(check))


def authorize_url(state: str, redirect_uri: str) -> str:
    query = urlencode({"client_id": settings.ORCID_CLIENT_ID.strip(), "response_type": "code",
                       "scope": "/authenticate", "redirect_uri": redirect_uri, "state": state})
    return f"{base_url()}/oauth/authorize?{query}"


def exchange(code: str, redirect_uri: str) -> dict:
    """Trade the one-time code for the authenticated iD and name. The token itself is discarded."""
    try:
        answer = http_post_form(f"{base_url()}/oauth/token", {
            "client_id": settings.ORCID_CLIENT_ID.strip(), "client_secret": settings.ORCID_CLIENT_SECRET.strip(),
            "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri})
    except (requests.RequestException, ValueError) as error:
        raise ORCIDError("ORCID could not confirm the sign-in. Try again in a moment.") from error
    orcid = answer.get("orcid") if isinstance(answer, dict) else None
    if not valid_orcid(orcid):
        raise ORCIDError("ORCID returned an unexpected answer.")
    name = answer.get("name")
    return {"orcid": orcid, "name": name.strip()[:200] if isinstance(name, str) and name.strip() else None}


def seal(purpose: str, minutes: int = FLOW_MINUTES, **values) -> str:
    """A short-lived signed value for a cookie, so the flow's state can't be forged or replayed later."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"purpose": purpose, "exp": expires, **values}, settings.USER_SECRET, algorithm=settings.ALGORITHM)


def unseal(token: str | None, purpose: str) -> dict | None:
    if not token:
        return None
    try:
        values = jwt.decode(token, settings.USER_SECRET, algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    return values if values.get("purpose") == purpose else None

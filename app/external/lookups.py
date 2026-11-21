"""Cached, time-limited lookups in external registries.

Lookups only read. They return proposed values with attribution; nothing reaches the archive until a curator
saves a form, and then `record_import` notes where the accepted values came from.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import requests
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db import SessionLocal
from app.external.models import ExternalImport, ExternalLookupCache
from app.external.providers import NOT_FOUND_TTL_DAYS, PROVIDERS

CONNECT_TIMEOUT = 5
# A lookup answer is a few kilobytes; anything larger means the provider ignored the query and sent a dump.
MAX_RESPONSE_BYTES = 2_000_000


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LookupUnavailable(Exception):
    """The provider is turned off, unreachable or answered with something unusable."""

    def __init__(self, provider: str, message: str, code: int = 502):
        super().__init__(message)
        self.provider = provider
        self.message = message
        self.code = code


@dataclass
class LookupResult:
    provider: str
    data: Any
    found: bool
    retrieved_at: datetime
    cached: bool
    stale: bool


def enabled_providers() -> set[str]:
    return {name.strip() for name in settings.EXTERNAL_LOOKUPS.split(",") if name.strip() in PROVIDERS}


def require(provider: str):
    if provider not in enabled_providers():
        raise LookupUnavailable(provider, f"{PROVIDERS[provider].name} lookups are turned off on this instance.", 503)


def timeout():
    return CONNECT_TIMEOUT, settings.EXTERNAL_TIMEOUT_SECONDS


def user_agent():
    contact = settings.EXTERNAL_CONTACT_EMAIL.strip()
    origin = settings.PUBLIC_BASE_URL.strip()
    details = "; ".join(part for part in (origin and f"+{origin}", contact and f"mailto:{contact}") if part)
    return f"ExHerbario/1.0 ({details})" if details else "ExHerbario/1.0"


def http_get(url: str, params: dict | None = None, headers: dict | None = None):
    """GET a JSON document. Returns None for 404. The whole request must finish within the connect and read
    timeouts together and stay under MAX_RESPONSE_BYTES: a server that keeps trickling data, which the read
    timeout alone does not catch, is cut off. Tests replace this function; see app/conftest.py."""
    deadline = time.monotonic() + CONNECT_TIMEOUT + settings.EXTERNAL_TIMEOUT_SECONDS
    with requests.get(url, params=params, headers={"User-Agent": user_agent(), "Accept": "application/json",
                                                   **(headers or {})}, timeout=timeout(), stream=True) as response:
        if response.status_code == 404:
            return None
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_content(64 * 1024):
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError(f"The answer from {url} is larger than expected; the query may have been ignored.")
            if time.monotonic() > deadline:
                raise requests.Timeout(f"{url} did not finish answering in time.")
    return json.loads(body)


def http_post_form(url: str, data: dict):
    """POST a form and read a JSON answer, with the same deadline and size limit as http_get. Errors raise."""
    deadline = time.monotonic() + CONNECT_TIMEOUT + settings.EXTERNAL_TIMEOUT_SECONDS
    with requests.post(url, data=data, headers={"User-Agent": user_agent(), "Accept": "application/json"},
                       timeout=timeout(), stream=True) as response:
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_content(64 * 1024):
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError(f"The answer from {url} is larger than expected.")
            if time.monotonic() > deadline:
                raise requests.Timeout(f"{url} did not finish answering in time.")
    return json.loads(body)


def _digest(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def cached(provider: str, key: str, fetch: Callable[[], Any]) -> LookupResult:
    """Return a fresh cached answer, or call `fetch` (None means not found) and remember the answer.
    If the provider fails, an expired answer is served with stale=True; without one, LookupUnavailable."""
    require(provider)
    now = utc_now()
    digest = _digest(key)
    with SessionLocal() as db:
        row = db.get(ExternalLookupCache, (provider, digest))
        if row is not None:
            ttl = timedelta(days=PROVIDERS[provider].ttl_days if row.found else NOT_FOUND_TTL_DAYS)
            if now - row.fetched_at < ttl:
                return LookupResult(provider, row.payload, row.found, row.fetched_at, cached=True, stale=False)
        try:
            data = fetch()
            json.dumps(data)  # only JSON-safe answers are cached
        except LookupUnavailable:
            raise
        except (requests.RequestException, ValueError, TypeError) as error:
            if row is not None and row.found:
                return LookupResult(provider, row.payload, True, row.fetched_at, cached=True, stale=True)
            raise LookupUnavailable(provider, f"{PROVIDERS[provider].name} can't be reached right now.") from error
        if row is None:
            row = ExternalLookupCache(provider=provider, key_digest=digest, lookup_key=key[:2000])
            db.add(row)
        row.found, row.payload, row.fetched_at = data is not None, data, now
        try:
            db.commit()
        except IntegrityError:
            # Another request stored the same answer first; use its entry rather than failing this one.
            db.rollback()
            stored = db.get(ExternalLookupCache, (provider, digest))
            if stored is not None:
                return LookupResult(provider, stored.payload, stored.found, stored.fetched_at, cached=True, stale=False)
            raise
    return LookupResult(provider, data, data is not None, now, cached=False, stale=False)


def peek(provider: str, key: str) -> LookupResult | None:
    """The cached answer for a key, however old, without asking the provider."""
    with SessionLocal() as db:
        row = db.get(ExternalLookupCache, (provider, _digest(key)))
        if row is None:
            return None
        return LookupResult(provider, row.payload, row.found, row.fetched_at, cached=True, stale=False)


def attribution(result_or_provider, url: str | None = None) -> dict:
    """What a form shows beside proposed values, and what `record_import` stores."""
    result = result_or_provider if isinstance(result_or_provider, LookupResult) else None
    provider = PROVIDERS[result.provider if result else result_or_provider]
    source = {"provider": provider.key, "name": provider.name, "license": provider.license,
              "citation": provider.citation, "url": url or provider.homepage}
    if result:
        source.update(retrieved_at=result.retrieved_at.isoformat() + "Z", cached=result.cached, stale=result.stale)
    return source


def parse_retrieved_at(value: str | None):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed


def record_import(db, *, provider: str, external_id: str, record_type: str, record_id: str, fields: dict,
                  confirmed_by: str, retrieved_at: datetime | None = None):
    """Note, in the caller's transaction, which values a curator accepted from a provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    entry = ExternalImport(provider=provider, external_id=str(external_id)[:300], record_type=record_type,
                           record_id=record_id, fields=fields, retrieved_at=retrieved_at,
                           confirmed_by=confirmed_by, confirmed_at=utc_now())
    db.add(entry)
    return entry


def provider_status() -> list[dict]:
    on = enabled_providers()
    return [{**attribution(key), "enabled": key in on} for key in PROVIDERS]

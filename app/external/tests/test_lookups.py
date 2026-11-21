"""The shared lookup layer: caching, expiry, stale answers, switches, timeouts and the offline test guard."""

from datetime import timedelta

import pytest
import requests

from app.config import settings
from app.external import lookups
from app.external.lookups import LookupUnavailable, cached
from app.external.models import ExternalLookupCache
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices, signJWT


def curator_headers():
    curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
    return {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}


class TestLookups(TestClass):
    def test_answers_are_cached_and_reused(self):
        calls = []

        def fetch():
            calls.append(1)
            return {"title": "Flora"}
        first = cached("crossref", "doi:10.1/x", fetch)
        second = cached("crossref", "doi:10.1/x", fetch)
        assert first.data == second.data == {"title": "Flora"}
        assert (first.cached, second.cached, len(calls)) == (False, True, 1)
        assert second.retrieved_at == first.retrieved_at

    def test_not_found_is_remembered_briefly(self):
        calls = []
        assert not cached("ror", "q:nowhere", lambda: calls.append(1)).found
        assert not cached("ror", "q:nowhere", lambda: calls.append(1)).found
        assert len(calls) == 1
        with TestingSessionLocal() as db:
            row = db.query(ExternalLookupCache).one()
            row.fetched_at -= timedelta(days=2)
            db.commit()
        cached("ror", "q:nowhere", lambda: calls.append(1))
        assert len(calls) == 2

    def test_expired_answer_is_served_stale_while_the_provider_is_down(self):
        cached("ror", "q:belgrade", lambda: {"items": [1]})
        with TestingSessionLocal() as db:
            row = db.query(ExternalLookupCache).one()
            row.fetched_at -= timedelta(days=31)
            db.commit()

        def down():
            raise requests.ConnectionError("offline")
        stale = cached("ror", "q:belgrade", down)
        assert stale.data == {"items": [1]} and stale.stale and stale.cached
        with pytest.raises(LookupUnavailable) as error:
            cached("ror", "q:elsewhere", down)
        assert error.value.code == 502 and "can't be reached" in error.value.message

    def test_unusable_answers_are_not_cached(self):
        def broken():
            raise ValueError("not JSON")
        with pytest.raises(LookupUnavailable):
            cached("crossref", "doi:10.1/bad", broken)
        with TestingSessionLocal() as db:
            assert db.query(ExternalLookupCache).count() == 0

    def test_providers_can_be_switched_off(self, monkeypatch):
        headers = curator_headers()
        monkeypatch.setattr(settings, "EXTERNAL_LOOKUPS", "gbif")
        with pytest.raises(LookupUnavailable) as error:
            cached("crossref", "doi:10.1/x", lambda: {})
        assert error.value.code == 503 and "turned off" in error.value.message
        status = {item["provider"]: item for item in client.get("/api/external/providers", headers=headers).json()}
        assert status["gbif"]["enabled"] and not status["crossref"]["enabled"]
        assert status["gbif"]["license"] == "CC BY 4.0" and "Thiers" in status["index_herbariorum"]["citation"]
        assert client.get("/api/external/providers").status_code == 403

    def test_requests_carry_timeouts_and_a_contact(self, monkeypatch):
        seen = {}

        chunks = [b'{"ok": ', b"true}"]

        class Response:
            status_code = 200

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def raise_for_status(self):
                pass

            def iter_content(self, _size):
                yield from chunks

        def fake_get(url, params=None, headers=None, timeout=None, stream=False):
            seen.update(url=url, headers=headers, timeout=timeout, stream=stream)
            return Response()
        monkeypatch.setattr(lookups.requests, "get", fake_get)
        monkeypatch.setattr(settings, "EXTERNAL_CONTACT_EMAIL", "herbarium@example.edu")
        monkeypatch.setattr(settings, "EXTERNAL_TIMEOUT_SECONDS", 7.5)
        assert lookups.http_get("https://api.example.org/x") == {"ok": True}
        assert seen["timeout"] == (5, 7.5) and seen["stream"] is True
        assert "mailto:herbarium@example.edu" in seen["headers"]["User-Agent"]

        # A provider that ignores the query and streams a whole dump is cut off, not waited for.
        chunks[:] = [b"[" + b"0," * 600_000] * 3
        with pytest.raises(ValueError, match="larger than expected"):
            lookups.http_get("https://api.example.org/dump")
        clock = iter([0, 1, 100])
        monkeypatch.setattr(lookups.time, "monotonic", lambda: next(clock))
        chunks[:] = [b"[1,", b"2]"]
        with pytest.raises(requests.Timeout, match="in time"):
            lookups.http_get("https://api.example.org/slow")

    def test_a_concurrent_lookup_reuses_the_answer_stored_first(self):
        key = "work:10.1/race"

        def fetch_while_another_request_stores():
            # A second request for the same uncached key finishes first and stores its answer.
            with TestingSessionLocal() as other:
                other.add(ExternalLookupCache(provider="crossref", key_digest=lookups._digest(key), lookup_key=key,
                                              found=True, payload={"title": "stored first"}, fetched_at=lookups.utc_now()))
                other.commit()
            return {"title": "fetched second"}
        result = cached("crossref", key, fetch_while_another_request_stores)
        assert result.data == {"title": "stored first"} and result.cached
        with TestingSessionLocal() as db:
            assert db.query(ExternalLookupCache).count() == 1

    def test_tests_never_reach_the_network(self):
        with pytest.raises(requests.ConnectionError, match="disabled in tests"):
            requests.get("https://api.gbif.org/v1/species/1", timeout=1)

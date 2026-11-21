"""Linking an ORCID iD that ORCID authenticated, and signing in with it, with recorded ORCID token answers."""

from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from fastapi.testclient import TestClient

from app.config import settings
from app.external.models import ExternalImport
from app.main import app
from app.tests import TestClass, TestingSessionLocal
from app.tests.test_record_pages import signed_in
from app.users import orcid
from app.users.models import User
from app.users.services import UserServices

HTTP = "app.users.orcid.http_post_form"
IDS = {"code-ana": {"orcid": "0000-0002-1825-0097", "name": "Ana Petrović"},
       "code-other": {"orcid": "0000-0001-5109-3700", "name": "Marko Jovanović"}}


def token_answer(url, data):
    assert url == "https://sandbox.orcid.org/oauth/token"
    assert data["grant_type"] == "authorization_code" and data["client_secret"] == "secret-123"
    if data["code"] not in IDS:
        raise requests.HTTPError("400 invalid_grant")
    return {"access_token": "discarded", "token_type": "bearer", "refresh_token": "discarded",
            "expires_in": 631138518, "scope": "/authenticate", **IDS[data["code"]]}


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "ORCID_CLIENT_ID", "APP-TEST")
    monkeypatch.setattr(settings, "ORCID_CLIENT_SECRET", "secret-123")
    monkeypatch.setattr(settings, "ORCID_URL", "https://sandbox.orcid.org")
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.setattr(HTTP, token_answer)


def start(web, path):
    response = web.get(path, follow_redirects=False)
    assert response.status_code == 303, response.text
    target = urlsplit(response.headers["location"])
    return target, parse_qs(target.query)


def back_from_orcid(web, state, code):
    return web.get("/orcid/callback", params={"state": state, "code": code}, follow_redirects=False)


class TestORCID(TestClass):
    def setup_method(self):
        super().setup_method()
        UserServices.create_user("Ana", "Petrović", "ana@example.org", "password")
        UserServices.create_user("Marko", "Jovanović", "marko@example.org", "password")

    def test_check_digit(self):
        assert orcid.valid_orcid("0000-0002-1825-0097") and orcid.valid_orcid("0000-0002-1694-233X")
        assert not orcid.valid_orcid("0000-0002-1825-0098") and not orcid.valid_orcid("0000-0002-1825")

    def test_off_until_configured(self):
        web = signed_in("ana@example.org")
        assert "Link your ORCID iD" not in web.get("/researcher").text
        assert web.get("/account/orcid/link", follow_redirects=False).status_code == 404
        assert "Sign in with ORCID" not in TestClient(app).get("/sign-in").text

    def test_link_after_confirmation(self, configured):
        web = signed_in("ana@example.org")
        assert "Link your ORCID iD" in web.get("/researcher").text
        target, query = start(web, "/account/orcid/link")
        assert (target.scheme, target.netloc, target.path) == ("https", "sandbox.orcid.org", "/oauth/authorize")
        assert query["scope"] == ["/authenticate"] and query["client_id"] == ["APP-TEST"]
        assert query["redirect_uri"] == ["http://testserver/orcid/callback"]

        assert back_from_orcid(web, "forged-state", "code-ana").status_code == 400
        target, query = start(web, "/account/orcid/link")
        returned = back_from_orcid(web, query["state"][0], "code-ana")
        assert returned.status_code == 303 and returned.headers["location"] == "/account/orcid/confirm"
        with TestingSessionLocal() as db:
            assert db.query(User).filter_by(email="ana@example.org").one().orcid is None  # not until confirmed

        page = web.get("/account/orcid/confirm").text
        assert "Ana Petrović" in page and "https://sandbox.orcid.org/0000-0002-1825-0097" in page
        assert web.post("/account/orcid/confirm", data={"csrf_token": "wrong"}).status_code == 403
        linked = web.post("/account/orcid/confirm", data={"csrf_token": web.cookies.get("herbar_csrf")},
                          follow_redirects=False)
        assert linked.status_code == 303
        with TestingSessionLocal() as db:
            user = db.query(User).filter_by(email="ana@example.org").one()
            assert (user.orcid, user.orcid_name, user.name) == ("0000-0002-1825-0097", "Ana Petrović", "Ana")
            entry = db.query(ExternalImport).one()
            assert (entry.provider, entry.record_type, entry.record_id) == ("orcid", "account", user.user_id)
            assert entry.confirmed_by == user.user_id and entry.fields == {"name": "Ana Petrović", "replaced": None}
        assert "Confirmed by ORCID for Ana Petrović" in web.get("/researcher").text
        assert 'data-orcid="0000-0002-1825-0097"' in web.get("/researcher/depositions/new").text
        assert web.get("/account/orcid/confirm").status_code == 400  # the pending link is used up

        # The same iD can't be linked to a second account.
        other = signed_in("marko@example.org")
        _, query = start(other, "/account/orcid/link")
        back_from_orcid(other, query["state"][0], "code-ana")
        assert "already linked to another account" in other.get("/account/orcid/confirm").text
        refused = other.post("/account/orcid/confirm", data={"csrf_token": other.cookies.get("herbar_csrf")})
        assert refused.status_code == 409

        web.post("/account/orcid/unlink", data={"csrf_token": web.cookies.get("herbar_csrf")})
        with TestingSessionLocal() as db:
            assert db.query(User).filter_by(email="ana@example.org").one().orcid is None

    def test_sign_in_with_a_linked_id(self, configured):
        web = signed_in("ana@example.org")
        _, query = start(web, "/account/orcid/link")
        back_from_orcid(web, query["state"][0], "code-ana")
        web.post("/account/orcid/confirm", data={"csrf_token": web.cookies.get("herbar_csrf")})

        visitor = TestClient(app)
        assert "Sign in with ORCID" in visitor.get("/sign-in").text
        _, query = start(visitor, "/sign-in/orcid?next=/researcher/depositions/new")
        signed = back_from_orcid(visitor, query["state"][0], "code-ana")
        assert signed.status_code == 303 and signed.headers["location"] == "/researcher/depositions/new"
        assert visitor.cookies.get("herbar_session")

        stranger = TestClient(app)
        _, query = start(stranger, "/sign-in/orcid")
        refused = back_from_orcid(stranger, query["state"][0], "code-other")
        assert refused.status_code == 403 and "No active account here is linked" in refused.text
        assert not stranger.cookies.get("herbar_session")

    def test_orcid_errors_change_nothing(self, configured, monkeypatch):
        web = signed_in("ana@example.org")
        _, query = start(web, "/account/orcid/link")
        denied = web.get("/orcid/callback", params={"state": query["state"][0], "error": "access_denied"})
        assert denied.status_code == 400 and "access was not granted" in denied.text

        _, query = start(web, "/account/orcid/link")
        assert back_from_orcid(web, query["state"][0], "expired-code").status_code == 502

        def offline(*_args, **_kwargs):
            raise requests.ConnectionError("no route")
        monkeypatch.setattr(HTTP, offline)
        _, query = start(web, "/account/orcid/link")
        down = back_from_orcid(web, query["state"][0], "code-ana")
        assert down.status_code == 502 and "could not confirm" in down.text
        with TestingSessionLocal() as db:
            assert db.query(User).filter(User.orcid.is_not(None)).count() == 0
            assert db.query(ExternalImport).count() == 0

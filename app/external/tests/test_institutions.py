"""Finding institutions in ROR and Index Herbariorum, with recorded-style registry answers."""

import requests

from app.config import settings
from app.deposition.models import Institution
from app.external.models import ExternalImport
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices, signJWT

HTTP = "app.deposition.registries.http_get"
ROR_BELGRADE = {
    "id": "https://ror.org/02qsmb048", "status": "active", "types": ["education", "funder"],
    "names": [{"value": "University of Belgrade", "types": ["ror_display", "label"], "lang": "en"},
              {"value": "Univerzitet u Beogradu", "types": ["label"], "lang": "sr"},
              {"value": "UB", "types": ["acronym"], "lang": None}],
    "locations": [{"geonames_id": 792680, "geonames_details": {"name": "Belgrade", "country_name": "Serbia",
                                                               "country_code": "RS"}}],
    "links": [{"type": "website", "value": "https://www.bg.ac.rs"}, {"type": "wikipedia", "value": "https://en.wikipedia.org/wiki/University_of_Belgrade"}],
}
IH_BEOU = {"irn": 124816, "code": "BEOU", "organization": "University of Belgrade",
           "division": "Faculty of Biology", "department": "Institute of Botany and Botanical Garden Jevremovac",
           "currentStatus": "Active",
           "address": {"physicalCity": "Belgrade", "physicalCountry": "Serbia"},
           "contact": {"webUrl": "http://www.bio.bg.ac.rs"}}


def registries(url, params=None, headers=None):
    params = params or {}
    if url == "https://api.ror.org/v2/organizations":
        return {"number_of_results": 1, "items": [ROR_BELGRADE]} if "belgrade" in params["query"].lower() or params["query"] == "BEOU" else {"number_of_results": 0, "items": []}
    if url == "https://api.ror.org/v2/organizations/02qsmb048":
        return ROR_BELGRADE
    if url.endswith("/institutions/search") and "code" in params:
        # A near miss in the answer is dropped: only the exact code is kept.
        return {"meta": {"hits": 2}, "data": [{**IH_BEOU, "code": "BEO"}, IH_BEOU]} if params["code"] == "BEOU" else None
    if url.endswith("/institutions/search"):
        return {"meta": {"hits": 1}, "data": [IH_BEOU]} if "belgrade" in params["organization"].lower() else None
    raise AssertionError(url)


class TestInstitutionLookup(TestClass):
    def setup_method(self):
        super().setup_method()
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        self.curator_id = curator.user_id
        self.curator = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        researcher = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
        self.researcher = {"Authorization": "Bearer " + signJWT(researcher.user_id, "classic_user")["access_token"]}

    def lookup(self, query):
        return client.get("/api/institutions/lookup", params={"q": query}, headers=self.curator)

    def test_both_registries_are_searched(self, monkeypatch):
        calls = []

        def fake(url, params=None, headers=None):
            calls.append((url, params, headers))
            return registries(url, params, headers)
        monkeypatch.setattr(HTTP, fake)
        monkeypatch.setattr(settings, "ROR_CLIENT_ID", "client-123")
        assert client.get("/api/institutions/lookup", params={"q": "BEOU"}).status_code == 403
        assert client.get("/api/institutions/lookup", params={"q": "BEOU"}, headers=self.researcher).status_code == 403

        found = self.lookup("Belgrade")
        assert found.status_code == 200, found.text
        found = found.json()
        assert found["ror"] == [{
            "ror_id": "02qsmb048", "ror": "https://ror.org/02qsmb048", "name": "University of Belgrade",
            "acronyms": ["UB"], "aliases": ["University of Belgrade", "Univerzitet u Beogradu"],
            "city": "Belgrade", "country": "Serbia", "types": ["education", "funder"], "status": "active",
            "website": "https://www.bg.ac.rs", "registered_code": None}]
        herbarium = found["index_herbariorum"][0]
        assert (herbarium["code"], herbarium["division"], herbarium["city"]) == ("BEOU", "Faculty of Biology", "Belgrade")
        assert herbarium["url"].endswith("irn=124816") and herbarium["registered_code"] is None
        assert found["errors"] == {}
        assert found["sources"]["ror"]["license"] == "CC0 1.0"
        assert "Thiers" in found["sources"]["index_herbariorum"]["citation"]
        assert ("https://api.ror.org/v2/organizations", {"query": "Belgrade"}, {"Client-Id": "client-123"}) in calls

        by_code = self.lookup("beou").json()
        assert [item["code"] for item in by_code["index_herbariorum"]] == ["BEOU"]  # code hit first, not repeated
        assert self.lookup("https://ror.org/02qsmb048").json()["ror"][0]["ror_id"] == "02qsmb048"
        before = len(calls)
        self.lookup("Belgrade")
        assert len(calls) == before  # served from the cache

    def test_registration_from_a_lookup_is_logged_and_marked(self, monkeypatch):
        monkeypatch.setattr(HTTP, registries)
        found = self.lookup("Belgrade").json()
        retrieved = found["sources"]["ror"]["retrieved_at"]
        entry = {"code": "beou", "name": found["ror"][0]["name"], "ror_id": found["ror"][0]["ror_id"],
                 "index_herbariorum_code": found["index_herbariorum"][0]["code"],
                 "sources": [{"provider": "ror", "external_id": "https://ror.org/02qsmb048", "retrieved_at": retrieved},
                             {"provider": "index_herbariorum", "external_id": "beou", "retrieved_at": retrieved}]}
        wrong = {**entry, "sources": [{"provider": "ror", "external_id": "05a28rw58"}]}
        assert client.post("/api/institutions", headers=self.curator, json=wrong).status_code == 422
        created = client.post("/api/institutions", headers=self.curator, json=entry)
        assert created.status_code == 201, created.text
        assert created.json() == {"code": "BEOU", "name": "University of Belgrade", "index_herbariorum_code": "BEOU",
                                  "ror": "https://ror.org/02qsmb048"}
        with TestingSessionLocal() as db:
            logged = {row.provider: row for row in db.query(ExternalImport).all()}
            assert set(logged) == {"ror", "index_herbariorum"}
            assert logged["ror"].external_id == "02qsmb048" and logged["ror"].record_id == "BEOU"
            assert logged["index_herbariorum"].fields == {"name": "University of Belgrade", "identifier": "BEOU"}
            assert logged["ror"].retrieved_at is not None and logged["ror"].confirmed_by == self.curator_id
            assert db.get(Institution, "BEOU").ror_id == "02qsmb048"

        again = self.lookup("Belgrade").json()
        assert again["ror"][0]["registered_code"] == "BEOU" and again["index_herbariorum"][0]["registered_code"] == "BEOU"
        repeat = client.post("/api/institutions", headers=self.curator, json=entry)
        assert repeat.status_code == 201
        with TestingSessionLocal() as db:
            assert db.query(ExternalImport).count() == 2  # an unchanged re-registration logs nothing new

    def test_one_registry_down_still_shows_the_other(self, monkeypatch):
        def ror_down(url, params=None, headers=None):
            if "ror.org" in url:
                raise requests.ConnectionError("no route")
            return registries(url, params, headers)
        monkeypatch.setattr(HTTP, ror_down)
        partial = self.lookup("BEOU").json()
        assert partial["ror"] == [] and partial["index_herbariorum"][0]["code"] == "BEOU"
        assert "can't be reached" in partial["errors"]["ror"]

        def all_down(*_args, **_kwargs):
            raise requests.ConnectionError("no route")
        monkeypatch.setattr(HTTP, all_down)
        assert self.lookup("Novi Sad").status_code == 502
        monkeypatch.setattr(settings, "EXTERNAL_LOOKUPS", "index_herbariorum")
        only_ih = self.lookup("BEOU").json()  # cached IH answer; ROR is not queried at all
        assert only_ih["index_herbariorum"] and "ror" not in only_ih["errors"] and only_ih["ror"] == []
        monkeypatch.setattr(settings, "EXTERNAL_LOOKUPS", "gbif")
        assert self.lookup("BEOU").status_code == 503

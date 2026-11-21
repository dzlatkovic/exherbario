"""Filling a bibliography entry from Crossref, with a recorded-style Crossref work record."""

import requests

from app.config import settings
from app.external.models import ExternalImport
from app.publication.models import Publication
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices, signJWT

HTTP = "app.publication.crossref.http_get"
DOI = "10.3390/plants13010001"
WORK = {"status": "ok", "message-type": "work", "message": {
    "DOI": "10.3390/plants13010001", "type": "journal-article", "publisher": "MDPI AG",
    "title": ["Essential Oil of <i>Achillea millefolium</i> L. from Serbia"],
    "container-title": ["Plants"], "short-container-title": ["Plants"],
    "published-online": {"date-parts": [[2023, 12, 19]]}, "published-print": {"date-parts": [[2024, 1]]},
    "issued": {"date-parts": [[2023, 12, 19]]},
    "abstract": "<jats:title>Abstract</jats:title><jats:p>Hydrodistilled oil was analysed by GC&#x2013;MS.</jats:p>",
    "author": [{"given": "Ana", "family": "Petrović", "ORCID": "https://orcid.org/0000-0002-1825-0097"},
               {"given": "Marko", "family": "Jovanović"}],
}}
BOOK = {"message": {"DOI": "10.1007/978-3-030-00001-1", "type": "book-chapter", "title": ["Herbaria"],
                    "container-title": ["Plant Collections"], "issued": {"date-parts": [[2019]]}}}


class TestCrossref(TestClass):
    def setup_method(self):
        super().setup_method()
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        self.curator_id = curator.user_id
        self.curator = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        researcher = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
        self.researcher = {"Authorization": "Bearer " + signJWT(researcher.user_id, "classic_user")["access_token"]}

    def lookup(self, doi):
        return client.get("/api/publication/doi-lookup", params={"doi": doi}, headers=self.curator)

    def test_lookup_proposes_cleaned_fields_with_attribution(self, monkeypatch):
        calls = []

        def fake(url, params=None, headers=None):
            calls.append((url, params))
            return {"10.3390/plants13010001": WORK, "10.1007/978-3-030-00001-1": BOOK}.get(url.rsplit("works/", 1)[1])
        monkeypatch.setattr(HTTP, fake)
        monkeypatch.setattr(settings, "EXTERNAL_CONTACT_EMAIL", "herbarium@example.edu")
        assert client.get("/api/publication/doi-lookup", params={"doi": DOI}).status_code == 403
        assert client.get("/api/publication/doi-lookup", params={"doi": DOI}, headers=self.researcher).status_code == 403

        found = self.lookup("https://doi.org/10.3390/PLANTS13010001")
        assert found.status_code == 200, found.text
        found = found.json()
        assert found["fields"] == {"doi": DOI, "title": "Essential Oil of Achillea millefolium L. from Serbia",
                                   "journal": "Plants", "year": "2024",
                                   "abstract": "Hydrodistilled oil was analysed by GC–MS."}
        assert found["authors"][0] == {"given": "Ana", "family": "Petrović",
                                       "orcid": "https://orcid.org/0000-0002-1825-0097"}
        assert found["existing_pub_id"] is None and found["publisher"] == "MDPI AG"
        assert found["warnings"] == ["The abstract is the publisher's text; check that you may store and show it."]
        assert found["source"]["provider"] == "crossref" and found["source"]["url"] == f"https://doi.org/{DOI}"
        assert "CC0" in found["source"]["license"] and found["source"]["cached"] is False
        assert calls == [(f"https://api.crossref.org/works/{DOI}", {"mailto": "herbarium@example.edu"})]

        assert self.lookup(f"doi:{DOI}").json()["source"]["cached"] is True
        assert len(calls) == 1

        book = self.lookup("10.1007/978-3-030-00001-1").json()
        assert any("book chapter" in warning for warning in book["warnings"])
        assert any("no abstract" in warning for warning in book["warnings"])

        missing = self.lookup("10.9999/nothing-here")
        assert missing.status_code == 404 and "no record" in missing.json()["detail"]
        assert "DataCite" in missing.json()["detail"]
        assert self.lookup("not-a-doi").status_code == 422

    def test_saving_a_reviewed_lookup_logs_its_source(self, monkeypatch):
        monkeypatch.setattr(HTTP, lambda url, params=None, headers=None: WORK)
        proposal = self.lookup(DOI).json()
        with TestingSessionLocal() as db:
            assert db.query(ExternalImport).count() == 0  # looking up writes nothing

        body = {**proposal["fields"], "title": "Essential oil of Achillea millefolium from Serbia",
                "source": {"provider": "crossref", "external_id": DOI, "retrieved_at": proposal["source"]["retrieved_at"]}}
        saved = client.post("/api/publication/create-new-publication", headers=self.curator, json=body)
        assert saved.status_code == 200, saved.text
        with TestingSessionLocal() as db:
            entry = db.query(ExternalImport).one()
            assert (entry.provider, entry.external_id, entry.record_type) == ("crossref", DOI, "publication")
            assert entry.record_id == saved.json()["pub_id"] and entry.confirmed_by == self.curator_id
            assert entry.fields == {"accepted": ["doi", "journal", "year", "abstract"], "edited": ["title"]}

        again = self.lookup(DOI.upper()).json()
        assert again["existing_pub_id"] == saved.json()["pub_id"]
        duplicate = client.post("/api/publication/create-new-publication", headers=self.curator,
                                json={**body, "doi": f"https://doi.org/{DOI.upper()}"})
        assert duplicate.status_code == 400

        typed = client.post("/api/publication/create-new-publication", headers=self.curator, json={
            "doi": "10.1000/typed", "year": "2020", "journal": "J", "title": "Typed by hand", "abstract": "Text"})
        assert typed.status_code == 200
        with TestingSessionLocal() as db:
            assert db.query(ExternalImport).count() == 1  # a hand-typed entry has no external source

    def test_crossref_down_or_switched_off(self, monkeypatch):
        def offline(*_args, **_kwargs):
            raise requests.ConnectionError("no route")
        monkeypatch.setattr(HTTP, offline)
        down = self.lookup(DOI)
        assert down.status_code == 502 and down.json()["provider"] == "crossref"
        monkeypatch.setattr(settings, "EXTERNAL_LOOKUPS", "gbif")
        off = self.lookup(DOI)
        assert off.status_code == 503 and "turned off" in off.json()["detail"]

    def test_a_failed_save_leaves_nothing_behind(self, monkeypatch):
        monkeypatch.setattr(HTTP, lambda url, params=None, headers=None: WORK)
        proposal = self.lookup(DOI).json()
        body = {**proposal["fields"], "source": {"provider": "crossref", "external_id": "not-a-doi"}}
        create = "/api/publication/create-new-publication"

        def nothing_saved():
            with TestingSessionLocal() as db:
                return db.query(Publication).count() == 0 and db.query(ExternalImport).count() == 0

        invalid = client.post(create, headers=self.curator, json=body)
        assert invalid.status_code == 400 and nothing_saved()
        other = client.post(create, headers=self.curator,
                            json={**body, "source": {"provider": "crossref", "external_id": "10.1000/other"}})
        assert other.status_code == 400 and "different DOI" in other.json()["detail"] and nothing_saved()

        def broken(*_args, **_kwargs):
            raise RuntimeError("provenance could not be written")
        monkeypatch.setattr("app.publication.services.publication_services.record_import", broken)
        failed = client.post(create, headers=self.curator, json={**body, "source": {"provider": "crossref", "external_id": DOI}})
        assert failed.status_code == 500 and nothing_saved()

        monkeypatch.undo()
        monkeypatch.setattr(HTTP, lambda url, params=None, headers=None: WORK)
        retry = client.post(create, headers=self.curator, json={**body, "source": {"provider": "crossref", "external_id": DOI}})
        assert retry.status_code == 200, retry.text  # the retry is not blocked by a half-saved entry

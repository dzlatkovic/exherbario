"""Matching names as written to the GBIF Backbone, with recorded GBIF v2 answers."""

from requests import RequestException

from app.external.models import ExternalImport
from app.tests import TestClass, TestingSessionLocal, client
from app.tests.test_taxon_lookup import TREE
from app.users.services import UserServices, signJWT

SERVICE = "app.taxonomy.services.taxonomy_services.species"
PORELLA = [{"key": "6", "name": "Plantae", "rank": "KINGDOM"},
           {"key": "102", "name": "Porellaceae", "rank": "FAMILY"},
           {"key": "2688728", "name": "Porella", "rank": "GENUS"}]
MATCHES = {
    "Porella platyphylla": {
        "usage": {"key": "2688800", "name": "Porella platyphylla (L.) Pfeiff.", "canonicalName": "Porella platyphylla",
                  "authorship": "(L.) Pfeiff.", "rank": "SPECIES", "status": "ACCEPTED"},
        "classification": PORELLA, "synonym": False,
        "diagnostics": {"matchType": "EXACT", "confidence": 99},
    },
    "Porella platiphylla": {
        "usage": {"key": "2688800", "name": "Porella platyphylla (L.) Pfeiff.", "rank": "SPECIES", "status": "ACCEPTED"},
        "classification": PORELLA, "synonym": False,
        "diagnostics": {"matchType": "FUZZY", "confidence": 88},
    },
    "Porella rivularis": {
        "usage": {"key": "999", "name": "Porella rivularis Nees", "rank": "SPECIES", "status": "SYNONYM"},
        "acceptedUsage": {"key": "2688800", "name": "Porella platyphylla (L.) Pfeiff.", "rank": "SPECIES"},
        "classification": PORELLA, "synonym": True,
        "diagnostics": {"matchType": "EXACT", "confidence": 98},
    },
    "Porella": {
        "classification": [], "synonym": False,
        "diagnostics": {"matchType": "NONE", "confidence": 100, "note": "Multiple equal matches for Porella",
                        "alternatives": [
                            {"usage": {"key": "1004711", "name": "Porella Gray, 1848", "rank": "GENUS", "status": "ACCEPTED"},
                             "classification": [{"rank": "KINGDOM", "name": "Animalia"}],
                             "diagnostics": {"matchType": "EXACT", "confidence": 98}},
                            {"usage": {"key": "2688728", "name": "Porella L.", "rank": "GENUS", "status": "ACCEPTED"},
                             "classification": PORELLA[:2], "diagnostics": {"matchType": "EXACT", "confidence": 98}},
                        ]},
    },
    "Xyzzy plugh": {"synonym": False, "diagnostics": {"matchType": "NONE", "confidence": 100}},
}


def usage(key, **_):
    return {"key": int(key), **TREE[str(key)]}


class TestGBIFMatch(TestClass):
    def setup_method(self):
        super().setup_method()
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        self.curator_id = curator.user_id
        self.curator = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        researcher = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
        self.researcher = {"Authorization": "Bearer " + signJWT(researcher.user_id, "classic_user")["access_token"]}

    def match(self, name, **params):
        return client.get("/api/taxonomy/gbif-match", params={"name": name, **params}, headers=self.curator)

    def test_exact_fuzzy_synonym_and_no_match(self, monkeypatch):
        calls = []

        def backbone(scientificName, kingdom=None, verbose=None, timeout=None):
            calls.append((scientificName, kingdom, verbose, timeout))
            return MATCHES[scientificName]
        monkeypatch.setattr(f"{SERVICE}.name_backbone", backbone)
        assert client.get("/api/taxonomy/gbif-match", params={"name": "Porella"}).status_code == 403
        assert client.get("/api/taxonomy/gbif-match", params={"name": "Porella"}, headers=self.researcher).status_code == 403

        exact = self.match("  Porella   platyphylla ", kingdom="Plantae").json()
        assert exact["query"] == "Porella platyphylla" and exact["match_type"] == "exact" and exact["review"] == []
        assert exact["match"]["gbif_key"] == "2688800" and exact["match"]["family"] == "Porellaceae"
        assert exact["match"]["importable"] and exact["match"]["taxon_id"] is None
        assert exact["source"]["provider"] == "gbif" and exact["source"]["license"] == "CC BY 4.0"
        assert exact["source"]["url"] == "https://www.gbif.org/species/2688800" and exact["source"]["cached"] is False
        assert calls[0][1:3] == ("Plantae", True) and calls[0][3][0] == 5

        fuzzy = self.match("Porella platiphylla").json()
        assert fuzzy["match_type"] == "fuzzy"
        assert any("differently spelled" in note for note in fuzzy["review"])
        assert any("88%" in note for note in fuzzy["review"])

        synonym = self.match("Porella rivularis").json()
        assert synonym["synonym"] and synonym["accepted"]["gbif_key"] == "2688800"
        assert any("accepted name Porella platyphylla" in note for note in synonym["review"])

        ambiguous = self.match("Porella").json()
        assert ambiguous["match"] is None and "Multiple equal matches" in " ".join(ambiguous["review"])
        assert [item["gbif_key"] for item in ambiguous["alternatives"]] == ["2688728"]  # the bryozoan is left out

        none = self.match("Xyzzy plugh").json()
        assert none["match"] is None and none["review"] == ["GBIF found no match. Check the spelling or search for the genus."]

        assert self.match("Porella platyphylla", kingdom="Plantae").json()["source"]["cached"] is True
        assert len(calls) == 5
        assert self.match("Porella", kingdom="Animalia").status_code == 422

    def test_import_after_review_is_logged_and_marks_the_match(self, monkeypatch):
        monkeypatch.setattr(f"{SERVICE}.name_backbone", lambda scientificName, **_: MATCHES[scientificName])
        monkeypatch.setattr(f"{SERVICE}.name_usage", usage)
        proposal = self.match("Porella rivularis").json()
        with TestingSessionLocal() as db:
            assert db.query(ExternalImport).count() == 0  # matching writes nothing

        imported = client.post("/api/taxonomy/import-from-gbif", headers=self.curator, params={
            "gbif_key": proposal["match"]["gbif_key"], "matched_name": proposal["query"]}).json()
        assert imported["name"] == "Porella platyphylla (L.) Pfeiff." and "synonym" in imported["note"]
        with TestingSessionLocal() as db:
            entry = db.query(ExternalImport).one()
            assert (entry.provider, entry.external_id, entry.record_type) == ("gbif", "2688800", "taxon")
            assert entry.record_id == imported["taxon_id"] and entry.confirmed_by == self.curator_id
            assert entry.fields["matched_name"] == "Porella rivularis"
            assert entry.fields["requested_synonym"]["gbif_key"] == "999"
            assert {item["name"] for item in entry.fields["added"]} >= {"Plantae", "Porella L."}
            assert entry.retrieved_at is not None

        client.post("/api/taxonomy/import-from-gbif", headers=self.curator, params={"gbif_key": "2688800"})
        with TestingSessionLocal() as db:
            assert db.query(ExternalImport).count() == 1  # nothing new was added, so nothing new is logged
        again = self.match("Porella rivularis").json()
        assert again["accepted"]["taxon_id"] == imported["taxon_id"]

    def test_gbif_down_or_switched_off(self, monkeypatch):
        def offline(**_):
            raise RequestException("no route")
        monkeypatch.setattr(f"{SERVICE}.name_backbone", offline)
        down = self.match("Porella platyphylla")
        assert down.status_code == 502 and "can't be matched" in down.json()["detail"]

        from app.config import settings
        monkeypatch.setattr(settings, "EXTERNAL_LOOKUPS", "crossref")
        off = self.match("Porella platyphylla")
        assert off.status_code == 503 and "turned off" in off.json()["detail"]
        assert client.get("/api/taxonomy/gbif-search", params={"q": "Porella"}, headers=self.curator).status_code == 503

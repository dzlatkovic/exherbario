"""Literature-reported natural products for a taxon (LOTUS via Wikidata), with recorded SPARQL answers."""

from datetime import datetime, timedelta

import requests

from app.chemistry.models import Compound
from app.config import settings
from app.external.models import ExternalImport, ExternalLookupCache
from app.tests import TestClass, TestingSessionLocal, client
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices, signJWT

HTTP = "app.chemistry.lotus.http_get"
SERVICE = "app.taxonomy.services.taxonomy_services.species"
TREE = {
    "6": {"scientificName": "Plantae", "rank": "KINGDOM"},
    "7707728": {"scientificName": "Tracheophyta", "rank": "PHYLUM", "parentKey": 6},
    "220": {"scientificName": "Magnoliopsida", "rank": "CLASS", "parentKey": 7707728},
    "414": {"scientificName": "Asterales", "rank": "ORDER", "parentKey": 220},
    "3065": {"scientificName": "Asteraceae", "rank": "FAMILY", "parentKey": 414},
    "3117424": {"scientificName": "Achillea L.", "rank": "GENUS", "parentKey": 3065},
    "3120060": {"scientificName": "Achillea millefolium L.", "rank": "SPECIES", "parentKey": 3117424},
}


def uri(qid):
    return {"type": "uri", "value": f"http://www.wikidata.org/entity/{qid}"}


def literal(value):
    return {"type": "literal", "value": value}


MAIN = {"head": {"vars": []}, "results": {"bindings": [
    {"compound": uri("Q407334"), "compoundLabel": literal("eucalyptol"), "inchikey": literal("WEEGYLXZBRQIMU-UHFFFAOYSA-N"),
     "cid": literal("2758"), "reference": uri("Q90001"), "taxonName": literal("Achillea millefolium")},
    {"compound": uri("Q407334"), "compoundLabel": literal("eucalyptol"), "inchikey": literal("WEEGYLXZBRQIMU-UHFFFAOYSA-N"),
     "cid": literal("2758"), "reference": uri("Q90002"), "taxonName": literal("Achillea millefolium")},
    {"compound": uri("Q27104536"), "compoundLabel": literal("Q27104536"), "inchikey": literal("GUAFOGOEJLSQBT-UHFFFAOYSA-N"),
     "reference": uri("Q90003"), "taxonName": literal("Achillea millefolium")},
]}}
SCHOLARLY = {"head": {"vars": []}, "results": {"bindings": [
    {"reference": uri("Q90001"), "doi": literal("10.1016/J.PHYTOCHEM.2005.01.001"), "title": literal("Volatiles of yarrow"),
     "date": literal("2005-03-01T00:00:00Z")},
    {"reference": uri("Q90002"), "title": literal("Essential oil of Achillea"), "date": literal("1998-01-01T00:00:00Z")},
]}}


def wikidata(url, params=None, headers=None):
    assert params["format"] == "json" and headers["Accept"] == "application/sparql-results+json"
    if url == "https://query.wikidata.org/sparql":
        return MAIN if 'wdt:P846 "3120060"' in params["query"] else {"results": {"bindings": []}}
    assert url == "https://query-scholarly.wikidata.org/sparql"
    assert "wd:Q90001" in params["query"]
    return SCHOLARLY


def usage(key, **_):
    return {"key": int(key), **TREE[str(key)]}


class TestLOTUS(TestClass):
    def setup_method(self):
        super().setup_method()
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        self.curator_id = curator.user_id
        self.curator = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        researcher = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
        self.researcher = {"Authorization": "Bearer " + signJWT(researcher.user_id, "classic_user")["access_token"]}

    def taxon(self, monkeypatch, key="3120060"):
        monkeypatch.setattr(f"{SERVICE}.name_usage", usage)
        imported = client.post("/api/taxonomy/import-from-gbif", params={"gbif_key": key}, headers=self.curator)
        assert imported.status_code == 200, imported.text
        return imported.json()["taxon_id"]

    def test_lookup_review_and_publish(self, monkeypatch):
        taxon_id = self.taxon(monkeypatch)
        calls = []
        monkeypatch.setattr(HTTP, lambda url, params=None, headers=None: calls.append(url) or wikidata(url, params, headers))
        lookup_url = f"/api/chemistry/lotus/taxa/{taxon_id}"
        assert client.get(lookup_url).status_code == 403
        assert client.get(lookup_url, headers=self.researcher).status_code == 403
        with TestingSessionLocal() as db:
            db.add(Compound(cid=2758, title="Eucalyptol", inchikey="WEEGYLXZBRQIMU-UHFFFAOYSA-N", synonyms=[],
                            cas_numbers=[], retrieved_at=datetime(2026, 1, 1)))
            db.commit()

        found = client.get(lookup_url, headers=self.curator)
        assert found.status_code == 200, found.text
        found = found.json()
        assert found["taxon"]["gbif_key"] == "3120060" and found["wikidata_taxon_name"] == "Achillea millefolium"
        first, second = found["compounds"]
        assert (first["wikidata_id"], first["name"], first["cid"], first["in_registry"]) == ("Q407334", "eucalyptol", 2758, True)
        assert first["references"][0] == {"wikidata_id": "Q90001", "doi": "10.1016/j.phytochem.2005.01.001",
                                          "title": "Volatiles of yarrow", "year": "2005"}
        assert first["references"][1]["doi"] is None and first["references"][1]["year"] == "1998"
        assert second["name"] == "GUAFOGOEJLSQBT-UHFFFAOYSA-N"  # no label: the InChIKey, not the bare item ID
        assert second["references"] == [{"wikidata_id": "Q90003", "doi": None, "title": None, "year": None}]
        assert found["source"]["provider"] == "lotus" and "eLife.70780" in found["source"]["citation"]
        assert found["published_at"] is None
        assert calls == ["https://query.wikidata.org/sparql", "https://query-scholarly.wikidata.org/sparql"]
        client.get(lookup_url, headers=self.curator)
        assert len(calls) == 2  # cached

        public_url = f"/api/chemistry/public/taxa/{taxon_id}/literature-compounds"
        assert client.get(public_url).status_code == 404  # nothing public before a curator publishes
        with TestingSessionLocal() as db:
            assert db.query(ExternalImport).filter_by(provider="lotus").count() == 0

        publish = f"{lookup_url}/published"
        reviewed = found["review_id"]
        assert client.put(publish, headers=self.curator, json={"wikidata_ids": ["Q407334"]}).status_code == 422
        assert client.put(publish, headers=self.curator, json={"review_id": reviewed, "wikidata_ids": ["Q1"]}).status_code == 422
        assert client.put(publish, headers=self.researcher, json={"review_id": reviewed}).status_code == 403
        done = client.put(publish, headers=self.curator, json={"review_id": reviewed, "wikidata_ids": ["Q407334"]})
        assert done.status_code == 200 and done.json()["published"] == 1
        public = client.get(public_url).json()
        assert [item["name"] for item in public["compounds"]] == ["eucalyptol"]
        assert public["compounds"][0]["in_registry"] and "Rutz" in public["source"]["citation"]
        with TestingSessionLocal() as db:
            entry = db.query(ExternalImport).filter_by(provider="lotus").one()
            assert (entry.record_type, entry.record_id, entry.confirmed_by) == ("taxon_literature", taxon_id, self.curator_id)
            assert entry.fields == {"compounds": 1, "of": 2}

        assert client.put(publish, headers=self.curator, json={"review_id": reviewed}).json()["published"] == 2  # all, replacing
        assert len(client.get(public_url).json()["compounds"]) == 2
        assert client.get(lookup_url, headers=self.curator).json()["published_at"]

        voucher = client.post("/api/specimen/create-new-specimen", headers=self.curator,
                              json={"holding_type": "local", "taxon_id": taxon_id}).json()["specimen_id"]
        client.put(f"/api/specimen/{voucher}/visibility", headers=self.curator, json={"is_public": True, "public_location": "withheld"})
        page = client.get(f"/specimens/{voucher}").text
        assert "Reported in the literature for this taxon" in page and "not measured on this voucher" in page
        assert 'href="/compounds/2758"' in page and "https://doi.org/10.1016/j.phytochem.2005.01.001" in page
        staff = signed_in("curator@example.org").get(f"/researcher/specimens/{voucher}").text
        assert 'id="lotus"' in staff and "/js/lotus.js" in staff

        assert client.delete(publish, headers=self.curator).status_code == 204
        assert client.get(public_url).status_code == 404
        assert "Reported in the literature" not in client.get(f"/specimens/{voucher}").text

    def test_publishing_needs_a_reviewed_lookup(self, monkeypatch):
        taxon_id = self.taxon(monkeypatch)
        refused = client.put(f"/api/chemistry/lotus/taxa/{taxon_id}/published", headers=self.curator,
                             json={"review_id": "0" * 32})
        assert refused.status_code == 409 and "Look up" in refused.json()["detail"]
        assert client.get("/api/chemistry/lotus/taxa/missing", headers=self.curator).status_code == 404

    def test_no_compounds_wikidata_down_or_switched_off(self, monkeypatch):
        taxon_id = self.taxon(monkeypatch, "3117424")
        monkeypatch.setattr(HTTP, wikidata)
        empty = client.get(f"/api/chemistry/lotus/taxa/{taxon_id}", headers=self.curator).json()
        assert empty["compounds"] == []

        genus_species = self.taxon(monkeypatch)

        def offline(*_args, **_kwargs):
            raise requests.ConnectionError("no route")
        monkeypatch.setattr(HTTP, offline)
        down = client.get(f"/api/chemistry/lotus/taxa/{genus_species}", headers=self.curator)
        assert down.status_code == 502 and down.json()["provider"] == "lotus"
        monkeypatch.setattr(settings, "EXTERNAL_LOOKUPS", "gbif")
        off = client.get(f"/api/chemistry/lotus/taxa/{genus_species}", headers=self.curator)
        assert off.status_code == 503

    def test_publishing_refuses_a_list_that_changed_after_review(self, monkeypatch):
        taxon_id = self.taxon(monkeypatch)
        monkeypatch.setattr(HTTP, wikidata)
        lookup_url = f"/api/chemistry/lotus/taxa/{taxon_id}"
        first = client.get(lookup_url, headers=self.curator).json()
        assert [item["wikidata_id"] for item in first["compounds"]] == ["Q407334", "Q27104536"]

        # The shared cache is refreshed (here: expired and looked up again) and Wikidata now answers differently.
        changed = {"results": {"bindings": [{**MAIN["results"]["bindings"][2], "compound": uri("Q2")}]}}
        monkeypatch.setattr(HTTP, lambda url, params=None, headers=None: changed if "query.wikidata" in url else SCHOLARLY)
        with TestingSessionLocal() as db:
            row = db.query(ExternalLookupCache).filter_by(provider="lotus").one()
            row.fetched_at -= timedelta(days=31)
            db.commit()
        second = client.get(lookup_url, headers=self.curator).json()
        assert [item["wikidata_id"] for item in second["compounds"]] == ["Q2"]
        assert second["review_id"] != first["review_id"]

        stale = client.put(f"{lookup_url}/published", headers=self.curator, json={"review_id": first["review_id"]})
        assert stale.status_code == 409 and "changed since you reviewed" in stale.json()["detail"]
        assert client.get(f"/api/chemistry/public/taxa/{taxon_id}/literature-compounds").status_code == 404
        fresh = client.put(f"{lookup_url}/published", headers=self.curator, json={"review_id": second["review_id"]})
        assert fresh.status_code == 200 and fresh.json()["published"] == 1

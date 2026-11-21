"""GBIF taxon lookup for voucher registration and redetermination."""

from requests import RequestException

from app.tests import TestClass, client
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices, signJWT

SERVICE = "app.taxonomy.services.taxonomy_services.species"
TREE = {
    "6": {"scientificName": "Plantae", "rank": "KINGDOM"},
    "9": {"scientificName": "Marchantiophyta", "rank": "PHYLUM", "parentKey": 6},
    "100": {"scientificName": "Jungermanniopsida", "rank": "CLASS", "parentKey": 9},
    "101": {"scientificName": "Porellales", "rank": "ORDER", "parentKey": 100},
    "102": {"scientificName": "Porellaceae", "rank": "FAMILY", "parentKey": 101},
    "2688728": {"scientificName": "Porella L.", "rank": "GENUS", "parentKey": 102, "authorship": "L."},
    "2688800": {"scientificName": "Porella platyphylla (L.) Pfeiff.", "rank": "SPECIES", "parentKey": 2688728},
    "999": {"scientificName": "Porella rivularis Nees", "rank": "SPECIES", "parentKey": 2688728, "synonym": True,
            "acceptedKey": 2688800, "accepted": "Porella platyphylla (L.) Pfeiff."},
}
SUGGEST = [
    {"key": 1004711, "scientificName": "Porella Gray, 1848", "canonicalName": "Porella", "rank": "GENUS",
     "status": "ACCEPTED", "kingdom": "Animalia", "phylum": "Bryozoa"},
    {"key": 11087141, "scientificName": "Porella Nees", "canonicalName": "Porella", "rank": "GENUS",
     "status": "DOUBTFUL", "kingdom": "Plantae", "phylum": "Marchantiophyta", "family": "Porellaceae"},
    {"key": 2688728, "scientificName": "Porella L.", "canonicalName": "Porella", "rank": "GENUS",
     "status": "ACCEPTED", "kingdom": "Plantae", "phylum": "Marchantiophyta", "family": "Porellaceae"},
    {"key": 5, "scientificName": "Porella sect. X", "rank": "SECTION", "status": "ACCEPTED", "kingdom": "Plantae"},
]


def usage(key, **_):
    return {"key": int(key), **TREE[str(key)]}


def headers(user):
    return {"Authorization": "Bearer " + signJWT(user.user_id, "super_user" if user.is_superuser else "classic_user")["access_token"]}


class TestTaxonLookup(TestClass):
    def test_search_and_import(self, monkeypatch):
        monkeypatch.setattr(f"{SERVICE}.name_usage", usage)
        monkeypatch.setattr(f"{SERVICE}.name_suggest", lambda **_: SUGGEST)
        curator = headers(UserServices.create_super_user("Curator", "Example", "curator@example.org", "password"))
        researcher = headers(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        for method, path in (("get", "/api/taxonomy/gbif-search?q=Porella"), ("post", "/api/taxonomy/import-from-gbif?gbif_key=2688728")):
            assert getattr(client, method)(path).status_code == 403
            assert getattr(client, method)(path, headers=researcher).status_code == 403

        found = client.get("/api/taxonomy/gbif-search", params={"q": "Porella"}, headers=curator).json()
        assert [(item["gbif_key"], item["status"]) for item in found] == [("2688728", "accepted"), ("11087141", "doubtful")]
        assert found[0]["family"] == "Porellaceae" and found[0]["taxon_id"] is None  # animal and unsupported rank left out

        species = client.post("/api/taxonomy/import-from-gbif", params={"gbif_key": "2688800"}, headers=curator).json()
        assert species["name"] == "Porella platyphylla (L.) Pfeiff." and species["rank"] == "species" and species["note"] is None
        lineage = client.get("/api/taxonomy", params={"query": "Porella"}).json()["items"]
        assert {item["name"] for item in lineage} >= {"Porella L.", "Porellaceae", "Porella platyphylla (L.) Pfeiff."}
        again = client.post("/api/taxonomy/import-from-gbif", params={"gbif_key": "2688800"}, headers=curator).json()
        assert again["taxon_id"] == species["taxon_id"]
        assert client.get("/api/taxonomy/gbif-search", params={"q": "Porella"}, headers=curator).json()[0]["taxon_id"]

        synonym = client.post("/api/taxonomy/import-from-gbif", params={"gbif_key": "999"}, headers=curator).json()
        assert synonym["taxon_id"] == species["taxon_id"] and "synonym" in synonym["note"]
        assert client.post("/api/taxonomy/import-from-gbif", params={"gbif_key": "abc"}, headers=curator).status_code == 422

        voucher = client.post("/api/specimen/create-new-specimen", headers=curator, json={
            "holding_type": "local", "accession": "P-1", "taxon_id": species["taxon_id"], "subnomen": "Porella platyphylla"})
        assert voucher.status_code == 200, voucher.text
        assert voucher.json()["taxon_id"] == species["taxon_id"]
        staff = signed_in("curator@example.org").get(f"/researcher/specimens/{voucher.json()['specimen_id']}").text
        assert 'id="redetermine-taxon"' in staff and "Porella platyphylla" in staff

        def offline(**_):
            raise RequestException("no route")
        monkeypatch.setattr(f"{SERVICE}.name_suggest", offline)
        down = client.get("/api/taxonomy/gbif-search", params={"q": "Porella"}, headers=curator)
        assert down.status_code == 502 and "still listed" in down.json()["detail"]

    def test_forms_carry_the_lookup(self):
        UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        admin = signed_in("curator@example.org")
        assert 'id="register-taxon"' in admin.get("/curation/vouchers").text

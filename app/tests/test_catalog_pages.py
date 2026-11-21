"""Public catalog pages: home, search results and specimen records."""

from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, headers_for, release_voucher, sample_payload
from app.db import SessionLocal
from app.specimen.models import Specimen
from app.specimen.repository import SpecimenRepository
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.taxonomy.models import Taxonomy
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices


def make_vouchers(count, released=()):
    template = SpecimenFixtures.create_test_specimen_object()
    with TestingSessionLocal() as db:
        taxon = db.get(Taxonomy, template.taxon_id)
        taxon.common_name = "Red maple"
        db.commit()
        repository = SpecimenRepository(db)
        ids = [repository.create_specimen(template.model_copy(update={
            "reg_no": f"R-{index:03d}", "accession": f"BEOU-{index:03d}", "holding_institution": "BEOU",
            "collection": "Vascular plants", "subnomen": "Acer rubrum L." if index % 2 == 0 else "Achillea atrata",
        })).specimen_id for index in range(count)]
    with SessionLocal() as db:
        for index, specimen_id in enumerate(ids):
            if index in released:
                specimen = db.get(Specimen, specimen_id)
                specimen.is_public, specimen.public_location = True, "region"
        db.commit()
    return ids


class TestCatalogPages(TestClass):
    def test_home_and_empty_catalog(self):
        home = client.get("/")
        assert home.status_code == 200 and "Find a voucher specimen" in home.text
        assert "No specimens have been released yet." in home.text
        empty = client.get("/specimens")
        assert "No specimens have been released yet." in empty.text and "Download CSV" not in empty.text

    def test_search_filters_and_privacy(self):
        ids = make_vouchers(25, released=set(range(0, 25)) - {1, 3})
        home = client.get("/")
        assert "23 released specimens" in home.text
        page = client.get("/specimens", params={"q": "red maple"})
        assert page.status_code == 200 and "23 specimens · page 1 of 2" in page.text
        assert f"/specimens/{ids[0]}" in page.text and f"/specimens/{ids[1]}" not in page.text
        assert "BEOU-001" not in page.text and "Nis, Serbia" in page.text
        assert 'href="/specimens?q=red+maple&amp;page=2" rel="next"' in page.text
        second = client.get("/specimens?q=red+maple&page=2")
        assert "page 2 of 2" in second.text and 'rel="prev"' in second.text
        assert 'href="/api/specimen/export?q=red+maple"' in page.text
        assert "BEOU-001" not in client.get("/api/specimen/export?q=red+maple").text
        filtered = client.get("/specimens", params={"q": "atrata", "collection": "Vascular plants"})
        assert "10 specimens" in filtered.text and "Clear filters" in filtered.text and " open>" in filtered.text
        none = client.get("/specimens", params={"q": "Quercus"})
        assert "No matches for these filters." in none.text and 'href="/specimens"' in none.text
        assert "Enter dates as YYYY-MM-DD." in client.get("/specimens", params={"start_date": "20-01-2010"}).text
        backwards = client.get("/specimens", params={"start_date": "2011-01-01", "end_date": "2010-01-01"})
        assert "start date must come before" in backwards.text

    def test_specimen_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ids = make_vouchers(2, released={0})
        record = client.get(f"/specimens/{ids[0]}")
        assert record.status_code == 200
        for text in ("Acer rubrum", "Red maple", "BEOU-000", "Vascular plants", "2010-01-01", "Nis, Serbia",
                     f"/specimens/{ids[0]}", "https://www.gbif.org/species/2871551"):
            assert text in record.text, text
        for absent in ("Photographs", "Determination history", "Literature", "Analytical profiles", "John Smith"):
            assert absent not in record.text, absent
        private = client.get(f"/specimens/{ids[1]}")
        unknown = client.get("/specimens/no-such-record")
        assert private.status_code == unknown.status_code == 404
        assert private.text.replace(ids[1], "") == unknown.text.replace("no-such-record", "")

        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        curator = headers_for(UserServices.create_super_user("Curator", "Example", "curator@example.org", "password"))
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "Maple oils"}).json()["id"]
        sample = client.post(f"{BASE}/studies/{study}/samples", headers=owner,
                             json=sample_payload([(ids[0], "sampled_from_voucher")])).json()["id"]
        preparation = client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json={
            "batch_code": "B", "kind": "extract", "method_reference": "Methanol"}).json()["id"]
        profile = client.post(f"{BASE}/preparations/{preparation}/profiles", headers=owner,
                              data={"run_code": "R-1", "analytical_method": "LC", "unit": "mg/g",
                                    "measurement_basis": "concentration", "technique": "HPLC-DAD"},
                              files={"file": ("p.csv", b"feature,value,confidence\nA,1.5,annotated\n", "text/csv")})
        assert profile.status_code == 201, profile.text
        assert "Analytical profiles" not in client.get(f"/specimens/{ids[0]}").text
        for url in (f"{BASE}/studies/{study}/visibility", f"{BASE}/profiles/{profile.json()['id']}/visibility"):
            assert client.put(url, headers=curator, json={"is_public": True}).status_code == 200
        release_voucher(curator, ids[0])
        with_chemistry = client.get(f"/specimens/{ids[0]}").text
        assert "Analytical profiles" in with_chemistry and "Maple oils" in with_chemistry and "HPLC-DAD" in with_chemistry
        assert f"/api/chemistry/public/export?study_id={study}&amp;format=long" in with_chemistry

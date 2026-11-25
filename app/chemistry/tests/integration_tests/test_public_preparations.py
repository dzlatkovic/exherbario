"""Public pages list preparations released by deposition without runs, and nothing that was not released."""

from app.chemistry.tests.integration_tests import test_sample_vouchers
from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, sample_payload, vouchers
from app.chemistry.models import Profile
from app.config import settings
from app.tests import TestClass, TestingSessionLocal, client

EXTRACT = {"batch_code": "MeOH-1", "kind": "extract", "method_reference": "Maceration in methanol, 3 × 24 h",
           "plant_material_mass_g": 50, "yield_percent": 12.5}
UNDEPOSITED = {"batch_code": "Hexane-9", "kind": "extract", "method_reference": "Soxhlet extraction with hexane"}
PRIVATE_NOTE = "Private note: freezer 3, shelf B"
SECTION = "Samples and preparations without analytical profiles"


class TestPublicPreparations(TestClass):
    setup_people = test_sample_vouchers.TestSampleVouchers.setup_people
    add_profile = test_sample_vouchers.TestSampleVouchers.add_profile
    create_study = test_sample_vouchers.TestSampleVouchers.create_study

    def publish(self, owner, curator, title, preparation_ids):
        created = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": title, "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}], "preparation_ids": preparation_ids})
        assert created.status_code == 201, created.text
        path = f"/api/depositions/{created.json()['id']}"
        preview = client.get(f"{path}/draft/preview", headers=curator).json()
        approval = {key: preview[key] for key in ("draft_revision", "snapshot_sha256", "releases_sha256")}
        assert client.post(f"{path}/publish", headers=curator, json=approval).status_code == 200
        return path

    def test_released_preparations_appear_once_and_private_records_stay_hidden(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        (voucher,), _ = vouchers(1)
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        study_url = self.create_study(owner)
        study_id = study_url.rsplit("/", 1)[-1]
        sample = client.post(f"{study_url}/samples", headers=owner, json=sample_payload(
            [(voucher, "sampled_from_voucher")], code="BIO-1", collection_notes=PRIVATE_NOTE)).json()["id"]
        extract = client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json=EXTRACT).json()["id"]
        client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json=UNDEPOSITED)
        profile = self.add_profile(owner, curator, sample)  # essential oil B-1 with a released run
        with TestingSessionLocal() as db:
            with_run = db.get(Profile, profile).preparation_id

        # Nothing is public before publication.
        assert client.get(f"/studies/{study_id}").status_code == 404
        assert client.get(f"/specimens/{voucher}").status_code == 404

        path = self.publish(owner, curator, "Extracts of the population", [extract, with_run])

        page = client.get(f"/specimens/{voucher}")
        assert page.status_code == 200
        assert SECTION in page.text and "MeOH-1" in page.text and "Maceration in methanol" in page.text
        assert "12.5% (w/w) from 50 g" in page.text and "No analytical profile" in page.text
        assert "Extracts of the population" in page.text and "/depositions/EXU/" in page.text
        assert "Hexane-9" not in page.text and "Soxhlet" not in page.text  # never deposited
        assert PRIVATE_NOTE not in page.text
        assert "Analytical profiles" in page.text
        # The essential oil is listed through its run, not again among preparations without profiles.
        assert "Essential oil B-1" not in page.text
        assert "deposited in" in page.text  # the oil links to the deposition instead

        study_page = client.get(f"/studies/{study_id}")
        assert study_page.status_code == 200
        assert SECTION in study_page.text and "MeOH-1" in study_page.text
        assert "Hexane-9" not in study_page.text and PRIVATE_NOTE not in study_page.text
        assert "Essential oil B-1" not in study_page.text

        listing = client.get("/studies")
        assert listing.status_code == 200 and f'href="/studies/{study_id}"' in listing.text
        assert "1 analytical profile" in listing.text and "1 preparation without profiles" in listing.text

        # A withdrawn version no longer lists its preparations.
        assert client.post(f"{path}/versions/1/withdraw", headers=curator,
                           json={"reason": "Wrong extraction protocol recorded."}).status_code == 200
        assert "MeOH-1" not in client.get(f"/specimens/{voucher}").text

    def test_study_with_only_preparations_has_a_public_page(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        (voucher,), _ = vouchers(1)
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        study_url = self.create_study(owner)
        study_id = study_url.rsplit("/", 1)[-1]
        sample = client.post(f"{study_url}/samples", headers=owner,
                             json=sample_payload([(voucher, "sampled_from_voucher")], code="BIO-2")).json()["id"]
        extract = client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json=EXTRACT).json()["id"]
        self.publish(owner, curator, "Extract only", [extract])
        page = client.get(f"/studies/{study_id}")
        assert page.status_code == 200
        assert "0 released profiles" in page.text and "1 preparation without profiles" in page.text
        assert "Long CSV" not in page.text  # nothing to export
        assert f'href="/specimens/{voucher}"' in page.text
        # A released study with nothing released in it stays unavailable.
        empty = client.post(f"{BASE}/studies", headers=owner, json={"title": "Empty"}).json()["id"]
        assert client.put(f"{BASE}/studies/{empty}/visibility", headers=curator, json={"is_public": True}).status_code == 200
        assert client.get(f"/studies/{empty}").status_code == 404
        assert f'href="/studies/{empty}"' not in client.get("/studies").text

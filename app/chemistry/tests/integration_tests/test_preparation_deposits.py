import json
from io import BytesIO
from zipfile import ZipFile

from app.chemistry.tests.integration_tests import test_sample_vouchers
from app.chemistry.tests.integration_tests.test_sample_vouchers import (BASE, headers_for, release_voucher,
                                                                        sample_payload, vouchers)
from app.config import settings
from app.deposition.verify_archive import verify_archive
from app.tests import TestClass, client
from app.users.services import UserServices

EXTRACT = {"batch_code": "MeOH-1", "kind": "extract", "method_reference": "Maceration in methanol, 3 × 24 h",
           "plant_material_mass_g": 50, "method_parameters": "Evaporated under reduced pressure at 40 °C"}


class TestPreparationDeposits(TestClass):
    setup_people = test_sample_vouchers.TestSampleVouchers.setup_people
    add_profile = test_sample_vouchers.TestSampleVouchers.add_profile
    create_study = test_sample_vouchers.TestSampleVouchers.create_study

    def test_preparation_without_runs_is_deposited_with_its_sample_and_vouchers(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        other = headers_for(UserServices.create_user("Other", "Lab", "other@example.org", "password"))
        (voucher,), _ = vouchers(1)
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        study_url = self.create_study(owner)
        study_id = study_url.rsplit("/", 1)[-1]
        sample = client.post(f"{study_url}/samples", headers=owner,
                             json=sample_payload([(voucher, "sampled_from_voucher")], code="BIO-1")).json()["id"]
        preparation = client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json=EXTRACT).json()["id"]
        described = client.get(f"{BASE}/preparations/{preparation}", headers=owner).json()
        assert (described["sample_code"], described["batch_code"], described["study"]["id"]) == ("BIO-1", "MeOH-1", study_id)
        assert client.get(f"{BASE}/preparations/{preparation}", headers=other).status_code == 404

        assert client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "x", "preparation_ids": ["missing"]}).status_code == 409
        created = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Antimicrobial extract", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}], "preparation_ids": [preparation]})
        assert created.status_code == 201, created.text
        path = f"/api/depositions/{created.json()['id']}"
        inputs = client.get(f"{path}/draft/inputs", headers=owner).json()
        entry = inputs["preparations"][0]
        assert (entry["preparation"]["sample_code"], entry["study"]["is_public"], entry["vouchers"][0]["is_public"]) == (
            "BIO-1", False, False)
        assert inputs["unavailable"] == 0
        deleting = client.delete(f"{BASE}/preparations/{preparation}", headers=owner)
        assert deleting.status_code == 409 and "Antimicrobial extract" in deleting.json()["detail"]

        # Nothing is released yet: the preview lists what publishing will release.
        preview = client.get(f"{path}/draft/preview", headers=curator)
        assert preview.status_code == 200, preview.text
        releases = preview.json()["releases"]
        assert ([item["id"] for item in releases["studies"]], [item["id"] for item in releases["vouchers"]],
                releases["runs"]) == ([study_id], [voucher], [])
        snapshot = preview.json()["snapshot"]
        assert snapshot["schema_version"] == 6 and snapshot["profiles"] == []
        deposited = snapshot["preparations"][0]
        assert (deposited["id"], deposited["batch_code"], deposited["kind"], deposited["plant_material_mass_g"],
                deposited["study"]["id"]) == (preparation, "MeOH-1", "extract", 50, study_id)
        assert deposited["sample"]["code"] == "BIO-1"
        assert [(link["id"], link["role"]) for link in deposited["sample"]["vouchers"]] == [(voucher, "sampled_from_voucher")]
        assert [item["id"] for item in snapshot["vouchers"]] == [voucher]

        approval = {key: preview.json()[key] for key in ("draft_revision", "snapshot_sha256")}
        assert client.post(f"{path}/publish", headers=owner, json=approval).status_code == 403
        assert client.post(f"{path}/publish", headers=curator, json=approval).status_code == 200
        assert client.get(f"{study_url}", headers=owner).json()["is_public"] is True
        assert client.get(f"/api/specimen/{voucher}").status_code == 200  # released with the version
        # The editor opens a published deposition with what a correction would start from.
        published = client.get(f"{path}/draft", headers=owner).json()
        assert (published["draft"], published["published"]["version"]) == (None, 1)
        assert published["published"]["page"] == snapshot["identifier"].removeprefix("https://herbar.example.edu")
        start = published["published"]["correction_start"]
        assert (start["title"], start["license"], start["preparation_ids"], start["profile_ids"], start["specimen_ids"]) == (
            "Antimicrobial extract", "CC BY 4.0", [preparation], [], [])
        assert start["contributors"] == [{"name": "F. Scientist", "role": "analyst"}]
        page = client.get(snapshot["identifier"].removeprefix("https://herbar.example.edu"))
        assert page.status_code == 200
        assert "Samples and preparations without analytical runs" in page.text and "MeOH-1" in page.text
        assert "Maceration in methanol" in page.text and "Sampled from the voucher" in page.text
        archive = client.get(snapshot["url"].removeprefix("https://herbar.example.edu") + "/archive.zip")
        with ZipFile(BytesIO(archive.content)) as bundle:
            manifest = json.loads(bundle.read("manifest.json"))
        assert [entry["path"] for entry in manifest["entries"]] == ["deposition.json"]
        (tmp_path / "version.zip").write_bytes(archive.content)
        digest = preview.json()["snapshot_sha256"]
        assert verify_archive(tmp_path / "version.zip", digest)["snapshot_sha256"] == digest
        # Released with its study, so it is retained.
        assert client.delete(f"{BASE}/preparations/{preparation}", headers=owner).status_code == 409

    def test_a_preparation_is_not_deposited_twice(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        (voucher,), _ = vouchers(1)
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        study_url = self.create_study(owner, curator)
        sample = client.post(f"{study_url}/samples", headers=owner,
                             json=sample_payload([(voucher, "sampled_from_voucher")])).json()["id"]
        profile = self.add_profile(owner, curator, sample)
        release_voucher(curator, voucher)
        preparation = client.get(f"{BASE}/profiles/{profile}", headers=owner).json()["preparation_id"]
        created = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Oil", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}],
            "profile_ids": [profile], "preparation_ids": [preparation]}).json()
        preview = client.get(f"/api/depositions/{created['id']}/draft/preview", headers=curator)
        assert preview.status_code == 409 and "already included through its runs" in preview.json()["detail"]

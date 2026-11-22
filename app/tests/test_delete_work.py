from app.chemistry.models import LabSample, Measurement, Preparation, Profile, Study
from app.chemistry.tests.integration_tests.test_sample_vouchers import headers_for
from app.config import settings
from app.deposition.models import Deposition, DepositionVersion, Institution
from app.specimen.models import Specimen
from app.tests import TestClass, TestingSessionLocal, client
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices


class TestDeleteWork(TestClass):
    def setup_method(self):
        super().setup_method()
        owner = UserServices.create_user("Lab", "Owner", "owner@example.org", "password")
        curator = UserServices.create_super_user("Lab", "Curator", "curator@example.org", "password")
        self.owner = headers_for(owner)
        self.curator = headers_for(curator)
        with TestingSessionLocal() as db:
            db.add(Institution(code="TEST", name="Test Herbarium"))
            study = Study(owner_id=owner.user_id, title="Test study", description="")
            voucher = Specimen(holding_type="local")
            db.add_all([study, voucher])
            db.flush()
            sample = LabSample(study_id=study.id, code="S1", plant_part="leaf")
            db.add(sample)
            db.flush()
            preparation = Preparation(sample_id=sample.id, batch_code="P1", kind="extract", method_reference="")
            db.add(preparation)
            db.flush()
            run = Profile(preparation_id=preparation.id, run_code="R1", analytical_method="GC-MS",
                          measurement_basis="peak_area", unit="AU", source_name="result.csv", source_csv="A,1")
            db.add(run)
            db.flush()
            db.add(Measurement(profile_id=run.id, feature="A", value=1, status="measured", confidence="tentative"))
            db.commit()
            self.study, self.run, self.voucher = study.id, run.id, voucher.specimen_id

    def draft(self, **fields):
        response = client.post("/api/depositions", headers=self.owner, json={"institution": "TEST", **fields})
        assert response.status_code == 201, response.text
        return response.json()

    def test_draft_blocks_deleting_study_and_discard_preserves_inputs(self):
        draft = self.draft(title="My draft", profile_ids=[self.run], specimen_ids=[self.voucher])
        study_url = f"/api/chemistry/studies/{self.study}"
        counts = {"samples": 1, "preparations": 1, "runs": 1, "imports": 0}
        assert "Delete study" in signed_in("owner@example.org").get(f"/researcher/studies/{self.study}").text
        blocked = client.delete(study_url, headers=self.owner, params=counts)
        assert blocked.status_code == 409 and "My draft" in blocked.json()["detail"]
        voucher_url = "/api/specimen/delete-specimen"
        assert client.delete(voucher_url, headers=self.curator, params={"specimen_id": self.voucher}).status_code == 409
        path = f"/api/depositions/{draft['id']}"
        params = {"expected_revision": draft["draft_revision"]}
        assert client.post(f"{path}/submission", headers=self.owner).status_code == 200
        assert client.delete(f"{path}/draft", headers=self.owner, params=params).status_code == 409
        assert client.delete(f"{path}/submission", headers=self.owner).status_code == 200
        assert client.delete(f"{path}/draft", headers=self.owner, params=params).status_code == 204
        with TestingSessionLocal() as db:
            assert db.get(Deposition, draft["id"]) is None and db.get(Profile, self.run)
        assert client.delete(study_url, headers=self.owner, params={**counts, "runs": 0}).status_code == 409
        assert client.delete(study_url, headers=self.owner, params=counts).status_code == 204
        with TestingSessionLocal() as db:
            assert db.get(Profile, self.run) is None and db.query(Measurement).count() == 0
            assert db.get(Specimen, self.voucher)

    def test_withdrawn_records_remain_protected(self):
        run_url = f"/api/chemistry/profiles/{self.run}"
        voucher_url = f"/api/specimen/{self.voucher}/visibility"
        for released in (True, False):
            assert client.put(f"{run_url}/visibility", headers=self.curator,
                              json={"is_public": released}).status_code == 200
            assert client.put(voucher_url, headers=self.curator, json={
                "is_public": released, "public_location": "withheld"}).status_code == 200
        assert client.delete(run_url, headers=self.owner).status_code == 409
        assert client.delete("/api/specimen/delete-specimen", headers=self.curator,
                             params={"specimen_id": self.voucher}).status_code == 409

    def test_discard_import_removes_only_its_upload(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        response = client.post(f"/api/chemistry/studies/{self.study}/imports", headers=self.owner,
                               files={"file": ("demo.csv", b"Name,Value\nExample,1\n", "text/csv")})
        assert response.status_code == 201, response.text
        import_id = response.json()["id"]
        assert len(list(tmp_path.glob("files/*"))) == 1
        url = f"/api/chemistry/imports/{import_id}"
        outsider = UserServices.create_user("Other", "Lab", "other@example.org", "password")
        assert client.delete(url, headers=headers_for(outsider)).status_code == 404
        assert client.delete(url, headers=self.owner).status_code == 204
        assert not list(tmp_path.glob("files/*"))
        with TestingSessionLocal() as db:
            assert db.get(Profile, self.run)

    def test_discard_correction_preserves_the_published_snapshot(self, monkeypatch):
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://example.org")
        assert client.put(f"/api/specimen/{self.voucher}/visibility", headers=self.curator,
                          json={"is_public": True, "public_location": "withheld"}).status_code == 200
        fields = {"title": "Voucher dataset", "license": "CC-BY-4.0", "specimen_ids": [self.voucher],
                  "contributors": [{"name": "Lab Owner", "role": "Researcher"}]}
        item = self.draft(**fields)
        path = f"/api/depositions/{item['id']}"
        preview = client.get(f"{path}/draft/preview", headers=self.curator).json()
        approval = {key: preview[key] for key in ("draft_revision", "snapshot_sha256")}
        assert client.post(f"{path}/publish", headers=self.curator, json=approval).status_code == 200
        correction = client.put(f"{path}/draft", headers=self.owner,
                                json={**fields, "correction_reason": "Typo", "expected_revision": None}).json()
        assert client.delete(f"{path}/draft", headers=self.owner,
                             params={"expected_revision": item["draft_revision"]}).status_code == 409
        assert client.delete(f"{path}/draft", headers=self.owner,
                             params={"expected_revision": correction["draft_revision"]}).status_code == 204
        with TestingSessionLocal() as db:
            deposition = db.get(Deposition, item["id"])
            assert deposition.latest_version == 1 and deposition.draft is None
            assert db.get(DepositionVersion, (item["id"], 1)).snapshot_sha256 == approval["snapshot_sha256"]

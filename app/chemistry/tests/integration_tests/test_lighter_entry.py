from app.chemistry.tests.integration_tests import test_sample_vouchers
from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, release_voucher, sample_payload, vouchers
from app.config import settings
from app.tests import TestClass, client

OIL = {"kind": "essential_oil", "method_reference": "Hydrodistillation, Clevenger, 3 h"}


class TestLighterEntry(TestClass):
    setup_people = test_sample_vouchers.TestSampleVouchers.setup_people
    create_study = test_sample_vouchers.TestSampleVouchers.create_study

    def test_batch_codes_material_state_and_oil_yield(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        (voucher,), _ = vouchers(1)
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        study_url = self.create_study(owner)
        payload = sample_payload([(voucher, "sampled_from_voucher")], code="S1")
        payload.pop("material_state", None)
        created = client.post(f"{study_url}/sample-preparations", headers=owner, json={"sample": payload, "preparation": OIL})
        assert created.status_code == 201, created.text  # no material state, no batch code, no yield yet
        sample = created.json()["sample"]["id"]
        first = created.json()["preparation"]
        assert first["batch_code"] == "P1" and first["yield_percent"] is None
        second = client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json=OIL).json()["id"]
        assert client.get(f"{BASE}/preparations/{second}", headers=owner).json()["batch_code"] == "P2"

        draft = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Oil yields", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}], "preparation_ids": [first["id"]]}).json()
        preview = client.get(f"/api/depositions/{draft['id']}/draft/preview", headers=curator)
        assert preview.status_code == 409 and "yield" in preview.json()["detail"] and "P1 of sample S1" in preview.json()["detail"]

        edited = client.put(f"{BASE}/preparations/{first['id']}", headers=owner,
                            json={**OIL, "batch_code": None, "yield_percent": 0.42, "plant_material_mass_g": 100})
        assert edited.status_code == 200, edited.text
        assert (edited.json()["batch_code"], edited.json()["yield_percent"]) == ("P1", 0.42)
        assert client.put(f"{BASE}/preparations/{first['id']}", headers=owner,
                          json={**OIL, "batch_code": "P2"}).status_code == 409  # taken by the other preparation

        preview = client.get(f"/api/depositions/{draft['id']}/draft/preview", headers=curator)
        assert preview.status_code == 200, preview.text
        approval = {key: preview.json()[key] for key in ("draft_revision", "snapshot_sha256", "releases_sha256")}
        assert client.post(f"/api/depositions/{draft['id']}/publish", headers=curator, json=approval).status_code == 200
        frozen = client.put(f"{BASE}/preparations/{first['id']}", headers=owner, json={**OIL, "yield_percent": 0.5})
        assert frozen.status_code == 409 and "published deposition" in frozen.json()["detail"]

    def test_withdrawn_records_are_not_released_again_silently(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        (voucher,), _ = vouchers(1)
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        release_voucher(curator, voucher)
        release_voucher(curator, voucher, released=False)
        draft = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Vouchers", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "curator"}], "specimen_ids": [voucher]}).json()
        preview = client.get(f"/api/depositions/{draft['id']}/draft/preview", headers=curator)
        assert preview.status_code == 409 and "withdrawn" in preview.json()["detail"]
        release_voucher(curator, voucher)
        assert client.get(f"/api/depositions/{draft['id']}/draft/preview", headers=curator).status_code == 200


class TestImportTemplate(TestClass):
    def test_template_and_prompt(self):
        from io import BytesIO

        from openpyxl import load_workbook

        from app.chemistry.tests.integration_tests.test_sample_vouchers import headers_for
        from app.tests.test_record_pages import signed_in
        from app.users.services import UserServices

        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        assert client.get(f"{BASE}/import-template.xlsx").status_code == 403
        response = client.get(f"{BASE}/import-template.xlsx", headers=owner)
        assert response.status_code == 200
        book = load_workbook(BytesIO(response.content))
        assert book.sheetnames == ["GC-MS profile", "Isolated compounds", "Details", "Read me"]
        assert [cell.value for cell in book["GC-MS profile"][1]][:3] == ["No.", "Compound", "RT"]
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "Papers"}).json()["id"]
        page = signed_in("lab@example.org").get(f"/researcher/studies/{study}").text
        assert 'id="ai-prompt"' in page and "Copy values exactly as printed" in page
        assert "/api/chemistry/import-template.xlsx" in page

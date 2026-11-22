import json

from app.chemistry.models import Compound, CompoundAlias, Measurement, MeasurementCorrection
from app.chemistry.tests.integration_tests.test_sample_vouchers import (BASE, headers_for, release_voucher,
                                                                         sample_payload, vouchers)
from app.config import settings
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices

GC_RUN = json.dumps({"column": "HP-5MS, 30 m × 0.25 mm × 0.25 µm", "polarity_class": "non-polar",
                     "carrier_gas": "He", "ri_type": "linear_temperature_programmed"})
CSV = ("feature,value,confidence,cid,cas,rt_min,ri_exp,ri_ref,ri_ref_source,id_basis,id_level,qualifier\n"
       "α-Pinene,60,annotated,6654,80-56-8,7.82,932,932,Adams 2007,RI;MS,2,\n"
       "Limonene,39.5,annotated,,138-86-3,10.1,1029,1060,Adams 2007,RI;MS,2,\n"
       "Unidentified sesquiterpene,0.5,tentative,,,25.03,1498,,,MS,3,\n"
       "β-Elemene,,annotated,,,22.91,1390,1389,Adams 2007,RI;MS,2,trace\n").encode()


class TestCompounds(TestClass):
    def setup_profile(self, csv=CSV, technique="GC-MS", run=GC_RUN, expected=201):
        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        curator = headers_for(UserServices.create_super_user("Curator", "Example", "curator@example.org", "password"))
        (voucher,), _ = vouchers(1)
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "Oils"}).json()["id"]
        sample = client.post(f"{BASE}/studies/{study}/samples", headers=owner,
                             json=sample_payload([(voucher, "sampled_from_voucher")])).json()["id"]
        assert client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json={
            "batch_code": "B", "kind": "essential_oil", "method_reference": "Hydrodistillation", "yield_percent": -1}).status_code == 422
        preparation = client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json={
            "batch_code": "B", "kind": "essential_oil", "method_reference": "Hydrodistillation",
            "plant_material_mass_g": 100, "method_parameters": "Clevenger, 3 h", "yield_percent": 0.42})
        assert preparation.status_code == 201, preparation.text
        upload = client.post(f"{BASE}/preparations/{preparation.json()['id']}/profiles", headers=owner,
                             data={"run_code": "R-1", "analytical_method": "GC-MS 1", "unit": "%",
                                   "measurement_basis": "peak_area_percent", "technique": technique,
                                   "run_metadata": run},
                             files={"file": ("results.csv", csv, "text/csv")})
        assert upload.status_code == expected, upload.text
        return owner, curator, voucher, study, upload

    def test_upload_records_technique_evidence_and_compounds(self, pubchem):
        owner, _, _, _, upload = self.setup_profile()
        profile = upload.json()
        assert profile["technique"] == "GC-MS" and profile["run_metadata"]["polarity_class"] == "non-polar"
        assert profile["warnings"] == ["Row 3: experimental RI 1029 differs from the reference 1060 by more than 20."]
        detail = client.get(f"{BASE}/profiles/{profile['id']}", headers=owner).json()
        rows = {row["feature"]: row for row in detail["measurements"]}
        assert (rows["α-Pinene"]["cid"], rows["α-Pinene"]["compound_match"]) == (6654, "cid")
        assert rows["α-Pinene"]["compound"]["inchikey"] == "GRWFGVWFFZKLTI-UHFFFAOYSA-N"
        assert rows["α-Pinene"]["compound"]["cas_numbers"] == ["80-56-8"]
        assert (rows["Limonene"]["cid"], rows["Limonene"]["compound_match"]) == (22311, "cas")
        assert rows["Unidentified sesquiterpene"]["cid"] is None and "compound" not in rows["Unidentified sesquiterpene"]
        assert rows["β-Elemene"]["value"] is None and rows["β-Elemene"]["qualifier"] == "trace"
        assert rows["α-Pinene"]["ri_exp"] == 932 and rows["α-Pinene"]["id_basis"] == "RI;MS"
        study_id = client.get(f"{BASE}/studies", headers=owner).json()["studies"][0]["id"]
        assert client.get(f"{BASE}/studies/{study_id}", headers=owner).json()["preparations"][0]["yield_percent"] == 0.42
        with TestingSessionLocal() as db:
            assert sorted(db.query(Compound.cid)) == [(6654,), (22311,)]
        assert client.get(f"{BASE}/public/compounds/6654").json()["title"] == "alpha-Pinene"
        assert client.get(f"{BASE}/public/compounds/82227").status_code == 404

    def test_run_metadata_and_technique_columns_are_checked(self):
        self.setup_profile(run=json.dumps({"column": "DB-5"}), expected=422)

    def test_lc_columns_are_rejected_for_gc(self):
        self.setup_profile(csv=b"feature,value,confidence,mz_obs\nA,100,annotated,205.2\n", expected=422)

    LC_CSV = b"feature,value,confidence,mz_obs,adduct\nChlorogenic acid,100,annotated,355.1024,[M+H]+\n"

    def test_lc_profile_rejects_gc_run_metadata(self):
        self.setup_profile(csv=self.LC_CSV, technique="LC-MS", run=GC_RUN, expected=422)

    def test_lc_profile_takes_lc_run_metadata(self):
        _, _, _, _, upload = self.setup_profile(csv=self.LC_CSV, technique="LC-MS",
                                                run=json.dumps({"ionisation_mode": "ESI+"}))
        assert upload.json()["run_metadata"] == {"ionisation_mode": "ESI+"}

    def test_conflicting_identifiers_are_rejected(self):
        self.setup_profile(csv=b"feature,value,confidence,cid,cas\nA,100,annotated,6654,138-86-3\n", expected=422)

    def test_registry_search_and_parent(self, pubchem):
        owner, _, _, _, _ = self.setup_profile()
        search = f"{BASE}/compounds/search"
        assert client.get(search, params={"q": "alpha-pinene"}).status_code == 403
        found = client.get(search, headers=owner, params={"q": "ALPHA–pinene"}).json()
        assert [item["cid"] for item in found] == [6654]
        assert found[0]["structure_image"].endswith("/cid/6654/PNG")
        assert client.get(search, headers=owner, params={"q": "7785-70-8", "namespace": "cas"}).json()[0]["cid"] == 82227
        assert client.get(search, headers=owner, params={"q": "80-56-7", "namespace": "cas"}).status_code == 422
        assert client.get(search, headers=owner, params={"q": "GRWFGVWFFZKLTI-RKDXNWHRSA-N",
                                                         "namespace": "inchikey"}).json()[0]["cid"] == 440968
        assert client.get(f"{BASE}/compounds/82227/parent", headers=owner).json()["cid"] == 6654
        assert client.get(f"{BASE}/compounds/6654/parent", headers=owner).json()["cid"] == 6654
        with TestingSessionLocal() as db:
            assert db.get(Compound, 82227) is None  # candidates are not stored until chosen
        pubchem.available = False
        assert client.get(search, headers=owner, params={"q": "limonene"}).status_code == 503
        assert client.get(search, headers=owner, params={"q": "6654", "namespace": "cid"}).json()[0]["cid"] == 6654

    def test_corrections_are_logged_and_published(self, tmp_path, monkeypatch, pubchem):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator, voucher, study, upload = self.setup_profile()
        profile_id = upload.json()["id"]
        other = headers_for(UserServices.create_user("Other", "User", "other@example.org", "password"))
        url = f"{BASE}/profiles/{profile_id}/measurements/α-Pinene/compound"
        assert client.put(url, headers=other, json={"cid": 82227, "reason": "Chiral column"}).status_code == 404
        assert client.put(url, headers=owner, json={"cid": 82227, "reason": " "}).status_code == 422
        assert client.put(url, headers=owner, json={"cid": 6654, "reason": "Same"}).status_code == 409
        corrected = client.put(url, headers=owner, json={"cid": 82227, "reason": "Chiral column confirms (+)"})
        assert corrected.status_code == 200, corrected.text
        assert corrected.json() | {"corrected_at": None} == {
            "feature": "α-Pinene", "old_cid": 6654, "new_cid": 82227, "reason": "Chiral column confirms (+)",
            "corrected_at": None}
        unidentified = f"{BASE}/profiles/{profile_id}/measurements/Limonene/compound"
        assert client.put(unidentified, headers=curator, json={"cid": None, "reason": "Co-elutes"}).status_code == 200
        source = client.get(f"{BASE}/profiles/{profile_id}/source", headers=owner)
        assert source.content == CSV
        with TestingSessionLocal() as db:
            row = db.get(Measurement, (profile_id, "α-Pinene"))
            assert (row.cid, row.value, row.compound_match) == (82227, 60, "correction")
            assert db.get(Measurement, (profile_id, "Limonene")).compound_match == "unidentified"
            assert db.query(MeasurementCorrection).count() == 2
            assert db.query(CompoundAlias).count() == 0

        assert client.put(f"{BASE}/studies/{study}/visibility", headers=curator, json={"is_public": True}).status_code == 200
        assert client.put(f"{BASE}/profiles/{profile_id}/visibility", headers=curator, json={"is_public": True}).status_code == 200
        release_voucher(curator, voucher)
        public = client.get(f"{BASE}/public/profiles/{profile_id}").json()
        assert [item["new_cid"] for item in public["compound_corrections"]] == [82227, None]
        assert public["yield_percent"] == 0.42 and public["technique"] == "GC-MS"

        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        created = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Oil", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}], "profile_ids": [profile_id]}).json()
        snapshot = client.get(f"/api/depositions/{created['id']}/draft/preview", headers=curator).json()["snapshot"]
        assert snapshot["schema_version"] == 6
        frozen = snapshot["profiles"][0]
        assert frozen["technique"] == "GC-MS" and frozen["preparation"]["yield_percent"] == 0.42
        rows = {row["feature"]: row for row in frozen["measurements"]}
        assert rows["α-Pinene"]["compound"]["title"] == "(+)-alpha-Pinene" and rows["β-Elemene"]["qualifier"] == "trace"
        assert [item["reason"] for item in frozen["compound_corrections"]] == ["Chiral column confirms (+)", "Co-elutes"]

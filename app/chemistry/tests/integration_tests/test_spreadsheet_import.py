from io import BytesIO

from openpyxl import Workbook

from app.chemistry.models import CompoundAlias, Measurement, Profile
from app.chemistry.services.profile_import import read_measurements
from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, headers_for, sample_payload, vouchers
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices

ROWS = [
    ["Table 2. Chemical composition (%) of the essential oils"],
    [],
    ["No.", "Compound", "RI exp", "RI lit", "S1", "S1 SD", "S2", "Identification"],
    [1, "α-Pinene", 932, 932, "12,4", 0.3, 10.1, "RI, MS"],
    [2, "Limonene", 1029, 1060, "3.1a", None, "tr", "RI;MS"],
    [3, "Pinene", 933, None, 1.2, None, 0.8, "MS"],
    [4, "Unknown sesquiterpene", 1498, None, 0.4, None, "–", "MS"],
    [None, "Monoterpene hydrocarbons", None, None, 16.7, None, 10.9, None],
    [None, "Total identified", None, None, 17.1, None, 10.9, None],
]
SETTINGS = {"technique": "GC-MS", "measurement_basis": "peak_area_percent", "unit": "%",
            "analytical_method": "GC-MS, HP-5MS", "run_metadata": {"polarity_class": "non-polar", "column": "HP-5MS"},
            "ri_ref_polarity": "non-polar"}


def workbook(rows=ROWS):
    book = Workbook()
    book.active.title = "Table 2"
    for row in rows:
        book.active.append(row)
    output = BytesIO()
    book.save(output)
    return output.getvalue()


def columns(second_preparation=None, **extra):
    return [{"index": 1, "role": "name"}, {"index": 2, "role": "ri_exp"}, {"index": 3, "role": "ri_ref"},
            {"index": 4, "role": "sample"}, {"index": 5, "role": "sd", "sd_for": 4},
            {"index": 6, "role": "sample", "preparation_id": second_preparation, **extra},
            {"index": 7, "role": "id_basis"}, {"index": 0, "role": "ignore"}]


class TestSpreadsheetImport(TestClass):
    def setup_study(self):
        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        (voucher,), _ = vouchers(1)
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "Oils"}).json()["id"]
        preparations = []
        for code in ("S1", "Population B"):
            sample = client.post(f"{BASE}/studies/{study}/samples", headers=owner,
                                 json=sample_payload([(voucher, "same_population")], code=code)).json()["id"]
            preparations.append(client.post(f"{BASE}/samples/{sample}/preparations", headers=owner, json={
                "batch_code": "HD-1", "kind": "essential_oil", "method_reference": "Hydrodistillation",
                "yield_percent": 0.6}).json()["id"])
        return owner, study, preparations

    def upload(self, owner, study, content=None, name="table2.xlsx"):
        upload = client.post(f"{BASE}/studies/{study}/imports", headers=owner,
                             files={"file": (name, content or workbook(), "application/octet-stream")})
        assert upload.status_code == 201, upload.text
        return upload.json()

    def test_upload_before_creating_the_sample_and_preparation(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        (voucher,), _ = vouchers(1)
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "New study"}).json()["id"]
        draft = self.upload(owner, study, workbook([["Compound", "S1"], ["Unknown peak", 5]]))
        import_url = f"{BASE}/imports/{draft['id']}"
        assignment = {"sheet": "Table 2", "header_row": 1, "settings": SETTINGS,
                      "columns": [{"index": 0, "role": "name"}, {"index": 1, "role": "sample"}]}
        preview = client.put(f"{import_url}/assignment", headers=owner, json=assignment).json()["preview"]
        assert any("choose the lab sample preparation" in error for error in preview["errors"])

        create_url = f"{BASE}/studies/{study}/sample-preparations"
        sample = sample_payload([(voucher, "sampled_from_voucher")], code="S1")
        preparation = {"batch_code": "B1", "kind": "essential_oil", "method_reference": "Test method"}
        assert client.post(create_url, headers=owner, json={"sample": sample, "preparation": preparation}).status_code == 422
        assert client.get(f"{BASE}/studies/{study}", headers=owner).json()["samples"] == []
        response = client.post(create_url, headers=owner,
                               json={"sample": sample, "preparation": {**preparation, "yield_percent": 1}})
        assert response.status_code == 201, response.text
        result = response.json()
        assert result["sample"]["code"] == "S1"
        assert result["preparation"]["sample_id"] == result["sample"]["id"]

        assignment["columns"][1]["preparation_id"] = result["preparation"]["id"]
        preview = client.put(f"{import_url}/assignment", headers=owner, json=assignment).json()["preview"]
        assert preview["errors"] == []
        assert client.put(f"{import_url}/rows/2/compound", headers=owner,
                          json={"action": "unidentified"}).status_code == 200
        confirmed = client.post(f"{import_url}/confirm", headers=owner)
        assert confirmed.status_code == 201, confirmed.text
        assert confirmed.json()["profiles"][0]["preparation_id"] == result["preparation"]["id"]

        second = client.post(create_url, headers=owner, json={"sample_id": result["sample"]["id"],
                             "preparation": {"batch_code": "B2", "kind": "extract", "method_reference": "Test extract"}})
        assert second.status_code == 201 and second.json()["sample"] == result["sample"]

    def test_full_import(self, pubchem, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, study, (first, second) = self.setup_study()
        created = self.upload(owner, study)
        assert created["sheets"][0]["name"] == "Table 2" and created["sheets"][0]["rows"][2][1] == "Compound"
        imports = f"{BASE}/imports/{created['id']}"
        outsider = headers_for(UserServices.create_user("Other", "User", "other@example.org", "password"))
        assert client.get(imports, headers=outsider).status_code == 404

        assignment = {"sheet": "Table 2", "header_row": 3, "columns": columns(), "settings": SETTINGS,
                      "save_template": "GC table"}
        preview = client.put(f"{imports}/assignment", headers=owner, json=assignment).json()["preview"]
        assert any("S2" in error and "preparation" in error for error in preview["errors"])
        assert preview["profiles"][0]["preparation_id"] == first  # matched by the sample code in the header
        assignment["columns"] = columns(second)
        response = client.put(f"{imports}/assignment", headers=owner, json=assignment)
        assert response.status_code == 200, response.text
        preview = response.json()["preview"]
        assert preview["errors"] == []
        assert [(profile["header"], profile["total"], profile["detected"]) for profile in preview["profiles"]] == [
            ("S1", 17.1, 4), ("S2", 10.9, 3)]
        warnings = " ".join(preview["warnings"])
        assert "E5" in warnings and "Summary rows were left out: 8, 9" in warnings and "1060" in warnings
        assert [row["status"] for row in response.json()["review"]] == ["pending"] * 4
        assert client.post(f"{imports}/confirm", headers=owner).status_code == 409

        pubchem.available = False
        stalled = client.post(f"{imports}/match", headers=owner).json()
        assert stalled["pending"] == 4 and "PubChem" in stalled["problem"]
        pubchem.available = True
        assert client.post(f"{imports}/match", headers=owner, params={"limit": 26}).status_code == 422
        assert client.post(f"{imports}/match", headers=owner, params={"limit": 1}).json()["pending"] == 3
        matched = client.post(f"{imports}/match", headers=owner).json()
        assert matched["pending"] == 0
        review = {row["name"]: row for row in matched["review"]}
        assert (review["α-Pinene"]["status"], review["α-Pinene"]["match"]["cid"]) == ("needs_review", 6654)
        assert review["Limonene"]["match"]["cid"] == 22311 and review["Pinene"]["match"]["cid"] == 6654
        assert review["Unknown sesquiterpene"]["status"] == "unmatched"

        rows = f"{imports}/rows"
        assert client.put(f"{rows}/7/compound", headers=owner, json={"action": "accept"}).status_code == 409
        for number in (4, 5):
            assert client.put(f"{rows}/{number}/compound", headers=owner, json={"action": "accept"}).status_code == 200
        chosen = client.put(f"{rows}/6/compound", headers=owner, json={"action": "choose", "cid": 82227})
        assert chosen.json()["match"]["cid"] == 82227
        parent = client.put(f"{rows}/6/compound", headers=owner, json={"action": "parent"}).json()
        assert (parent["status"], parent["method"], parent["match"]["cid"]) == ("confirmed", "parent", 6654)
        assert client.put(f"{rows}/7/compound", headers=owner, json={"action": "unidentified"}).status_code == 200
        assert client.put(f"{rows}/99/compound", headers=owner, json={"action": "unidentified"}).status_code == 404

        confirmed = client.post(f"{imports}/confirm", headers=owner)
        assert confirmed.status_code == 201, confirmed.text
        profiles = confirmed.json()["profiles"]
        assert [(item["run_code"], item["import_column"], item["technique"]) for item in profiles] == [
            ("S1", "S1", "GC-MS"), ("S2", "S2", "GC-MS")]
        assert client.put(f"{imports}/assignment", headers=owner, json=assignment).status_code == 409
        with TestingSessionLocal() as db:
            s1 = {row.feature: row for row in db.query(Measurement).filter_by(profile_id=profiles[0]["id"])}
            s2 = {row.feature: row for row in db.query(Measurement).filter_by(profile_id=profiles[1]["id"])}
            aliases = {alias.name: alias.cid for alias in db.query(CompoundAlias)}
            assert db.get(Profile, profiles[0]["id"]).import_id == created["id"]
        assert set(s1) == {"α-Pinene", "Limonene", "Pinene", "Unknown sesquiterpene"}
        pinene = s1["α-Pinene"]
        assert (pinene.value, pinene.sd, pinene.cid, pinene.ri_exp, pinene.ri_ref_polarity, pinene.id_basis) == (
            12.4, 0.3, 6654, 932, "non-polar", "RI;MS")
        assert (s1["Limonene"].value, s2["Limonene"].value, s2["Limonene"].qualifier) == (3.1, None, "trace")
        assert (s2["Unknown sesquiterpene"].status, s2["Unknown sesquiterpene"].cid) == ("not_detected", None)
        assert s1["Unknown sesquiterpene"].compound_match == "unidentified"
        assert aliases == {"α-Pinene": 6654, "Limonene": 22311, "Pinene": 6654}

        source = client.get(f"{BASE}/profiles/{profiles[1]['id']}/source", headers=owner)
        _, reparsed, _ = read_measurements(source.content, "peak_area_percent", "GC-MS", SETTINGS["run_metadata"])
        assert {row["feature"]: (row["value"], row.get("qualifier"), row["status"]) for row in reparsed} == {
            name: (row.value, row.qualifier, row.status) for name, row in s2.items()}

        # The same layout again: the saved template assigns the columns and the aliases confirm the names.
        again = self.upload(owner, study)
        templates = client.get(f"{BASE}/import-templates", headers=owner).json()
        assert [template["name"] for template in templates] == ["GC table"]
        proposed = client.get(f"{BASE}/imports/{again['id']}/templates/{templates[0]['id']}", headers=owner).json()
        assert proposed["missing_headers"] == []
        roles = {column["index"]: column["role"] for column in proposed["columns"]}
        assert roles == {0: "ignore", 1: "name", 2: "ri_exp", 3: "ri_ref", 4: "sample", 5: "sd", 6: "sample", 7: "id_basis"}
        calls = len(pubchem.calls)
        proposed["columns"] = [column if column["index"] != 6 else {**column, "preparation_id": second}
                               for column in proposed["columns"]]
        del proposed["missing_headers"]
        replay = client.put(f"{BASE}/imports/{again['id']}/assignment", headers=owner, json=proposed).json()
        assert any("run code 'S1' is already used" in error for error in replay["preview"]["errors"])
        statuses = {row["name"]: (row["status"], row["method"]) for row in replay["review"]}
        assert statuses["α-Pinene"] == ("confirmed", "alias") and statuses["Pinene"] == ("confirmed", "alias")
        assert statuses["Unknown sesquiterpene"] == ("pending", None)
        assert len(pubchem.calls) == calls

    def test_csv_with_semicolons_and_bad_cells(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, study, (first, _) = self.setup_study()
        content = "Compound;S1\nα-Pinene;12,4\nLimonene;abc\nalpha-pinene;1\n".encode("utf-8")
        created = self.upload(owner, study, content, "table.csv")
        assert created["sheets"][0]["rows"][1] == ["α-Pinene", "12,4"]
        preview = client.put(f"{BASE}/imports/{created['id']}/assignment", headers=owner, json={
            "sheet": "CSV", "header_row": 1, "settings": SETTINGS,
            "columns": [{"index": 0, "role": "name"}, {"index": 1, "role": "sample"}]}).json()["preview"]
        assert any("B3" in error and "not a number" in error for error in preview["errors"])
        assert any("also on row 2" in error for error in preview["errors"])
        assert client.post(f"{BASE}/studies/{study}/imports", headers=owner,
                           files={"file": ("table.ods", b"x", "application/octet-stream")}).status_code == 422
        assert client.post(f"{BASE}/studies/{study}/imports", headers=owner,
                           files={"file": ("table.xlsx", b"not a zip", "application/octet-stream")}).status_code == 422

    def test_lc_ms_and_library_evidence_columns(self, tmp_path, monkeypatch):
        """The results-table import records every evidence field the per-run CSV accepts."""
        monkeypatch.chdir(tmp_path)
        owner, study, (first, _) = self.setup_study()
        header = ["Compound", "m/z", "Adduct", "Δm (ppm)", "MS/MS", "MSI level", "n", "S1"]
        created = self.upload(owner, study, workbook([
            header,
            ["Chlorogenic acid", 353.0878, "[M-H]-", -1.4, "191.0556; 179.0344", 2, 3, 41.2],
            ["Luteolin 7-O-glucoside", 447.0933, "[M-H]-", "0,9", "285.0405", 2, 3, "tr"],
        ]))
        imports = f"{BASE}/imports/{created['id']}"
        roles = ["name", "mz_obs", "adduct", "mass_error_ppm", "msms_match", "id_level", "n", "sample"]
        lc = {"technique": "LC-MS/MS", "measurement_basis": "concentration", "unit": "mg/g DW",
              "analytical_method": "UHPLC-ESI-MS/MS, C18", "run_metadata": {"column": "C18", "ionisation_mode": "ESI-"}}
        assignment = {"sheet": "Table 2", "header_row": 1, "settings": lc,
                      "columns": [{"index": index, "role": role} for index, role in enumerate(roles)]}
        response = client.put(f"{imports}/assignment", headers=owner, json=assignment)
        assert response.status_code == 200, response.text
        assert response.json()["preview"]["errors"] == []
        for number in (2, 3):
            assert client.put(f"{imports}/rows/{number}/compound", headers=owner,
                              json={"action": "unidentified"}).status_code == 200
        confirmed = client.post(f"{imports}/confirm", headers=owner)
        assert confirmed.status_code == 201, confirmed.text
        profile_id = confirmed.json()["profiles"][0]["id"]
        with TestingSessionLocal() as db:
            rows = {row.feature: row for row in db.query(Measurement).filter_by(profile_id=profile_id)}
        acid = rows["Chlorogenic acid"]
        assert (acid.mz_obs, acid.adduct, acid.mass_error_ppm, acid.msms_match, acid.id_level, acid.n, acid.value) == (
            353.0878, "[M-H]-", -1.4, "191.0556; 179.0344", 2, 3, 41.2)
        assert (rows["Luteolin 7-O-glucoside"].mass_error_ppm, rows["Luteolin 7-O-glucoside"].qualifier) == (0.9, "trace")

        # LC-MS evidence is refused for a GC run, as in the per-run CSV.
        again = self.upload(owner, study, workbook([header, ["Chlorogenic acid", 353.0878, "[M-H]-", -1.4, "", 2, 3, 41.2]]))
        refused = client.put(f"{BASE}/imports/{again['id']}/assignment", headers=owner,
                             json={**assignment, "settings": SETTINGS}).json()["preview"]["errors"]
        assert any("adduct" in error and "mz_obs" in error and "GC-MS" in error for error in refused)

    def test_gc_ms_library_columns(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, study, (first, _) = self.setup_study()
        created = self.upload(owner, study, workbook([
            ["Compound", "RI exp", "NIST hit", "Match score", "S1"],
            ["α-Pinene", 932, "alpha-Pinene", 94, 12.4],
        ]))
        imports = f"{BASE}/imports/{created['id']}"
        roles = ["name", "ri_exp", "library_match", "library_score", "sample"]
        response = client.put(f"{imports}/assignment", headers=owner, json={
            "sheet": "Table 2", "header_row": 1, "settings": SETTINGS,
            "columns": [{"index": index, "role": role} for index, role in enumerate(roles)]})
        assert response.status_code == 200 and response.json()["preview"]["errors"] == []
        assert client.put(f"{imports}/rows/2/compound", headers=owner, json={"action": "unidentified"}).status_code == 200
        profile_id = client.post(f"{imports}/confirm", headers=owner).json()["profiles"][0]["id"]
        with TestingSessionLocal() as db:
            row = db.query(Measurement).filter_by(profile_id=profile_id).one()
        assert (row.library_match, row.library_score, row.ri_exp) == ("alpha-Pinene", 94, 932)

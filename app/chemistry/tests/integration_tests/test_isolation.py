import csv
from io import StringIO

from app.chemistry.models import ChemistryStructure, Measurement
from app.chemistry.services.profile_import import read_measurements
from app.chemistry.structures import parse_structure
from app.chemistry.tests.integration_tests.test_sample_vouchers import (BASE, headers_for, release_voucher,
                                                                        sample_payload, vouchers)
from app.chemistry.tests.integration_tests.test_spreadsheet_import import workbook
from app.tests import TestClass, TestingSessionLocal, client
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices

PHENYLETHANOL = "C[C@H](O)c1ccccc1"  # (S)-1-phenylethanol: not in the recorded PubChem data, so a "new" compound
NEW_KEY = parse_structure(PHENYLETHANOL)["inchikey"]
ROWS = [
    ["Compound", "SMILES", "Amount", "NMR experiments", "Solvent", "New or known", "Literature DOI",
     "Optical rotation", "CCDC", "Configuration type", "Identification", "Level", "m/z", "Adduct"],
    ["Compound 1", PHENYLETHANOL, 12.5, "¹H, ¹³C, COSY, HSQC, HMBC", "CDCl3", "new", None,
     "[α]D20 −35 (c 0.1, MeOH)", "CCDC 2345678", "absolute", "NMR; HRMS; X-ray", 1, 145.0624, "[M+Na]+"],
    ["α-Pinene", "CC1=CCC2CC1C2(C)C", 3.1, "1H;13C", "CDCl3", "known", "https://doi.org/10.1021/np000001",
     None, None, None, "NMR", 2, None, None],
    ["Unknown diterpene", None, 0.8, "1H", None, None, None, None, None, None, "NMR", 3, None, None],
]
ROLES = ["name", "smiles", "sample", "nmr_experiments", "nmr_solvent", "novelty", "literature_doi",
         "optical_rotation", "ccdc", "configuration_type", "id_basis", "id_level", "mz_obs", "adduct"]
SETTINGS = {"technique": "isolation", "measurement_basis": "isolated_mass", "unit": "mg",
            "run_metadata": {"isolation_procedure": "CH2Cl2 extract; silica CC; semi-preparative HPLC",
                             "nmr_frequency_mhz": "600", "nmr_solvent": "CDCl3",
                             "data_accessions": "nmrXiv P123"}}


class TestIsolation(TestClass):
    def setup_study(self):
        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        curator = headers_for(UserServices.create_super_user("Curator", "Example", "curator@example.org", "password"))
        (voucher,), _ = vouchers(1)
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "Isolation"}).json()["id"]
        created = client.post(f"{BASE}/studies/{study}/sample-preparations", headers=owner, json={
            "sample": sample_payload([(voucher, "sampled_from_voucher")], code="A1"),
            "preparation": {"batch_code": "E1", "kind": "extract", "method_reference": "CH2Cl2 maceration"}}).json()
        return owner, curator, voucher, study, created["preparation"]["id"]

    def import_table(self, owner, study, preparation, settings=SETTINGS):
        draft = client.post(f"{BASE}/studies/{study}/imports", headers=owner,
                            files={"file": ("isolated.xlsx", workbook(ROWS), "application/octet-stream")}).json()
        url = f"{BASE}/imports/{draft['id']}"
        columns = [{"index": index, "role": role, **({"preparation_id": preparation} if role == "sample" else {})}
                   for index, role in enumerate(ROLES)]
        response = client.put(f"{url}/assignment", headers=owner, json={
            "sheet": "Table 2", "header_row": 1, "columns": columns, "settings": settings})
        assert response.status_code == 200, response.text
        return url, response.json()

    def test_isolated_compounds_with_author_structures(self, pubchem, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, preparation = self.setup_study()

        _, wrong = self.import_table(owner, study, preparation, {**SETTINGS, "measurement_basis": "peak_area_percent",
                                                                 "unit": "%"})
        draft = client.post(f"{BASE}/studies/{study}/imports", headers=owner,
                            files={"file": ("x.xlsx", workbook(ROWS), "application/octet-stream")}).json()
        no_method = client.put(f"{BASE}/imports/{draft['id']}/assignment", headers=owner, json={
            "sheet": "Table 2", "header_row": 1, "columns": [{"index": 0, "role": "name"}, {"index": 2, "role": "sample"}],
            "settings": {**SETTINGS, "technique": "GC-MS", "measurement_basis": "peak_area_percent", "unit": "%"}})
        assert no_method.status_code == 200, no_method.text
        assert no_method.json()["preview"]["profiles"][0]["settings"]["analytical_method"] == "GC-MS"
        assert any("isolation technique" in error for error in wrong["preview"]["errors"])
        url, assigned = self.import_table(owner, study, preparation)
        preview = assigned["preview"]
        assert preview["errors"] == [] and preview["warnings"] == []
        evidence = preview["rows"][0]["evidence"]
        assert (evidence["nmr_experiments"], evidence["novelty"], evidence["ccdc"], evidence["id_basis"]) == (
            "1H;13C;COSY;HSQC;HMBC", "new", "CCDC 2345678", "HRMS;NMR;X-ray")
        assert preview["rows"][1]["evidence"]["literature_doi"] == "10.1021/np000001"

        review = {row["name"]: row for row in client.post(f"{url}/match", headers=owner).json()["review"]}
        new = review["Compound 1"]
        assert (new["status"], new["method"], new["match"]["cid"], new["match"]["author_structure"]) == (
            "needs_review", "author_structure", None, True)
        assert new["match"]["inchikey"] == NEW_KEY and new["match"]["structure_image"].startswith("/api/chemistry/depict.svg")
        assert (review["α-Pinene"]["match"]["cid"], review["α-Pinene"]["method"]) == (6654, "smiles")
        assert review["Unknown diterpene"]["status"] == "unmatched"
        assert client.put(f"{url}/rows/2/compound", headers=owner, json={"action": "parent"}).status_code == 409
        # A row without SMILES in the table can be given a structure during review.
        given = client.put(f"{url}/rows/4/compound", headers=owner, json={"action": "structure", "smiles": "OCC1CCCCC1"})
        assert given.status_code == 200, given.text
        assert (given.json()["status"], given.json()["method"], given.json()["match"]["cid"]) == (
            "confirmed", "author_structure", None)
        assert client.put(f"{url}/rows/4/compound", headers=owner, json={"action": "structure", "smiles": "C1CC"}).status_code == 422
        pubchem_hit = client.put(f"{url}/rows/4/compound", headers=owner,
                                 json={"action": "structure", "smiles": "CC1=CCC(CC1)C(=C)C"}).json()
        assert (pubchem_hit["method"], pubchem_hit["match"]["cid"]) == ("smiles", 22311)
        for number, action in ((2, "accept"), (3, "accept"), (4, "unidentified")):
            assert client.put(f"{url}/rows/{number}/compound", headers=owner, json={"action": action}).status_code == 200
        confirmed = client.post(f"{url}/confirm", headers=owner)
        assert confirmed.status_code == 201, confirmed.text
        profile = confirmed.json()["profiles"][0]
        assert (profile["technique"], profile["measurement_basis"], profile["unit"]) == ("isolation", "isolated_mass", "mg")
        assert profile["analytical_method"] == "Isolation and structure elucidation"
        assert profile["run_metadata"]["nmr_frequency_mhz"] == 600

        with TestingSessionLocal() as db:
            rows = {row.feature: row for row in db.query(Measurement).filter_by(profile_id=profile["id"])}
            structure = db.query(ChemistryStructure).one()
            assert (structure.inchikey, structure.name, structure.molecular_formula) == (NEW_KEY, "Compound 1", "C8H10O")
            first = rows["Compound 1"]
            assert (first.cid, first.structure_id, first.compound_match, first.value, first.id_level) == (
                None, structure.id, "author_structure", 12.5, 1)
            assert (rows["α-Pinene"].cid, rows["α-Pinene"].structure_id) == (6654, None)
            structure_id = structure.id

        # The run file carries the structure as SMILES and reads back to the same rows.
        source = client.get(f"{BASE}/profiles/{profile['id']}/source", headers=owner).content
        assert PHENYLETHANOL.encode() in source or parse_structure(PHENYLETHANOL)["smiles"].encode() in source
        _, reparsed, _ = read_measurements(source, "isolated_mass", "isolation", profile["run_metadata"])
        assert {row["feature"]: row["identifiers"].get("inchikey") for row in reparsed}["Compound 1"] == NEW_KEY

        # A correction can assign the same structure by SMILES; it is stored once.
        corrected = client.put(f"{BASE}/profiles/{profile['id']}/measurements/Unknown diterpene/compound", headers=owner,
                               json={"smiles": PHENYLETHANOL, "reason": "Same as compound 1"})
        assert corrected.status_code == 200, corrected.text
        assert (corrected.json()["new_structure_id"], corrected.json()["new_cid"]) == (structure_id, None)
        assert client.put(f"{BASE}/profiles/{profile['id']}/measurements/Unknown diterpene/compound", headers=owner,
                          json={"smiles": PHENYLETHANOL, "cid": 6654, "reason": "x"}).status_code == 422

        researcher = signed_in("lab@example.org")
        page = researcher.get(f"/researcher/profiles/{profile['id']}").text
        assert "Structure from the authors · C8H10O" in page and "/api/chemistry/depict.svg?smiles=" in page
        assert "NMR: 1H, 13C, COSY, HSQC, HMBC (CDCl3)" in page and "now the authors' structure" in page
        wizard = researcher.get(url.replace(f"{BASE}/imports", f"/researcher/studies/{study}/imports")).text
        assert 'data-kind="run"' in wizard and 'data-kind="preparation"' in wizard and 'value="isolation"' in wizard
        assert 'data-kind="preparation"' in researcher.get(f"/researcher/studies/{study}").text

        svg = client.get(f"{BASE}/depict.svg", params={"smiles": PHENYLETHANOL}, headers=owner)
        assert svg.status_code == 200 and svg.headers["content-type"].startswith("image/svg+xml")
        assert "default-src 'none'" in svg.headers["content-security-policy"]
        assert client.get(f"{BASE}/depict.svg", params={"smiles": "C1CC"}, headers=owner).status_code == 422
        assert client.get(f"{BASE}/public/structures/{structure_id}").status_code == 404  # unpublished until released
        assert client.get(f"/structures/{structure_id}").status_code == 404

        for path in (f"{BASE}/studies/{study}/visibility", f"{BASE}/profiles/{profile['id']}/visibility"):
            assert client.put(path, headers=curator, json={"is_public": True}).status_code == 200
        release_voucher(curator, voucher)
        public = client.get(f"{BASE}/public/structures/{structure_id}").json()
        assert (public["inchikey"], public["source"]) == (NEW_KEY, "author-supplied")
        assert client.get(f"{BASE}/public/structures/{structure_id}/depiction.svg").status_code == 200
        page = client.get(f"/structures/{structure_id}")
        assert page.status_code == 200 and NEW_KEY in page.text
        profile_page = client.get(f"/profiles/{profile['id']}").text
        assert f"/structures/{structure_id}" in profile_page and "New compound" in profile_page and "CCDC 2345678" in profile_page
        measurements = {row["feature"]: row for row in client.get(f"{BASE}/public/profiles/{profile['id']}").json()["measurements"]}
        assert measurements["Compound 1"]["structure"]["inchikey"] == NEW_KEY

        long = list(csv.DictReader(StringIO(client.get(f"{BASE}/public/export", params={"study_id": study}).text)))
        by_name = {row["feature"]: row for row in long}
        assert (by_name["Compound 1"]["structure_source"], by_name["Compound 1"]["inchikey"],
                by_name["Compound 1"]["nmr_experiments"]) == ("author", NEW_KEY, "1H;13C;COSY;HSQC;HMBC")
        assert by_name["α-Pinene"]["structure_source"] == "PubChem"
        wide = client.get(f"{BASE}/public/export", params={"study_id": study, "format": "wide"})
        assert wide.status_code == 409  # two measurements now share the structure; the long format still works
        assert f"inchikey:{NEW_KEY}" in wide.json()["detail"]

        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        draft = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Isolated compounds", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}], "profile_ids": [profile["id"]]}).json()
        snapshot = client.get(f"/api/depositions/{draft['id']}/draft/preview", headers=curator).json()["snapshot"]
        frozen = {row["feature"]: row for row in snapshot["profiles"][0]["measurements"]}
        assert snapshot["schema_version"] == 6 and snapshot["profiles"][0]["technique"] == "isolation"
        assert (frozen["Compound 1"]["structure"]["smiles"], frozen["Compound 1"]["optical_rotation"]) == (
            parse_structure(PHENYLETHANOL)["smiles"], "[α]D20 −35 (c 0.1, MeOH)")
        assert snapshot["profiles"][0]["compound_corrections"][0]["new_structure_id"] == structure_id

    def test_deleting_a_private_isolation_removes_its_unused_structure(self, pubchem, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, _, _, study, preparation = self.setup_study()
        url, _ = self.import_table(owner, study, preparation)
        client.post(f"{url}/match", headers=owner)
        for number, action in ((2, "accept"), (3, "accept"), (4, "unidentified")):
            client.put(f"{url}/rows/{number}/compound", headers=owner, json={"action": action})
        profile = client.post(f"{url}/confirm", headers=owner).json()["profiles"][0]["id"]
        with TestingSessionLocal() as db:
            assert db.query(ChemistryStructure).count() == 1
        assert client.delete(f"{BASE}/profiles/{profile}", headers=owner).status_code == 204
        with TestingSessionLocal() as db:
            assert db.query(ChemistryStructure).count() == 0

    def test_co_injection_evidence_and_isolation_rules(self, pubchem, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, _, _, _, preparation = self.setup_study()
        run = '{"polarity_class": "non-polar"}'

        def upload(content, technique="GC-MS", basis="peak_area_percent", unit="%", run_metadata=run, code="R"):
            return client.post(f"{BASE}/preparations/{preparation}/profiles", headers=owner,
                               data={"run_code": code, "analytical_method": "GC-MS", "unit": unit,
                                     "measurement_basis": basis, "technique": technique, "run_metadata": run_metadata},
                               files={"file": ("run.csv", content.encode(), "text/csv")})

        header = "feature,value,confidence,ri_exp,id_basis,id_level,standard_source,standard_reference\n"
        created = upload(header + "α-Pinene,60,identified,932,RI;co-injection,1,synthesised,10.1000/synthesis\n")
        assert created.status_code == 201, created.text
        with TestingSessionLocal() as db:
            row = db.query(Measurement).filter_by(profile_id=created.json()["id"]).one()
            assert (row.id_basis, row.id_level, row.standard_source, row.standard_reference) == (
                "RI;co-injection", 1, "synthesized", "10.1000/synthesis")
        no_standard = upload(header + "α-Pinene,60,identified,932,RI;MS,2,commercial,Sigma\n", code="R2")
        assert no_standard.status_code == 422 and "standard or co-injection" in no_standard.text
        nmr_on_gc = upload("feature,value,confidence,id_basis,id_level\nα-Pinene,60,identified,NMR,1\n", code="R3")
        assert nmr_on_gc.status_code == 422 and "MSI level 1" in nmr_on_gc.text
        mixed = upload("feature,value,confidence\nX,1,annotated\n", technique="isolation", code="R4", run_metadata="{}")
        assert mixed.status_code == 422 and "isolation technique" in mixed.text
        grams = upload("feature,value,confidence\nX,1,annotated\n", technique="isolation", basis="isolated_mass",
                       unit="mL", code="R5", run_metadata="{}")
        assert grams.status_code == 422 and "mg, g or µg" in grams.text

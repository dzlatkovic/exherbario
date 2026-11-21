"""Signed-in work pages: My work, study, profile, import and deposition editor."""

from app.chemistry.tests.integration_tests import test_compounds
from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE
from app.chemistry.tests.integration_tests.test_spreadsheet_import import workbook
from app.tests import TestClass, client
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices


class TestWorkPages(TestClass):
    setup_profile = test_compounds.TestCompounds.setup_profile

    def test_pages_and_lists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, upload = self.setup_profile()
        profile_id = upload.json()["id"]
        UserServices.create_user("Other", "Researcher", "other@example.org", "password")
        for path in ("/researcher", f"/researcher/studies/{study}", f"/researcher/profiles/{profile_id}",
                     "/researcher/depositions/new"):
            assert client.get(path, follow_redirects=False).status_code == 303, path

        imported = client.post(f"{BASE}/studies/{study}/imports", headers=owner,
                               files={"file": ("table2.xlsx", workbook(), "application/octet-stream")}).json()
        listed = client.get(f"{BASE}/studies/{study}/imports", headers=owner)
        assert listed.status_code == 200 and [item["id"] for item in listed.json()] == [imported["id"]]

        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        deposition = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Oil", "license": "CC BY 4.0", "profile_ids": [profile_id]}).json()
        mine = client.get("/api/depositions", headers=owner).json()
        assert [row["id"] for row in mine] == [deposition["id"]] and mine[0]["has_draft"]

        researcher = signed_in("lab@example.org")
        home = researcher.get("/researcher").text
        for text in ("Oils", f'href="/researcher/studies/{study}"', f'href="/researcher/depositions/{deposition["id"]}"',
                     "table2.xlsx", "New deposition"):
            assert text in home, text
        study_page = researcher.get(f"/researcher/studies/{study}").text
        assert f'href="/researcher/profiles/{profile_id}"' in study_page and "R-1" in study_page
        assert "/visibility" not in study_page  # release is for curators
        # Results come in through the table import only; the per-run CSV stays an API route.
        assert 'id="import-upload"' in study_page and "upload-run" not in study_page and "Upload a CSV run" not in study_page
        profile = researcher.get(f"/researcher/profiles/{profile_id}")
        assert profile.status_code == 200 and "α-Pinene" in profile.text and 'id="correct"' in profile.text
        wizard = researcher.get(f"/researcher/studies/{study}/imports/{imported['id']}")
        assert wizard.status_code == 200 and 'id="import-assign"' in wizard.text
        editor = researcher.get(f"/researcher/depositions/{deposition['id']}")
        assert editor.status_code == 200 and f'data-deposition="{deposition["id"]}"' in editor.text
        assert 'data-curator="false"' in editor.text
        assert researcher.get("/researcher/depositions/new").status_code == 200

        other = signed_in("other@example.org")
        assert "Oils" not in other.get("/researcher").text
        for path in (f"/researcher/studies/{study}", f"/researcher/profiles/{profile_id}",
                     f"/researcher/studies/{study}/imports/{imported['id']}", f"/researcher/depositions/{deposition['id']}",
                     "/researcher/studies/nothing"):
            assert other.get(path).status_code == 404, path

        admin = signed_in("curator@example.org")
        assert 'data-curator="true"' in admin.get(f"/researcher/depositions/{deposition['id']}").text
        assert "Register a voucher" in admin.get("/researcher").text
        assert f"/api/chemistry/studies/{study}/visibility" in admin.get(f"/researcher/studies/{study}").text

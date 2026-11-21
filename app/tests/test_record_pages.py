"""Public study, profile and compound pages, and the signed-in specimen record."""

from fastapi.testclient import TestClient

from app.chemistry.tests.integration_tests import test_compounds
from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, release_voucher
from app.main import app
from app.tests import TestClass, client
from app.users.services import UserServices
from app.users.session import CSRF_COOKIE


def signed_in(email):
    web = TestClient(app)
    web.post("/sign-in", data={"email": email, "password": "password", "next": "/researcher"})
    return web


class TestRecordPages(TestClass):
    setup_profile = test_compounds.TestCompounds.setup_profile

    def released_profile(self):
        owner, curator, voucher, study, upload = self.setup_profile()
        profile_id = upload.json()["id"]
        for url in (f"{BASE}/studies/{study}/visibility", f"{BASE}/profiles/{profile_id}/visibility"):
            assert client.put(url, headers=curator, json={"is_public": True}).status_code == 200
        release_voucher(curator, voucher)
        return owner, curator, voucher, study, profile_id

    def test_public_study_profile_and_compound_pages(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, profile_id = self.released_profile()
        study_page = client.get(f"/studies/{study}")
        assert study_page.status_code == 200
        assert f'href="/profiles/{profile_id}"' in study_page.text and "GC-MS" in study_page.text
        assert f"/api/chemistry/public/export?study_id={study}&amp;format=wide" in study_page.text

        page = client.get(f"/profiles/{profile_id}").text
        for text in ('href="/compounds/6654"', ">α-Pinene</a>", "Unidentified sesquiterpene", "· unlinked", ">tr<",
                     "932", "RI, MS", "MSI 2", "Yield", "0.42% (w/w) from 100 g", f'href="/specimens/{voucher}"',
                     "Sampled from the voucher", "Column polarity", f'href="/studies/{study}"'):
            assert text in page, text
        assert "m/z" not in page  # evidence columns appear only when a measurement has them

        assert client.put(f"{BASE}/profiles/{profile_id}/measurements/Limonene/compound", headers=owner,
                          json={"cid": None, "reason": "Co-elutes with β-phellandrene"}).status_code == 200
        assert "Co-elutes with β-phellandrene" in client.get(f"/profiles/{profile_id}").text

        compound = client.get("/compounds/6654")
        assert compound.status_code == 200 and "alpha-Pinene" in compound.text and "80-56-8" in compound.text
        assert "img-src 'self' https://pubchem.ncbi.nlm.nih.gov" in compound.headers["content-security-policy"]
        assert client.get("/compounds/82227").status_code == 404

        assert client.put(f"{BASE}/profiles/{profile_id}/visibility", headers=curator, json={"is_public": False}).status_code == 200
        hidden, unknown = client.get(f"/profiles/{profile_id}"), client.get("/profiles/nothing")
        assert hidden.status_code == unknown.status_code == 404
        assert client.get(f"/studies/{study}").status_code == 404  # no released profile left

    def test_staff_specimen_record(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, _ = self.setup_profile()
        UserServices.create_user("Other", "Researcher", "other@example.org", "password")
        assert client.get(f"/researcher/specimens/{voucher}", follow_redirects=False).status_code == 303

        researcher = signed_in("lab@example.org")
        page = researcher.get(f"/researcher/specimens/{voucher}")
        assert page.status_code == 200 and "Private" in page.text and "Suva mt." in page.text and "43.0, 22.0" in page.text
        assert "Box box1" in page.text and "John Smith" in page.text and "Oils" in page.text
        assert 'id="release"' not in page.text and 'id="redetermine"' not in page.text
        assert "Oils" not in signed_in("other@example.org").get(f"/researcher/specimens/{voucher}").text

        admin = signed_in("curator@example.org")
        curated = admin.get(f"/researcher/specimens/{voucher}").text
        assert 'id="release"' in curated and 'id="redetermine"' in curated and 'id="upload-photo"' in curated
        token = {"X-CSRF-Token": admin.cookies[CSRF_COOKIE]}
        assert admin.put(f"/api/specimen/{voucher}/visibility", headers=token,
                         json={"is_public": True, "public_location": "region"}).status_code == 200
        released = admin.get(f"/researcher/specimens/{voucher}").text
        assert "Released · region shown" in released and f'href="/specimens/{voucher}"' in released
        staff_read = admin.get(f"/api/specimen/get-specimen-by-id?specimen_id={voucher}").json()
        assert (staff_read["is_public"], staff_read["public_location"]) == (True, "region")
        assert f'href="/researcher/specimens/{voucher}"' in admin.get(f"/specimens/{voucher}").text
        assert "Staff record" not in client.get(f"/specimens/{voucher}").text

        label = researcher.get(f"/researcher/specimens/{voucher}/label")
        assert label.status_code == 200 and "<svg" in label.text and f"/specimens/{voucher}" in label.text
        assert "Leg. John Smith" in label.text and "Serbia, Nis: Suva mt." in label.text
        assert researcher.get("/researcher/specimens/nothing").status_code == 404

"""Staff record actions as the page scripts send them (session cookie and CSRF header), and the
layout of the voucher workspace, My work and catalog results."""

from io import BytesIO

from PIL import Image
from sqlalchemy import select

from app.chemistry.tests.integration_tests import test_compounds
from app.db import SessionLocal
from app.specimen.models import ScientificCorrection, Specimen
from app.tests import TestClass, client
from app.tests.test_catalog_pages import make_vouchers
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices
from app.users.session import CSRF_COOKIE


def jpeg():
    data = BytesIO()
    Image.new("RGB", (4, 4), "green").save(data, "JPEG")
    return data.getvalue()


class TestStaffActions(TestClass):
    setup_profile = test_compounds.TestCompounds.setup_profile

    def test_photograph_upload_and_approval(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _, _, voucher, _, _ = self.setup_profile()
        admin = signed_in("curator@example.org")
        token = {"X-CSRF-Token": admin.cookies[CSRF_COOKIE]}
        page = admin.get(f"/researcher/specimens/{voucher}").text
        assert 'id="photo-gallery" hidden' in page and 'id="photo-empty"' in page
        assert 'method="post" enctype="multipart/form-data"' in page  # never a GET with the file name in the URL

        # What specimen.js sends: the file alone in the body, specimen and type in the query.
        uploaded = admin.post(f"/api/image/upload-image?specimen_id={voucher}&image_type=herbarium",
                              headers=token, files={"file": ("sheet.jpg", jpeg(), "image/jpeg")})
        assert uploaded.status_code == 200, uploaded.text
        photo = uploaded.json()
        assert photo["is_public"] is False and photo["image_type"] == "herbarium"  # the script renders from these
        assert admin.get(f"/api/image/{photo['image_id']}/original").status_code == 200

        page = admin.get(f"/researcher/specimens/{voucher}").text
        assert f'data-image="{photo["image_id"]}"' in page and "Not public" in page and ">Approve</button>" in page
        assert 'id="photo-empty"' not in page

        approved = admin.put(f"/api/image/{photo['image_id']}/visibility", headers=token, json={"is_public": True})
        assert approved.status_code == 200 and approved.json() == {"is_public": True}
        page = admin.get(f"/researcher/specimens/{voucher}").text
        assert "Approved" in page and ">Withdraw</button>" in page
        assert admin.put(f"/api/image/{photo['image_id']}/visibility", headers=token,
                         json={"is_public": False}).json() == {"is_public": False}

    def test_collection_corrections_and_layout(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _, _, voucher, _, _ = self.setup_profile()
        researcher, admin = signed_in("lab@example.org"), signed_in("curator@example.org")
        assert 'id="edit-collection"' not in researcher.get(f"/researcher/specimens/{voucher}").text

        page = admin.get(f"/researcher/specimens/{voucher}").text
        assert 'id="edit-collection"' in page and "Edit collection details" in page and 'id="redetermine"' in page
        # Visibility sits with the title; identification and collection come before photographs.
        assert page.index('class="status-chip">Private') < page.index('id="release"') < page.index('id="identification-title"')
        assert page.index('id="identification-title"') < page.index('id="collection-title"') < page.index('id="photos-title"')
        assert "Release to the public catalog" in page and 'id="release-title"' not in page

        with SessionLocal() as db:
            location = db.get(Specimen, voucher).field_loc_id
        token = {"X-CSRF-Token": admin.cookies[CSRF_COOKIE]}
        reason = "Date mistyped from the label"
        assert admin.put(f"/api/specimen/update-specimen?specimen_id={voucher}", headers=token,
                         json={"collection_date": "2019-06-14", "collector_number": "JS 41",
                               "correction_reason": reason}).status_code == 200
        assert admin.put(f"/api/field-locations/update-field-loc?field_loc_id={location}", headers=token,
                         json={"habitat": "Beech forest", "correction_reason": reason}).status_code == 200
        page = admin.get(f"/researcher/specimens/{voucher}").text
        assert "2019-06-14" in page and "JS 41" in page and "Beech forest" in page
        with SessionLocal() as db:
            reasons = db.scalars(select(ScientificCorrection.reason).where(
                (ScientificCorrection.specimen_id == voucher) | (ScientificCorrection.field_loc_id == location))).all()
        assert reasons.count(reason) == 2

    def test_voucher_workspace_and_my_work(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _, _, voucher, study, _ = self.setup_profile()
        admin = signed_in("curator@example.org")
        vouchers = admin.get("/curation/vouchers").text
        # Search comes first in the page, with a button that opens registration on narrow screens.
        assert vouchers.index('id="find-title"') < vouchers.index('id="register-title"')
        assert 'class="button primary narrow-only" href="#register-section"' in vouchers

        work = signed_in("lab@example.org").get("/researcher").text
        assert 'href="#new-study"' in work and "Create your first study" not in work
        assert work.index("New study") < work.index("New deposition")

        UserServices.create_user("New", "Researcher", "new@example.org", "password")
        empty = signed_in("new@example.org").get("/researcher").text
        assert "Create your first study" in empty and 'id="create-study"' in empty
        assert 'href="#new-study"' not in empty and 'class="primary">Create study' in empty

    def test_public_navigation_and_search_results(self):
        public = client.get("/specimens").text
        assert ">Published datasets</a>" in public and ">Depositions</a>" not in public
        assert "<h1 class=\"title\">Published datasets</h1>" in client.get("/depositions").text

        make_vouchers(4, released={0, 1, 2, 3})
        page = client.get("/specimens", params={"q": "maple"}).text
        assert '<span class="common-name">Red maple</span>' in page
        assert "Download these results (CSV)" in page and "Download full catalog (Darwin Core)" in page
        by_number = client.get("/specimens", params={"q": "R-002"}).text
        assert "matched registration number R-002" in by_number
        results = client.get("/api/specimen", params={"q": "maple"}).json()["items"]
        assert results and {item["matched_on"] for item in results} == {"common name"}

"""Step 4: public deposition index, review queue, version management and the curation area."""

import pytest
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.specimen.models import Specimen
from app.tests import TestClass, client
from app.tests.test_record_pages import TestRecordPages, signed_in
from app.users.models import User


def publish(deposition_id, curator):
    with pytest.MonkeyPatch.context() as patch:  # only here: an https address makes the session cookie Secure
        patch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu/")
        preview = client.get(f"/api/depositions/{deposition_id}/draft/preview", headers=curator)
        assert preview.status_code == 200, preview.text
        preview = preview.json()
        published = client.post(f"/api/depositions/{deposition_id}/publish", headers=curator, json={
            "draft_revision": preview["draft_revision"], "snapshot_sha256": preview["snapshot_sha256"]})
    assert published.status_code == 200, published.text
    return published.json()


class TestCuration(TestClass):
    setup_profile = TestRecordPages.setup_profile
    released_profile = TestRecordPages.released_profile

    def published(self):
        owner, curator, voucher, study, profile_id = self.released_profile()
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example University"}).status_code == 201
        draft = {"institution": "EXU", "title": "Achillea essential oil", "license": "CC BY 4.0",
                 "contributors": [{"name": "F. Scientist", "role": "analyst"}], "profile_ids": [profile_id]}
        deposition = client.post("/api/depositions", headers=owner, json=draft).json()
        return owner, curator, voucher, deposition["id"], publish(deposition["id"], curator)

    def test_public_index_lists_published_versions_only(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, deposition_id, version = self.published()
        unpublished = client.post("/api/depositions", headers=owner, json={"institution": "EXU", "title": "Still a draft"}).json()

        listed = client.get("/api/depositions/public").json()
        assert listed["total"] == 1 and listed["items"][0]["title"] == "Achillea essential oil"
        item = listed["items"][0]
        assert item["path"] == f"/depositions/EXU/{version['accession']}/versions/1" and item["status"] == "published"
        assert client.get("/api/depositions/public", params={"q": "draft"}).json()["total"] == 0
        assert client.get("/api/depositions/public", params={"q": "ACHILLEA"}).json()["total"] == 1
        assert unpublished["id"] not in str(listed)

        page = client.get("/depositions")
        assert page.status_code == 200 and "Achillea essential oil" in page.text and item["path"] in page.text
        assert "Still a draft" not in page.text and 'href="/depositions"' in page.text
        assert "No depositions match" in client.get("/depositions", params={"q": "nothing"}).text

        base = f"/api/depositions/{deposition_id}/versions/1"
        assert client.put(f"{base}/article-doi", headers=curator, json={"doi": "10.3390/plants1"}).status_code == 200
        assert client.put(f"{base}/doi", headers=curator, json={"doi": "10.5281/zenodo.1", "agency": "zenodo"}).status_code == 200
        assert client.get("/api/depositions/public", params={"q": "zenodo.1"}).json()["items"][0]["dataset_doi"] == "10.5281/zenodo.1"

        version_page = item["path"]
        assert 'id="manage-version"' not in client.get(version_page).text
        assert 'id="manage-version"' not in signed_in("lab@example.org").get(version_page).text
        managed = signed_in("curator@example.org").get(version_page).text
        assert f'data-deposition="{deposition_id}"' in managed and 'id="withdraw-version"' in managed
        assert 'id="dataset-doi"' not in managed  # already registered

        assert client.post(f"{base}/withdraw", headers=curator, json={"reason": "Wrong voucher"}).status_code == 200
        assert client.get("/api/depositions/public").json()["items"][0]["status"] == "withdrawn"
        assert "Withdrawn" in client.get("/depositions").text
        notice = client.get(version_page)
        assert notice.status_code == 410 and "Wrong voucher" in notice.text

    def test_review_queue(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, profile_id = self.released_profile()
        assert client.post("/api/institutions", headers=curator, json={"code": "EXU", "name": "Example"}).status_code == 201
        deposition = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Oil", "license": "CC BY 4.0", "profile_ids": [profile_id],
            "contributors": [{"name": "F. Scientist", "role": "analyst"}]}).json()
        assert deposition["submitted_at"] is None
        submission = f"/api/depositions/{deposition['id']}/submission"

        other = signed_in("lab@example.org")
        assert client.get("/api/depositions/review", headers=owner).status_code == 403
        assert client.post(submission, headers=curator).status_code == 200  # curators may act on any draft
        assert client.delete(submission, headers=owner).json()["submitted_at"] is None
        assert client.get("/api/depositions/review", headers=curator).json() == []

        submitted = client.post(submission, headers=owner).json()
        assert submitted["submitted_at"]
        assert client.post(submission, headers=owner).json()["submitted_at"] == submitted["submitted_at"]
        queue = client.get("/api/depositions/review", headers=curator).json()
        assert [(item["id"], item["owner"], item["title"]) for item in queue] == [(deposition["id"], "Lab Owner", "Oil")]
        assert client.get("/api/depositions", headers=owner).json()[0]["in_review"] is True
        assert "in review" in other.get("/researcher").text

        review = signed_in("curator@example.org").get("/curation")
        assert review.status_code == 200 and f'href="/researcher/depositions/{deposition["id"]}"' in review.text
        assert 'id="submission"' in other.get(f"/researcher/depositions/{deposition['id']}").text
        assert 'id="submission"' not in signed_in("curator@example.org").get(f"/researcher/depositions/{deposition['id']}").text

        publish(deposition["id"], curator)
        assert client.get("/api/depositions/review", headers=curator).json() == []
        assert client.post(submission, headers=owner).status_code == 409  # nothing left to review

    def test_curation_pages_and_refusals(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, _ = self.setup_profile()
        pages = ["/curation", "/curation/vouchers", "/curation/directories", "/curation/accounts",
                 *(f"/curation/directories/{kind}" for kind in ("institutions", "storage", "locations", "bibliography", "taxonomy"))]
        researcher, admin = signed_in("lab@example.org"), signed_in("curator@example.org")
        for path in pages:
            assert client.get(path, follow_redirects=False).status_code == 303, path
            assert researcher.get(path).status_code == 404, path
            assert admin.get(path).status_code == 200, path
        assert admin.get("/curation/directories/nothing").status_code == 404
        assert 'href="/curation"' in admin.get("/researcher").text and 'href="/curation"' not in researcher.get("/researcher").text
        accounts = admin.get("/curation/accounts").text
        assert "lab@example.org" in accounts and "You" in accounts and 'id="new-account"' in accounts

        with SessionLocal() as db:
            specimen = db.get(Specimen, voucher)
            storage, location, taxon, collector = specimen.storage_id, specimen.field_loc_id, specimen.taxon_id, specimen.collected_by
            me = db.scalar(select(User.user_id).where(User.email == "curator@example.org"))
        refusals = {
            f"/api/storage/delete-storage?storage_id={storage}": "Move them to another box",
            f"/api/field-locations/delete-field-loc?field_loc_id={location}": "referenced by a voucher",
            f"/api/taxonomy/delete-taxon?taxon_id={taxon}": "can't be deleted",
            f"/api/users/delete-user?user_id={collector}": "Deactivate it instead",
            f"/api/users/delete-user?user_id={me}": "your own account",
        }
        for path, reason in refusals.items():
            response = client.delete(path, headers=curator)
            assert response.status_code == 409 and reason in response.json()["detail"], (path, response.text)
        assert client.put(f"/api/users/update/is_active?user_id={me}&is_active=false", headers=curator).status_code == 409
        assert client.put(f"/api/users/update/is_active?user_id={collector}&is_active=false", headers=curator).json()["is_active"] is False
        unused = client.post("/api/storage/create-new-storage", headers=curator, json={"box": "spare"}).json()
        assert client.delete(f"/api/storage/delete-storage?storage_id={unused['storage_id']}", headers=curator).status_code == 200

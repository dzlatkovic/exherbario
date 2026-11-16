from io import BytesIO

from PIL import Image

from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import TestClass, client
from app.users.services import UserServices, signJWT


def headers_for(user):
    role = "super_user" if user.is_superuser else "classic_user"
    return {"Authorization": "Bearer " + signJWT(user.user_id, role)["access_token"]}


class TestCatalog(TestClass):
    def test_catalog_search_detail_history_and_jpeg(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        specimen = SpecimenFixtures.create_test_specimen()
        admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        headers = headers_for(admin)
        update = client.put("/api/specimen/update-specimen", params={"specimen_id": specimen.specimen_id},
                            json={"subnomen": "New determination"}, headers=headers)
        assert update.status_code == 200, update.text

        image = BytesIO()
        Image.new("RGB", (4, 4), "green").save(image, "JPEG")
        upload = client.post("/api/image/upload-image", headers=headers,
                             params={"specimen_id": specimen.specimen_id, "image_type": "herbarium"},
                             files={"file": ("voucher.jpg", image.getvalue(), "image/jpeg")})
        assert upload.status_code == 200, upload.text
        profile_image = client.get("/api/image/" + upload.json()["image_id"] + "/content")
        assert profile_image.headers["content-type"] == "image/jpeg"
        assert profile_image.content == image.getvalue()

        results = client.get("/api/specimen", params={"reg_no": specimen.reg_no, "q": "determination"})
        assert results.json()["total"] == 1
        export = client.get("/api/specimen/export", params={"region": "Nis"})
        assert export.status_code == 200 and "New determination" in export.text
        detail = client.get("/api/specimen/" + specimen.specimen_id)
        assert detail.status_code == 200, detail.text
        assert detail.json()["subnomen"] == "New determination"
        assert detail.json()["photos"][0]["content_url"] == "/api/image/" + upload.json()["image_id"] + "/content"
        assert "curator@example.org" not in detail.text and "file_path" not in detail.text
        history = client.get(f"/api/specimen/{specimen.specimen_id}/revisions")
        assert history.json()[0]["previous_subnomen"] == specimen.subnomen
        assert client.get("/").json() == {"message": "In Progress"}

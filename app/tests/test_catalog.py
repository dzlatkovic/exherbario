from io import BytesIO
from re import sub

from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from app.main import app
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
        voucher = f"/api/specimen/{specimen.specimen_id}"
        assert client.get(voucher).status_code == 404
        assert client.get(f"{voucher}/revisions").status_code == 404
        assert client.get(f"{voucher}/publications").status_code == 404
        assert client.get("/api/specimen").json()["total"] == 0
        update = client.put("/api/specimen/update-specimen", params={"specimen_id": specimen.specimen_id},
                            json={"subnomen": "New determination"}, headers=headers)
        assert update.status_code == 200, update.text

        image = BytesIO()
        metadata = Image.Exif()
        metadata[34853] = {1: "N", 2: tuple(IFDRational(value) for value in (42, 10, 30))}
        Image.new("RGB", (4, 4), "green").save(image, "JPEG", exif=metadata)
        assert Image.open(image).getexif().get_ifd(34853)
        upload = client.post("/api/image/upload-image", headers=headers,
                             params={"specimen_id": specimen.specimen_id, "image_type": "herbarium"},
                             files={"file": ("voucher.jpg", image.getvalue(), "image/jpeg")})
        assert upload.status_code == 200, upload.text
        photo = f"/api/image/{upload.json()['image_id']}"
        assert client.get(f"{photo}/content").status_code == 404
        assert client.get(f"{photo}/original").status_code == 403
        assert client.get(f"{photo}/original", headers=headers).content == image.getvalue()
        assert client.put(f"{photo}/visibility", headers=headers, json={"is_public": True}).status_code == 200
        assert client.get(f"{photo}/content").status_code == 404
        state = {"is_public": True, "public_location": "withheld"}
        assert client.put(f"{voucher}/visibility", headers=headers, json=state).status_code == 200
        profile_image = client.get(f"{photo}/content")
        assert profile_image.headers["content-type"] == "image/jpeg"
        assert profile_image.headers["cache-control"] == "no-store"
        with Image.open(BytesIO(profile_image.content)) as public_image:
            assert not public_image.getexif()
            assert public_image.size == (4, 4)

        results = client.get("/api/specimen", params={"reg_no": specimen.reg_no, "q": "determination"})
        assert results.json()["total"] == 1
        assert results.json()["items"][0]["region"] is None
        assert client.get("/api/specimen", params={"region": "Nis"}).json()["total"] == 0
        assert "New determination" not in client.get("/api/specimen/export", params={"region": "Nis"}).text
        assert client.get("/api/specimen", params={"box": "box1"}).status_code == 422
        assert client.get(voucher).json()["location"] is None
        state["public_location"] = "region"
        assert client.put(f"{voucher}/visibility", headers=headers, json=state).status_code == 200
        export = client.get("/api/specimen/export", params={"region": "Nis"})
        assert export.status_code == 200 and "New determination" in export.text
        assert "Suva mt." not in export.text
        detail = client.get(voucher)
        assert detail.status_code == 200, detail.text
        assert detail.json()["subnomen"] == "New determination"
        assert detail.json()["location"] == {"region": "Nis", "country": "Serbia"}
        assert detail.json()["photos"][0]["content_url"] == "/api/image/" + upload.json()["image_id"] + "/content"
        assert "curator@example.org" not in detail.text and "file_path" not in detail.text
        history = client.get(f"/api/specimen/{specimen.specimen_id}/revisions")
        assert history.json()[0]["previous_subnomen"] == specimen.subnomen
        assert "revised_by" not in history.json()[0]
        assert client.put(f"{photo}/visibility", headers=headers, json={"is_public": False}).status_code == 200
        assert client.get(voucher).json()["photos"] == []
        assert client.get(f"{photo}/content").status_code == 404
        assert client.put(f"{photo}/visibility", headers=headers, json={"is_public": True}).status_code == 200
        state["is_public"] = False
        assert client.put(f"{voucher}/visibility", headers=headers, json=state).status_code == 200
        assert client.get(f"{photo}/content").status_code == 404
        assert client.get(f"{voucher}/revisions").status_code == 404
        assert "New determination" not in client.get("/api/specimen/export").text
        assert client.get("/").json() == {"message": "In Progress"}

    def test_researcher_reads_and_curator_controls(self):
        specimen = SpecimenFixtures.create_test_specimen()
        researcher = UserServices.create_user("Lab", "Reader", "lab@example.org", "password")
        admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        headers = headers_for(researcher)
        voucher = f"/api/specimen/{specimen.specimen_id}"
        assert client.get(voucher, headers=headers).status_code == 404
        assert client.put(f"{voucher}/visibility", headers=headers,
                          json={"is_public": True, "public_location": "region"}).status_code == 403
        assert client.put("/api/image/missing/visibility", headers=headers,
                          json={"is_public": True}).status_code == 403
        accounts = "/api/users/get-all-users"
        assert client.get(accounts, headers=headers).status_code == 403
        assert client.get(accounts, headers=headers_for(admin)).status_code == 200
        gps = client.get("/api/specimen/get-gps", headers=headers, params={"keyword": specimen.subnomen})
        assert gps.json()[specimen.reg_no]["gps"] == [43.0, 22.0]
        assert client.get("/api/specimen/visualize-gps", headers=headers,
                          params={"keyword": specimen.subnomen}).status_code == 200
        assert client.get("/api/specimen/generate_qr_code", headers=headers,
                          params={"reg_no": specimen.reg_no}).headers["content-type"] == "image/png"

    def test_only_allowlisted_api_reads_are_anonymous(self):
        anonymous_routes = {
            "/api/specimen", "/api/specimen/export", "/api/specimen/{specimen_id}",
            "/api/specimen/{specimen_id}/revisions", "/api/specimen/{specimen_id}/publications",
            "/api/image/{image_id}/content", "/api/taxonomy",
            "/api/taxonomy/get-taxon-by-id", "/api/taxonomy/get-taxon-by-gbif",
            "/api/chemistry/public/studies/{study_id}", "/api/chemistry/public/profiles/{profile_id}",
            "/api/chemistry/public/specimens/{specimen_id}/profiles",
        }
        for route in app.routes:
            if not route.path.startswith("/api/") or "GET" not in route.methods:
                continue
            response = client.get(sub(r"\{[^}]+\}", "missing", route.path))
            if route.path in anonymous_routes:
                assert response.status_code != 403, route.path
            else:
                assert response.status_code == 403, route.path

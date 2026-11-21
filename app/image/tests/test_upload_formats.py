"""Uploads are decoded by Pillow's JPEG plugin only; other format parsers never see untrusted bytes."""

from io import BytesIO

from PIL import Image, PsdImagePlugin

from app.tests import TestClass, client
from app.users.services import UserServices, signJWT


class TestUploadFormats(TestClass):
    def test_only_the_jpeg_decoder_parses_uploads(self, monkeypatch):
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        headers = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        specimen = client.post("/api/specimen/create-new-specimen", headers=headers, json={"holding_type": "local"}).json()

        def upload(name, data, content_type):
            return client.post("/api/image/upload-image", headers=headers,
                               params={"specimen_id": specimen["specimen_id"], "image_type": "herbarium"},
                               files={"file": (name, data, content_type)})

        parsed = []
        monkeypatch.setattr(PsdImagePlugin.PsdImageFile, "_open", lambda self: parsed.append("psd"))
        psd = b"8BPS\x00\x01" + bytes(20)  # a Photoshop header, the kind of file several advisories target
        refused = upload("sheet.psd", psd, "image/jpeg")
        assert refused.status_code == 400 and refused.json()["detail"] == "Only JPEG images are supported."
        assert parsed == []

        png = BytesIO()
        Image.new("RGB", (4, 4), "green").save(png, "PNG")
        refused = upload("sheet.png", png.getvalue(), "image/png")
        assert refused.status_code == 400 and refused.json()["detail"] == "Only JPEG images are supported."

        jpeg = BytesIO()
        Image.new("RGB", (4, 4), "green").save(jpeg, "JPEG")
        assert upload("sheet.jpg", jpeg.getvalue(), "image/jpeg").status_code == 200

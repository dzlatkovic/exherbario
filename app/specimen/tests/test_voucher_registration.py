from app.specimen.models import Revision, ScientificCorrection
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices, signJWT


class TestVoucherRegistration(TestClass):
    def test_register_local_and_external_vouchers(self):
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        headers = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        register = "/api/specimen/create-new-specimen"
        assert client.post(register, json={"holding_type": "local"}).status_code == 403
        local = client.post(register, headers=headers, json={"holding_type": "local"})
        assert local.status_code == 200, local.text
        assert local.json()["reg_no"] is None
        assert local.json()["accession"] is None
        assert local.json()["collection_date"] is None
        assert local.json()["taxon_id"] is None
        assert local.json()["storage_id"] is None
        assert client.post(register, headers=headers, json={"holding_type": "local"}).status_code == 200

        label = "  Label line one\r\nLoc. only on the original label  "
        external = {
            "holding_type": "external",
            "holding_institution": "Example University",
            "collection": "Herbarium A",
            "accession": "BOT-2024-000001",
            "verbatim_label": label,
            "collector_name": "F. Collector",
            "determiner_name": "D. Botanist",
            "determination_date": "2024-05-02",
            "subnomen": "Achillea cf. millefolium",
        }
        created = client.post(register, headers=headers, json=external)
        assert created.status_code == 200, created.text
        voucher = created.json()
        specimen_id = voucher["specimen_id"]
        assert {key: voucher[key] for key in external} == external
        assert voucher["collected_by"] is None and voucher["verified_by"] is None
        duplicate = client.post(register, headers=headers, json={**external, "holding_type": "local"})
        assert duplicate.status_code == 409
        other = client.post(register, headers=headers, json={**external, "collection": "Herbarium B"})
        assert other.status_code == 200
        assert other.json()["specimen_id"] != specimen_id
        another_institution = client.post(register, headers=headers, json={
            **external, "holding_institution": "Another University",
        })
        assert another_institution.status_code == 200

        by_id = {"specimen_id": specimen_id}
        stored = client.get("/api/specimen/get-specimen-by-id", params=by_id, headers=headers)
        assert stored.json()["verbatim_label"] == label
        loaded_label = client.get("/api/specimen/get-herbarium-label", params=by_id, headers=headers)
        assert loaded_label.json()["collected_by"] == "F. Collector"
        assert loaded_label.json()["gps"] is None
        assert client.get("/api/specimen/generate_qr_code", params=by_id, headers=headers).status_code == 200
        assert client.post("/api/weather/download-weather_data", params=by_id, headers=headers).status_code == 400

        public = f"/api/specimen/{specimen_id}"
        assert client.get(public).status_code == 404
        assert client.put(f"{public}/visibility", headers=headers,
                          json={"is_public": True, "public_location": "withheld"}).status_code == 200
        detail = client.get(public).json()
        assert detail["accession"] == external["accession"]
        assert detail["determination_date"] == external["determination_date"]
        assert "verbatim_label" not in detail
        assert "collector_name" not in detail and "determiner_name" not in detail
        filters = {key: external[key] for key in ("accession", "holding_institution", "collection")}
        assert client.get("/api/specimen", params=filters).json()["total"] == 1
        assert client.get("/api/specimen/export", params=filters).text.count(external["accession"]) == 1

        study = client.post("/api/chemistry/studies", headers=headers, json={"title": "Voucher study"})
        study_url = f"/api/chemistry/studies/{study.json()['id']}"
        sample = client.post(f"{study_url}/samples", headers=headers, json={
            "specimen_id": specimen_id, "code": "Voucher sample", "plant_part": "leaf",
            "collection_event": "Synthetic", "voucher_relationship": "collected_alongside",
        })
        assert sample.status_code == 201, sample.text
        assert client.get(study_url, headers=headers).json()["samples"][0]["accession"] == external["accession"]

        change = "/api/specimen/update-specimen"
        assert client.put(change, params=by_id, headers=headers,
                          json={"verbatim_label": None}).status_code == 400
        assert client.put(change, params=by_id, headers=headers, json={
            "collection": "Herbarium B", "correction_reason": "Check the collection code",
        }).status_code == 409
        update = client.put(change, params=by_id, headers=headers, json={"subnomen": "Achillea sp."})
        assert update.status_code == 200, update.text
        assert update.json()["determiner_name"] is None
        assert update.json()["determination_date"] is None
        correction = client.put(change, params=by_id, headers=headers, json={
            "verbatim_label": None, "correction_reason": "Original label unavailable",
        })
        assert correction.status_code == 200 and correction.json()["verbatim_label"] is None
        with TestingSessionLocal() as db:
            revision = db.query(Revision).filter_by(specimen_id=specimen_id).one()
            assert revision.revised_by == curator.user_id
            assert revision.prev_determiner_name == external["determiner_name"]
            assert revision.prev_determination_date.isoformat() == external["determination_date"]
            journal = db.query(ScientificCorrection).filter_by(specimen_id=specimen_id).one()
            assert journal.old_values == {"verbatim_label": label}
            assert journal.new_values == {"verbatim_label": None}

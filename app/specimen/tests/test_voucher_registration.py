from app.field_loc.models import FieldLoc
from app.specimen.models import Revision, ScientificCorrection, Specimen
from app.tests import TestClass, TestingSessionLocal, client
from app.tests.test_record_pages import signed_in
from app.users.services import UserServices, signJWT


class TestVoucherRegistration(TestClass):
    def test_register_collection_event_and_reuse_its_site(self):
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        headers = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        register = "/api/specimen/create-new-specimen"
        site = {"country": "Ecuador", "region": "Pichincha", "locality": "River bank",
                "gps_lat": 0, "gps_long": -78.4, "coordinate_uncertainty_m": 0, "altitude": 2150,
                "geodetic_datum": "WGS84", "georeference_source": "Field notebook", "habitat": "Wet meadow"}
        event = {"holding_type": "local", "holding_institution": "EX", "collection": "Herbarium",
                 "accession": "V-1", "collector_name": "A. Vega", "collector_number": "AV 23",
                 "collection_date": "1972-05-04", "verbatim_collection_date": "4.V.1972"}
        created = client.post(register, headers=headers, json={**event, "field_location": site})
        assert created.status_code == 200, created.text
        voucher = created.json()
        assert {key: voucher[key] for key in event} == event
        site_id = voucher["field_loc_id"]
        with TestingSessionLocal() as db:
            saved = db.get(FieldLoc, site_id)
            assert {key: getattr(saved, key) for key in site} == site

        admin = signed_in("curator@example.org")
        form = admin.get("/curation/vouchers").text
        for field in ("collection_date", "verbatim_collection_date", "collector_number", "site.locality", "taxon_id"):
            assert f'name="{field}"' in form
        assert f'value="{site_id}">River bank' in form
        record = admin.get(f"/researcher/specimens/{voucher['specimen_id']}").text
        for value in ("4.V.1972", "1972-05-04", "AV 23", "River bank", "Field notebook", "± 0 m"):
            assert value in record

        duplicate = client.post(register, headers=headers, json={**event, "field_location": {**site, "locality": "Hill"}})
        assert duplicate.status_code == 409, duplicate.text
        both = client.post(register, headers=headers, json={"holding_type": "local", "field_loc_id": site_id, "field_location": site})
        assert both.status_code == 422, both.text
        later = client.post(register, headers=headers, json={"holding_type": "local", "field_loc_id": site_id,
                                                            "verbatim_collection_date": "May 1972"})
        assert later.status_code == 200, later.text
        assert later.json()["field_loc_id"] == site_id
        assert later.json()["collection_date"] is None and later.json()["verbatim_collection_date"] == "May 1972"
        with TestingSessionLocal() as db:
            assert db.query(FieldLoc).count() == 1

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
            "vouchers": [{"specimen_id": specimen_id, "role": "collected_alongside"}],
            "code": "Voucher sample", "plant_part": "leaf", "material_state": "fresh",
            "collection_notes": "Synthetic",
        })
        assert sample.status_code == 201, sample.text
        voucher = client.get(study_url, headers=headers).json()["samples"][0]["vouchers"][0]
        assert voucher["accession"] == external["accession"]

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

    def test_update_clears_optional_fields_only_when_asked(self):
        curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        headers = {"Authorization": "Bearer " + signJWT(curator.user_id, "super_user")["access_token"]}
        register, change = "/api/specimen/create-new-specimen", "/api/specimen/update-specimen"
        site = {"country": "Serbia", "region": "Zlatibor", "locality": "Tornik", "gps_lat": 43.7, "gps_long": 19.7,
                "coordinate_uncertainty_m": 50, "altitude": 1400, "geodetic_datum": "WGS84"}
        first = client.post(register, headers=headers, json={
            "holding_type": "local", "reg_no": "L-1", "subnomen": "Achillea millefolium",
            "collection_date": "1972-05-01", "verbatim_collection_date": "1.V.1972", "field_location": site,
        }).json()
        site_id = first["field_loc_id"]
        second = client.post(register, headers=headers, json={"holding_type": "local", "field_loc_id": site_id}).json()
        first_id, second_id = ({"specimen_id": voucher["specimen_id"]} for voucher in (first, second))

        assert client.put(change, params=first_id, headers=headers,
                          json={"collection_date": None}).status_code == 400
        corrected = client.put(change, params=first_id, headers=headers, json={
            "collection_date": None, "verbatim_collection_date": "May 1972",
            "correction_reason": "The label gives only the month",
        })
        assert corrected.status_code == 200, corrected.text
        corrected = corrected.json()
        assert corrected["collection_date"] is None and corrected["verbatim_collection_date"] == "May 1972"
        assert corrected["field_loc_id"] == site_id and corrected["reg_no"] == "L-1"
        with TestingSessionLocal() as db:
            journal = db.query(ScientificCorrection).filter_by(specimen_id=first["specimen_id"]).one()
            assert journal.old_values == {"collection_date": "1972-05-01", "verbatim_collection_date": "1.V.1972"}
            assert journal.new_values == {"collection_date": None, "verbatim_collection_date": "May 1972"}

        cleared = client.put(change, params=second_id, headers=headers,
                             json={"field_loc_id": "", "correction_reason": "Site assigned in error"})
        assert cleared.status_code == 200 and cleared.json()["field_loc_id"] is None

        for field in ("reg_no", "subnomen", "taxon_id"):
            refused = client.put(change, params=first_id, headers=headers,
                                 json={field: None, "correction_reason": "Clear it"})
            assert refused.status_code == 400, (field, refused.text)

        study = client.post("/api/chemistry/studies", headers=headers, json={"title": "Site study"}).json()
        sample = client.post(f"/api/chemistry/studies/{study['id']}/samples", headers=headers, json={
            "vouchers": [{"specimen_id": first["specimen_id"], "role": "sampled_from_voucher"}],
            "site_specimen_id": first["specimen_id"], "code": "S1", "plant_part": "leaf", "material_state": "fresh",
        })
        assert sample.status_code == 201, sample.text
        guarded = client.put(change, params=first_id, headers=headers,
                             json={"field_loc_id": None, "correction_reason": "Wrong site"})
        assert guarded.status_code == 409, guarded.text
        with TestingSessionLocal() as db:
            assert db.get(Specimen, first["specimen_id"]).field_loc_id == site_id

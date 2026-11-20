from pathlib import Path

from app.chemistry.models import SampleVoucher
from app.config import settings
from app.specimen.repository import SpecimenRepository
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices, signJWT

BASE = "/api/chemistry"
CSV = b"feature,value,confidence\r\nA,60,annotated\r\nB,40,annotated\r\n"


def headers_for(user):
    role = "super_user" if user.is_superuser else "classic_user"
    return {"Authorization": "Bearer " + signJWT(user.user_id, role)["access_token"]}


def vouchers(count):
    """The first voucher has the fixture's field location; the others have none."""
    template = SpecimenFixtures.create_test_specimen_object()
    with TestingSessionLocal() as db:
        repository = SpecimenRepository(db)
        created = [repository.create_specimen(template.model_copy(update={
            "reg_no": f"V-{index}", "field_loc_id": template.field_loc_id if index == 0 else None,
        })) for index in range(count)]
        return [specimen.specimen_id for specimen in created], template.field_loc_id


def sample_payload(links, **extra):
    return {"code": "S-1", "plant_part": "aerial parts", "material_state": "air-dried",
            "vouchers": [{"specimen_id": specimen_id, "role": role} for specimen_id, role in links], **extra}


def release_voucher(curator, specimen_id, released=True, location="region"):
    response = client.put(f"/api/specimen/{specimen_id}/visibility", headers=curator,
                          json={"is_public": released, "public_location": location})
    assert response.status_code == 200, response.text


class TestSampleVouchers(TestClass):
    def setup_people(self):
        owner = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
        admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        return headers_for(owner), headers_for(admin)

    def add_profile(self, owner, curator, sample_id, release=True):
        preparation = client.post(f"{BASE}/samples/{sample_id}/preparations", headers=owner, json={
            "batch_code": "B-1", "kind": "essential_oil", "method_reference": "Hydrodistillation, 3 h"})
        assert preparation.status_code == 201, preparation.text
        profile = client.post(f"{BASE}/preparations/{preparation.json()['id']}/profiles", headers=owner,
                              data={"run_code": "R-1", "analytical_method": "GC-MS",
                                    "measurement_basis": "peak_area_percent", "unit": "%"},
                              files={"file": ("results.csv", CSV, "text/csv")})
        assert profile.status_code == 201, profile.text
        if release:
            assert client.put(f"{BASE}/profiles/{profile.json()['id']}/visibility", headers=curator,
                              json={"is_public": True}).status_code == 200
        return profile.json()["id"]

    def create_study(self, owner, curator=None):
        study = client.post(f"{BASE}/studies", headers=owner, json={"title": "Population study"})
        assert study.status_code == 201, study.text
        if curator:
            assert client.put(f"{BASE}/studies/{study.json()['id']}/visibility", headers=curator,
                              json={"is_public": True}).status_code == 200
        return f"{BASE}/studies/{study.json()['id']}"

    def test_sample_validation(self):
        owner, _ = self.setup_people()
        (first, second), field_loc_id = vouchers(2)
        study_url = self.create_study(owner)
        samples = study_url + "/samples"
        both = [(first, "sampled_from_voucher"), (second, "same_population")]
        invalid = [
            sample_payload([]),
            sample_payload([(first, "sampled_from_voucher"), (first, "same_population")]),
            sample_payload([(first, "sampled_from_voucher")], site_specimen_id=second),
            sample_payload(both, site_specimen_id=first, field_loc_id=field_loc_id),
            sample_payload(both, plant_part="other"),
            sample_payload(both, plant_part="needles"),
            sample_payload(both, material_state="dried"),
            sample_payload([(first, "sampled_nearby")]),
            {**sample_payload(both), "specimen_id": first, "voucher_relationship": "collected_alongside"},
        ]
        for payload in invalid:
            assert client.post(samples, headers=owner, json=payload).status_code == 422, payload
        missing = client.post(samples, headers=owner, json=sample_payload([(first, "sampled_from_voucher"),
                                                                           ("no-such-voucher", "same_population")]))
        assert missing.status_code == 404 and "no-such-voucher" in missing.json()["detail"]
        assert client.post(samples, headers=owner, json=sample_payload(
            both, field_loc_id="no-such-location")).status_code == 404
        created = client.post(samples, headers=owner, json=sample_payload(
            [(second, "same_population"), (first, "sampled_from_voucher")], plant_part="other",
            plant_part_note="Needles and twigs", collection_date="2024-06-12", phenological_stage="Full flowering",
            site_specimen_id=first, drying_notes="Shade, 10 days", storage_notes="Paper bags, 4 °C",
            collection_notes="Behind the hut"))
        assert created.status_code == 201, created.text

        sample = client.get(study_url, headers=owner).json()["samples"][0]
        assert [(link["specimen_id"], link["role"]) for link in sample["vouchers"]] == [
            (first, "sampled_from_voucher"), (second, "same_population")]
        assert sample["vouchers"][0]["determination_at_link"] == {
            "taxon_id": sample["vouchers"][0]["current_determination"]["taxon_id"], "taxon_name": "Acer rubrum",
            "name_as_recorded": "Achillea atrata", "date": None, "recorded": "at_link"}
        assert sample["redetermined"] is False
        assert (sample["plant_part"], sample["plant_part_note"], sample["collection_notes"]) == (
            "other", "Needles and twigs", "Behind the hut")
        assert sample["site_specimen_id"] == first and sample["collection_date"] == "2024-06-12"
        assert client.post(samples, headers=owner, json=sample_payload(both)).status_code == 409

    def test_release_rule_site_and_redetermination(self):
        owner, curator = self.setup_people()
        (first, second), _ = vouchers(2)
        study_url = self.create_study(owner, curator)
        sample = client.post(study_url + "/samples", headers=owner, json=sample_payload(
            [(first, "sampled_from_voucher"), (second, "same_population")], site_specimen_id=first,
            collection_notes="Private notes"))
        assert sample.status_code == 201, sample.text
        profile_id = self.add_profile(owner, curator, sample.json()["id"])
        public = f"{BASE}/public/profiles/{profile_id}"

        release_voucher(curator, first)
        assert client.get(public).status_code == 404
        assert client.get(f"{BASE}/public/specimens/{first}/profiles").json() == []
        release_voucher(curator, second)
        released = client.get(public)
        assert released.status_code == 200, released.text
        body = released.json()
        assert [(link["specimen_id"], link["role"]) for link in body["vouchers"]] == [
            (first, "sampled_from_voucher"), (second, "same_population")]
        assert body["site"] == {"source": "voucher", "specimen_id": first,
                                "location": {"region": "Nis", "country": "Serbia"}}
        assert body["material_state"] == "air-dried" and "Private notes" not in released.text
        assert "collection_notes" not in body and "field_loc_id" not in body
        for specimen_id in (first, second):
            assert [row["id"] for row in client.get(f"{BASE}/public/specimens/{specimen_id}/profiles").json()] == [
                profile_id]

        release_voucher(curator, first, location="withheld")
        assert client.get(public).json()["site"]["location"] is None
        release_voucher(curator, second, released=False)
        assert client.get(public).status_code == 404
        assert client.get(f"{BASE}/public/specimens/{first}/profiles").json() == []
        release_voucher(curator, second)

        revised = client.put("/api/specimen/update-specimen", headers=curator, params={"specimen_id": second},
                             json={"subnomen": "Achillea clavennae"})
        assert revised.status_code == 200, revised.text
        study = client.get(study_url, headers=owner).json()
        links = study["samples"][0]["vouchers"]
        assert [link["redetermined"] for link in links] == [False, True]
        assert links[1]["determination_at_link"]["name_as_recorded"] == "Achillea atrata"
        assert links[1]["current_determination"]["name_as_recorded"] == "Achillea clavennae"
        assert study["samples"][0]["redetermined"] and study["profiles"][0]["redetermined"]
        public_links = client.get(public).json()["vouchers"]
        assert [link["redetermined"] for link in public_links] == [False, True]
        assert public_links[1]["determination_at_link"]["name_as_recorded"] == "Achillea atrata"
        assert client.get(f"{BASE}/public/studies/{study_url.rsplit('/', 1)[1]}").json()["profiles"][0]["redetermined"]

    def test_own_field_location_is_withheld(self):
        owner, curator = self.setup_people()
        (first,), field_loc_id = vouchers(1)
        study_url = self.create_study(owner, curator)
        sample = client.post(study_url + "/samples", headers=owner, json=sample_payload(
            [(first, "collected_alongside")], field_loc_id=field_loc_id))
        assert sample.status_code == 201, sample.text
        profile_id = self.add_profile(owner, curator, sample.json()["id"])
        release_voucher(curator, first)
        assert client.get(f"{BASE}/public/profiles/{profile_id}").json()["site"] == {
            "source": "field_location", "location": None}

    def test_adding_and_removing_vouchers(self):
        owner, curator = self.setup_people()
        (first, second, third), _ = vouchers(3)
        other = headers_for(UserServices.create_user("Other", "User", "other@example.org", "password"))
        study_url = self.create_study(owner, curator)
        sample_id = client.post(study_url + "/samples", headers=owner, json=sample_payload(
            [(first, "sampled_from_voucher")], site_specimen_id=first)).json()["id"]
        links = f"{BASE}/samples/{sample_id}/vouchers"

        assert client.delete(f"{links}/{first}", headers=owner).status_code == 409
        assert client.post(links, headers=other, json={"specimen_id": second, "role": "same_population"}).status_code == 404
        assert client.post(links, headers=owner, json={"specimen_id": "missing", "role": "same_population"}).status_code == 404
        added = client.post(links, headers=owner, json={"specimen_id": second, "role": "same_population"})
        assert added.status_code == 201, added.text
        assert added.json()["determination_at_link"]["recorded"] == "at_link"
        assert client.post(links, headers=owner, json={"specimen_id": second, "role": "same_individual"}).status_code == 409
        assert client.post(links, headers=owner, json={"specimen_id": third, "role": "cultivated_from"}).status_code == 201
        assert client.delete(f"{links}/{first}", headers=owner).status_code == 409  # gives the collection site
        assert client.delete(f"{links}/missing", headers=owner).status_code == 404

        profile_id = self.add_profile(owner, curator, sample_id)
        assert client.delete(f"{links}/{third}", headers=owner).status_code == 409  # released profile
        assert client.put(f"{BASE}/profiles/{profile_id}/visibility", headers=curator,
                          json={"is_public": False}).status_code == 200
        assert client.delete(f"{links}/{third}", headers=other).status_code == 404
        assert client.delete(f"{links}/{third}", headers=owner).status_code == 204
        with TestingSessionLocal() as db:
            assert {link.specimen_id for link in db.query(SampleVoucher).filter_by(sample_id=sample_id)} == {
                first, second}

    def test_deposition_lists_every_linked_voucher(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://herbar.example.edu")
        owner, curator = self.setup_people()
        (first, second), _ = vouchers(2)
        assert client.post("/api/institutions", headers=curator,
                           json={"code": "EXU", "name": "Example University"}).status_code == 201
        study_url = self.create_study(owner, curator)
        sample_id = client.post(study_url + "/samples", headers=owner, json=sample_payload(
            [(first, "sampled_from_voucher"), (second, "same_population")], site_specimen_id=first)).json()["id"]
        profile_id = self.add_profile(owner, curator, sample_id)
        for specimen_id in (first, second):
            release_voucher(curator, specimen_id)
        created = client.post("/api/depositions", headers=owner, json={
            "institution": "EXU", "title": "Two vouchers", "license": "CC BY 4.0",
            "contributors": [{"name": "F. Scientist", "role": "analyst"}], "profile_ids": [profile_id]})
        assert created.status_code == 201, created.text
        path = f"/api/depositions/{created.json()['id']}"
        preview = client.get(f"{path}/draft/preview", headers=curator)
        assert preview.status_code == 200, preview.text
        snapshot = preview.json()["snapshot"]
        assert snapshot["schema_version"] == 3
        assert sorted(voucher["id"] for voucher in snapshot["vouchers"]) == sorted([first, second])
        sample = snapshot["profiles"][0]["sample"]
        assert [(link["id"], link["role"]) for link in sample["vouchers"]] == [
            (first, "sampled_from_voucher"), (second, "same_population")]
        assert sample["site"]["location"] == {"region": "Nis", "country": "Serbia"}
        assert "voucher" not in snapshot["profiles"][0]

        approval = {key: preview.json()[key] for key in ("draft_revision", "snapshot_sha256")}
        published = client.post(f"{path}/publish", headers=curator, json=approval)
        assert published.status_code == 200, published.text
        page = client.get(snapshot["identifier"].removeprefix("https://herbar.example.edu"))
        assert page.status_code == 200, page.text
        assert "Sampled from the voucher" in page.text and "Same population as the voucher" in page.text
        assert client.get(snapshot["url"].removeprefix("https://herbar.example.edu") + "/archive.zip").status_code == 200
        assert list(Path("files").glob("*.csv"))

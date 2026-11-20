import pytest
from fastapi.encoders import jsonable_encoder

from app.chemistry.models import LabSample
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import TestClass, TestingSessionLocal, client
from app.users.services import UserServices, signJWT


def headers_for(user):
    role = "super_user" if user.is_superuser else "classic_user"
    return {"Authorization": "Bearer " + signJWT(user.user_id, role)["access_token"]}


class TestChemistry(TestClass):
    def test_specimen_can_be_registered_without_a_chemical_profile(self):
        specimen_data = SpecimenFixtures.create_test_specimen_object()
        admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        created = client.post(
            "/api/specimen/create-new-specimen",
            json=jsonable_encoder(specimen_data),
            headers=headers_for(admin),
        )
        assert created.status_code == 200, created.text
        specimen_id = created.json()["specimen_id"]
        assert client.get(f"/api/specimen/{specimen_id}").status_code == 404
        assert client.put(f"/api/specimen/{specimen_id}/visibility", headers=headers_for(admin),
                          json={"is_public": True, "public_location": "withheld"}).status_code == 200
        assert client.get(f"/api/specimen/{specimen_id}").status_code == 200

        profiles = client.get(f"/api/chemistry/public/specimens/{specimen_id}/profiles")
        assert profiles.status_code == 200, profiles.text
        assert profiles.json() == []
        with TestingSessionLocal() as db:
            assert db.query(LabSample).filter_by(specimen_id=specimen_id).count() == 0

    def test_drafts_release_and_reproducible_pca(self):
        specimen = SpecimenFixtures.create_test_specimen()
        actor = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
        other = UserServices.create_user("Other", "User", "other@example.org", "password")
        admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        owner, outsider, curator = map(headers_for, (actor, other, admin))
        base = "/api/chemistry"
        assert client.get(base + "/studies").status_code == 403
        assert client.get(base + "/studies", headers=owner).json() == {
            "can_publish": False, "studies": [],
        }
        study = client.post(base + "/studies", json={"title": "Field samples"}, headers=owner)
        assert study.status_code == 201, study.text
        study_id = study.json()["id"]
        study_url = f"{base}/studies/{study_id}"
        assert client.get(study_url, headers=outsider).status_code == 404
        public_study = f"{base}/public/studies/{study_id}"
        assert client.get(public_study).status_code == 404

        profiles = []
        for index, values in enumerate(((20, 35, 45), (25, 35, 40), (10, 45, 45))):
            sample = client.post(study_url + "/samples", headers=owner, json={
                "specimen_id": specimen.specimen_id, "code": f"sample-{index}",
                "plant_part": "leaf", "collection_event": f"collection-{index}",
                "voucher_relationship": "collected_alongside",
            })
            assert sample.status_code == 201, sample.text
            sample_id = sample.json()["id"]
            preparation = client.post(f"{base}/samples/{sample_id}/preparations", headers=owner, json={
                "batch_code": f"batch-{index}", "kind": "essential_oil", "method_reference": "REF-1",
            })
            assert preparation.status_code == 201, preparation.text
            preparation_id = preparation.json()["id"]
            csv = "feature,value,confidence\n" + "\n".join(
                f"{feature},{value},annotated" for feature, value in zip("ABC", values)
            )
            profile = client.post(f"{base}/preparations/{preparation_id}/profiles", headers=owner,
                                  data={"run_code": f"run-{index}", "analytical_method": "GC-MS-1",
                                        "measurement_basis": "peak_area_percent", "unit": "%"},
                                  files={"file": ("source.csv", csv, "text/csv")})
            assert profile.status_code == 201, profile.text
            profiles.append(profile.json()["id"])

        first = profiles[0]
        public_profile = f"{base}/public/profiles/{first}"
        voucher_profiles = f"{base}/public/specimens/{specimen.specimen_id}/profiles"
        assert client.get(public_profile).status_code == 404
        assert client.get(voucher_profiles).status_code == 404
        assert client.get(f"{base}/profiles/{first}/source", headers=outsider).status_code == 404
        assert client.get(f"{base}/profiles/{first}/source", headers=owner).text.startswith("feature,value")
        visibility = f"{base}/profiles/{first}/visibility"
        assert client.put(visibility, json={"is_public": True}, headers=owner).status_code == 403
        assert client.put(visibility, json={"is_public": True}, headers=curator).status_code == 200
        assert client.get(public_profile).status_code == 404
        assert client.put(study_url + "/visibility", json={"is_public": True}, headers=curator).status_code == 200
        assert client.get(public_profile).status_code == 404
        assert client.get(public_study).status_code == 404
        voucher_visibility = f"/api/specimen/{specimen.specimen_id}/visibility"
        voucher_state = {"is_public": True, "public_location": "region"}
        assert client.put(voucher_visibility, json=voucher_state, headers=curator).status_code == 200
        released = client.get(public_profile)
        assert released.status_code == 200, released.text
        assert released.json()["specimen_id"] == specimen.specimen_id
        assert [row["value"] for row in released.json()["measurements"]] == [20, 35, 45]
        assert "source_name" not in released.json()
        assert "collection_event" not in released.json()
        assert [row["id"] for row in client.get(voucher_profiles).json()] == [first]
        assert [row["id"] for row in client.get(public_study).json()["profiles"]] == [first]
        assert client.get(f"{base}/public/profiles/{profiles[1]}").status_code == 404

        request = {"profile_ids": profiles}
        result = client.post(study_url + "/pca", json=request, headers=owner)
        assert result.status_code == 201, result.text
        analysis = result.json()
        assert analysis["configuration"]["transform"] == "centered_log_ratio"
        assert analysis["profile_ids"] == profiles
        assert sum(analysis["explained_variance"]) == pytest.approx(100)
        saved = client.get(study_url + "/pca/" + analysis["id"], headers=owner)
        assert saved.json() == analysis
        assert client.put(study_url + "/visibility", json={"is_public": False}, headers=curator).status_code == 200
        assert client.get(public_profile).status_code == 404
        assert client.get(voucher_profiles).json() == []
        assert client.put(study_url + "/visibility", json={"is_public": True}, headers=curator).status_code == 200
        voucher_state["is_public"] = False
        assert client.put(voucher_visibility, json=voucher_state, headers=curator).status_code == 200
        assert client.get(voucher_profiles).status_code == 404
        assert client.get(public_study).status_code == 404
        assert client.get(public_profile).status_code == 404
        assert client.get(f"{base}/profiles/{first}/source", headers=owner).status_code == 200

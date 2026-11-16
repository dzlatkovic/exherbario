from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from fastapi_pagination import Params
from PIL import Image as JPEG
from pydantic import ValidationError

from app.field_loc.models import FieldLoc
from app.field_loc.schemas import FieldLocSchemaIn
from app.image.models import Image
from app.image.schemas import ImageType
from app.image.services import ImageService
from app.specimen.exceptions import SpecimenInUseException
from app.specimen.models import Revision
from app.specimen.repository import SpecimenRepository
from app.specimen.schemas import SpecimenSchemaIn, SpecimenSchemaUpdate
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.taxonomy.models import Taxonomy
from app.taxonomy.services import TaxonomyService
from app.tests import TestClass, TestingSessionLocal, client
from app.users.repository import UserRepository
from app.users.services import UserServices


class TestArchiveRegressions(TestClass):
    def test_reidentification_records_previous_values_and_prevents_deletion(self):
        specimen = SpecimenFixtures.create_test_specimen()
        with TestingSessionLocal() as db:
            repo = SpecimenRepository(db)
            updated = repo.update_specimen(
                specimen.specimen_id, SpecimenSchemaUpdate(subnomen="Revised name"),
                revised_by=specimen.verified_by,
            )
            revision = db.query(Revision).one()
            assert updated.subnomen == "Revised name"
            assert revision.prev_subnomen == specimen.subnomen
            assert revision.prev_taxon_id == specimen.taxon_id
            assert revision.revised_by == specimen.verified_by

            with pytest.raises(SpecimenInUseException):
                repo.delete_specimen(specimen.specimen_id)
            assert repo.read_specimen_by_id(specimen.specimen_id).subnomen == "Revised name"

    def test_taxonomy_uses_parent_chain_and_rolls_back_on_write_failure(self, monkeypatch):
        ranks = ("KINGDOM", "PHYLUM", "CLASS", "ORDER")

        def fetch(*, key, timeout):
            index = int(key) - 1
            data = {"key": index + 1, "rank": ranks[index], "scientificName": ranks[index]}
            if index:
                data["parentKey"] = index
            return data

        monkeypatch.setattr("app.taxonomy.services.taxonomy_services.species.name_usage", fetch)
        add_taxon = TaxonomyService._add_taxon

        def fail_on_class(repository, data, rank, parent_id):
            if data["rank"] == "CLASS":
                raise RuntimeError("interrupted import")
            return add_taxon(repository, data, rank, parent_id)

        with monkeypatch.context() as patch:
            patch.setattr(TaxonomyService, "_add_taxon", staticmethod(fail_on_class))
            with pytest.raises(RuntimeError, match="interrupted import"):
                TaxonomyService.build_taxonomic_tree("4")
        with TestingSessionLocal() as db:
            assert db.query(Taxonomy).count() == 0

        taxa = TaxonomyService.build_taxonomic_tree("4")
        assert [taxon.taxon_rank.name for taxon in taxa] == list(ranks)
        assert [taxon.parent_taxon_key for taxon in taxa] == [
            None, *(taxon.taxon_id for taxon in taxa[:-1]),
        ]
        assert TaxonomyService.build_taxonomic_tree("4") == []

        specimen_input = SpecimenFixtures.create_test_specimen_object()
        with TestingSessionLocal() as db:
            specimen = SpecimenRepository(db).create_specimen(
                specimen_input.copy(update={"taxon_id": taxa[-1].taxon_id})
            )
        assert [row.specimen_id for row in TaxonomyService.get_specimens_by_taxon("KINGDOM")] == [
            specimen.specimen_id
        ]

    def test_search_page_and_zero_coordinate(self):
        specimen_input = SpecimenFixtures.create_test_specimen_object()
        with TestingSessionLocal() as db:
            repo = SpecimenRepository(db)
            for reg_no in ("2", "1"):
                repo.create_specimen(specimen_input.copy(update={"reg_no": reg_no}))
            page = repo.search_specimens_by_keyword("Achillea", Params(page=2, size=1))
            assert page.total == 2
            assert [row.reg_no for row in page.items] == ["2"]

            location = db.get(FieldLoc, specimen_input.field_loc_id)
            location.gps_lat = 0
            db.commit()
            assert all(row["distance"] > 0 for row in repo.get_specimens_by_distance("Achillea"))

    def test_invalid_dates_and_coordinates_are_rejected(self):
        specimen = SpecimenFixtures.create_test_specimen_object()
        assert isinstance(specimen.collection_date, date)
        with pytest.raises(ValidationError):
            SpecimenSchemaIn(**dict(specimen.dict(), collection_date="invalid"))
        with pytest.raises(ValidationError):
            FieldLocSchemaIn(country="Serbia", region="Nis", locality="Nis", gps_lat=91)

    def test_images_use_distinct_keys_and_rollback_when_disk_write_fails(self, tmp_path, monkeypatch):
        specimen = SpecimenFixtures.create_test_specimen()
        monkeypatch.chdir(tmp_path)
        root = tmp_path / "images"
        jpeg = BytesIO()
        JPEG.new("RGB", (2, 2)).save(jpeg, "JPEG")

        def upload():
            return ImageService.create_image(
                specimen.specimen_id, ImageType.field,
                UploadFile(filename="same.jpg", file=BytesIO(jpeg.getvalue())),
            )

        first, second = upload(), upload()
        assert first.file_path != second.file_path
        assert all(Path(record.file_path).resolve().parent == root for record in (first, second))

        open_path = Path.open

        def unavailable(path, mode="r", *args, **kwargs):
            if mode == "xb" and path.parent == root:
                raise OSError("disk unavailable")
            return open_path(path, mode, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(Path, "open", unavailable)
            with pytest.raises(OSError, match="disk unavailable"):
                upload()
        with TestingSessionLocal() as db:
            assert db.query(Image).count() == 2

        ImageService.delete_image(str(first.image_id))
        assert not Path(first.file_path).exists()
        assert Path(second.file_path).is_file()

    def test_legacy_password_is_upgraded_after_login(self):
        password = "previous password"
        legacy_hash = sha256(password.encode()).hexdigest()
        with TestingSessionLocal() as db:
            user = UserRepository(db).create_user("Sample", "User", "sample@example.org", legacy_hash)

        verified = UserServices.login_user(user.email, password)
        assert verified.password.startswith("pbkdf2-sha256$")
        assert UserServices.login_user(user.email, password).password == verified.password

    def test_revision_and_search_routes_use_the_updated_identification(self):
        specimen = SpecimenFixtures.create_test_specimen()
        admin = UserServices.create_super_user("Sample", "Admin", "admin@example.org", "password")
        token = client.post(
            "/api/users/login", json={"email": admin.email, "password": "password"},
        ).json()["access_token"]
        response = client.post(
            "/api/revision/create-revision",
            json={"specimen_id": specimen.specimen_id, "taxon_id": specimen.taxon_id,
                  "subnomen": "Revised name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["revised_by"] == admin.user_id
        assert response.json()["prev_subnomen"] == specimen.subnomen

        response = client.get(
            "/api/specimen/search-specimens-by-keyword", params={"keyword": "Revised", "size": 1},
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["specimen_id"] == specimen.specimen_id

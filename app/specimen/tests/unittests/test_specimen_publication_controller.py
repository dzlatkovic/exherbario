import pytest
from fastapi import HTTPException

from app.photos.repository import PhotosRepository
from app.specimen.models import SpecimenPublication
from app.tests import TestClass, TestingSessionLocal
from app.specimen.repository import SpecimenRepository
from app.specimen.controller import SpecimenPublicationController
from app.publication.repository import PublicationRepository
from app.field_loc.repository import FieldLocRepository
from app.storage.repository import StorageRepository
from app.users.repository import UserRepository


class TestSpecimenPublicationController(TestClass):

    def create_test_specimen_publication(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            specimen_repository = SpecimenRepository(db)
            field_loc_repository = FieldLocRepository(db)
            users_repository = UserRepository(db)
            storage_repository = StorageRepository(db)
            photos_repository = PhotosRepository(db)
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine", "COVID-19 Treatment")
            field_loc = field_loc_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                              1400, "woods", 43.0, 22.0)
            storage = storage_repository.create_storage("room1", "shelf1", "box1")
            user = users_repository.create_user("John", "Smith", "john@example.com", "password")
            photos = photos_repository.create_photos("field1.jpg", "specimen1.jpg")
            specimen = specimen_repository.create_specimen("100",
                                                           "2010-01-01",
                                                           "2010-01-01",
                                                           "Asteraceae",
                                                           "Achillea",
                                                           "atrata",
                                                           "Achillea atrata",
                                                           field_loc.field_loc_id,
                                                           storage.storage_id,
                                                           photos.photos_id,
                                                           user.user_id,
                                                           user.user_id)
            sp = SpecimenPublicationController.create_new_specimen_publication(specimen.specimen_id,
                                                                            pub.pub_id)
            return sp

    def test_create_specimen_publication(self):
        sp = self.create_test_specimen_publication()
        assert isinstance(sp, SpecimenPublication)

    def test_delete_specimen_publication(self):
        sp = self.create_test_specimen_publication()
        outcome = SpecimenPublicationController.delete_specimen_publication_by_id(sp.specimen_publication_id)
        assert outcome.status_code == 200

    def test_delete_specimen_publication_invalid(self):
        self.create_test_specimen_publication()
        with pytest.raises(HTTPException) as error:
            SpecimenPublicationController.delete_specimen_publication_by_id("invalid_id")
        assert error.value.status_code == 400

    def test_create_specimen_invalid_foreign_key(self):
        with pytest.raises(HTTPException) as error:
            SpecimenPublicationController.create_new_specimen_publication("invalid path", "invalid path")
        assert error.value.status_code == 400

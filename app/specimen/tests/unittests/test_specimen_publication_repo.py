"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

import pytest

from app.photos.repository import PhotosRepository
from app.specimen.exceptions import SpecimenPublicationNotFoundException
from app.specimen.models import SpecimenPublication
from app.tests import TestClass, TestingSessionLocal
from app.specimen.repository import SpecimenRepository, SpecimenPublicationRepository
from app.publication.repository import PublicationRepository
from app.field_loc.repository import FieldLocRepository
from app.storage.repository import StorageRepository
from app.users.repository import UserRepository


class TestSpecimenPublicationRepo(TestClass):
    """# This class tests the specimen publication repository."""

    def create_test_specimen_publication(self):
        """
        It creates a specimen publication
        :return: SpecimenPublication object
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            specimen_repository = SpecimenRepository(db)
            field_loc_repository = FieldLocRepository(db)
            users_repository = UserRepository(db)
            storage_repository = StorageRepository(db)
            photos_repository = PhotosRepository(db)
            specimen_publication_repository = SpecimenPublicationRepository(db)
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine",
                                                            "COVID-19 Treatment")
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
            spec_pub = specimen_publication_repository.create_specimen_publication(
                specimen.specimen_id, pub.pub_id)
            return spec_pub

    def test_create_specimen_publication(self):
        """
        This function creates a specimen publication object
        """
        spec_pub = self.create_test_specimen_publication()
        assert isinstance(spec_pub, SpecimenPublication)

    def test_delete_specimen_publication(self):
        """
        This function tests the deletion of a specimen publication by id
        """
        spec_pub = self.create_test_specimen_publication()
        with TestingSessionLocal() as db:
            sp_repo = SpecimenPublicationRepository(db)
            outcome = sp_repo.delete_specimen_publication_by_id(spec_pub.specimen_publication_id)
        assert outcome is True

    def test_delete_specimen_publication_invalid(self):
        """
        This function tests that an exception is raised when an invalid
        specimen publication id is passed to the
        delete_specimen_publication_by_id function
        """
        self.create_test_specimen_publication()
        with TestingSessionLocal() as db:
            sp_repo = SpecimenPublicationRepository(db)
            with pytest.raises(SpecimenPublicationNotFoundException):
                sp_repo.delete_specimen_publication_by_id("invalid_id")

    def test_create_specimen_invalid_foreign_key(self):
        """
        `test_create_specimen_invalid_foreign_key` tests that a `ValueError`
        is raised when a `SpecimenPublication` is
        created with invalid foreign keys
        """
        with TestingSessionLocal() as db:
            spr = SpecimenPublicationRepository(db)
            with pytest.raises(ValueError) as error:
                spr.create_specimen_publication("invalid path", "invalid path")
            assert "not a valid foreign key" in str(error)

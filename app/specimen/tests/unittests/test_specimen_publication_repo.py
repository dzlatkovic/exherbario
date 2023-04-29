"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

import pytest

from app.specimen.exceptions import SpecimenPublicationNotFoundException
from app.specimen.models import SpecimenPublication
from app.tests import TestClass, TestingSessionLocal
from app.specimen.repository import SpecimenPublicationRepository
from app.publication.repository import PublicationRepository


class TestSpecimenPublicationRepo(TestClass):
    """# This class tests the specimen publication repository."""

    @staticmethod
    def create_test_publication():
        """
        It creates a specimen publication
        :return: SpecimenPublication object
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            return publication_repository.create_publication("1234", "2020",
                                                             "Journal of Medicine",
                                                             "COVID-19 Treatment",
                                                             "Sample text")

    @staticmethod
    def create_test_specimen_publication():
        from app.specimen.tests import TestSpecimenRepo
        with TestingSessionLocal() as db:
            specimen_publication_repository = SpecimenPublicationRepository(db)
            specimen = TestSpecimenRepo.create_test_specimen()
            publication = TestSpecimenPublicationRepo.create_test_publication()
            return specimen_publication_repository.create_specimen_publication(
                specimen.specimen_id, publication.pub_id)

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

"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

import pytest

from app.specimen.exceptions import SpecimenPublicationNotFoundException
from app.specimen.models import SpecimenPublication
from app.tests import TestClass
from app.specimen.services import SpecimenPublicationService


class TestSpecimenPublicationService(TestClass):
    """This class tests the specimen publication service"""

    def create_test_specimen_publication(self):
        """
        It creates a new specimen publication
        :return: The specimen_publication_id
        """
        from app.specimen.tests import TestSpecimenRepo, TestSpecimenPublicationRepo
        specimen = TestSpecimenRepo.create_test_specimen()
        publication = TestSpecimenPublicationRepo.create_test_publication()
        spec_pub = SpecimenPublicationService.create_new_specimen_publication(
                specimen.specimen_id,
                publication.pub_id)
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
        outcome = SpecimenPublicationService.delete_specimen_publication_by_id(
            spec_pub.specimen_publication_id)
        assert outcome is True

    def test_delete_specimen_publication_invalid(self):
        """
        It tests the delete_specimen_publication_by_id function in the
        SpecimenPublicationService class.
        """
        self.create_test_specimen_publication()
        with pytest.raises(SpecimenPublicationNotFoundException):
            SpecimenPublicationService.delete_specimen_publication_by_id("invalid_id")

    def test_create_specimen_invalid_foreign_key(self):
        """
        This function tests the create_new_specimen_publication function
        in the SpecimenPublicationService class
        """
        with pytest.raises(ValueError) as error:
            SpecimenPublicationService.create_new_specimen_publication("invalid path",
                                                                       "invalid path")
        assert "not a valid foreign key" in str(error)

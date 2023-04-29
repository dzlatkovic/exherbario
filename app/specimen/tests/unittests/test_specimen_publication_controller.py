"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

import pytest
from fastapi import HTTPException

from app.specimen.models import SpecimenPublication
from app.tests import TestClass
from app.specimen.controller import SpecimenPublicationController


class TestSpecimenPublicationController(TestClass):
    """This class tests the specimen publication controller."""

    def create_test_specimen_publication(self):
        """
        It creates a new specimen publication
        :return: SpecimenPublication object
        """
        from app.specimen.tests import TestSpecimenRepo, TestSpecimenPublicationRepo
        specimen = TestSpecimenRepo.create_test_specimen()
        publication = TestSpecimenPublicationRepo.create_test_publication()
        spec_pub = SpecimenPublicationController.create_new_specimen_publication(
                specimen.specimen_id, publication.pub_id)
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
        outcome = SpecimenPublicationController.delete_specimen_publication_by_id(
            spec_pub.specimen_publication_id)
        assert outcome.status_code == 200

    def test_delete_specimen_publication_invalid(self):
        """
        It tests the delete_specimen_publication_by_id function in the
        SpecimenPublicationController class.
        """
        self.create_test_specimen_publication()
        with pytest.raises(HTTPException) as error:
            SpecimenPublicationController.delete_specimen_publication_by_id("invalid_id")
        assert error.value.status_code == 400

    def test_create_specimen_invalid_foreign_key(self):
        """
        This function tests the create_new_specimen_publication function in the
        SpecimenPublicationController class
        """
        with pytest.raises(HTTPException) as error:
            SpecimenPublicationController.create_new_specimen_publication("invalid path",
                                                                          "invalid path")
        assert error.value.status_code == 400

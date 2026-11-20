"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

from app.specimen.models import Specimen
from app.specimen.schemas import SpecimenSchemaUpdate
from app.tests import TestClass
from app.specimen.controller import SpecimenController


class TestSpecimenController(TestClass):
    """This class tests the specimen controller"""

    def create_test_specimen(self):
        """
        It creates a new specimen, and returns it
        :return: The specimen object is being returned.
        """
        from app.specimen.tests import TestSpecimenRepo
        specimen_object_in = TestSpecimenRepo.create_test_specimen_object()
        specimen = SpecimenController.create_new_specimen(specimen_object_in)
        return specimen

    def test_create_specimen(self):
        """
        This function creates a specimen object and returns it
        """
        specimen = self.create_test_specimen()
        assert isinstance(specimen, Specimen)

    def test_read_specimen_by_id(self):
        """
        This function tests the ability to read a specimen by its id
        """
        specimen = self.create_test_specimen()
        read_specimen = SpecimenController.get_specimen_by_id(specimen.specimen_id)
        assert read_specimen is not None
        assert read_specimen.specimen_id == specimen.specimen_id

    def test_delete_specimen(self):
        """
        This function tests the deletion of a specimen by its id
        """
        specimen = self.create_test_specimen()
        outcome = SpecimenController.delete_specimen_by_id(specimen.specimen_id)
        assert outcome.status_code == 200

    def test_get_specimens_per_year(self):
        """
        This function tests the get_specimens_per_year function in the SpecimenController class
        """
        self.create_test_specimen()
        specimens_per_year = SpecimenController.get_specimens_per_year()
        assert specimens_per_year.status_code == 200

    def test_get_specimens_per_user(self):
        """
        This function tests the get_specimens_per_user function in the SpecimenController class
        """
        self.create_test_specimen()
        specimens_per_user = SpecimenController.get_specimens_per_user()
        assert specimens_per_user.status_code == 200

    def test_get_specimens_per_region(self):
        """
        This function tests the get_specimens_per_region function in the SpecimenController class
        """
        self.create_test_specimen()
        specimens_per_region = SpecimenController.get_specimens_per_region()
        assert specimens_per_region.status_code == 200

    def test_get_gps_for_genus(self):
        """
        This function tests the get_gps_for_genus function in the SpecimenController class
        """
        self.create_test_specimen()
        gps_for_genus = SpecimenController.get_gps_for_search_result("Achillea")
        assert gps_for_genus.status_code == 200

    def test_get_last_specimens(self):
        """
        `test_get_last_specimens` tests that the `get_last_specimens`
        function returns a list of specimens
        """
        self.create_test_specimen()
        last_specimens = SpecimenController.get_last_specimens()
        assert isinstance(last_specimens, list)
        assert len(last_specimens) == 1

    def test_update_specimen(self):
        """
        It updates the species of a specimen.
        """
        specimen = self.create_test_specimen()
        updated_specimen = SpecimenController.update_specimen(
            specimen.specimen_id, SpecimenSchemaUpdate(reg_no="new_reg_no", correction_reason="Accession transcription"),
            specimen.verified_by)
        assert updated_specimen is not None
        assert updated_specimen.reg_no == "new_reg_no"

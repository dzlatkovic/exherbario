"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

from app.photos.repository import PhotosRepository
from app.specimen.models import Specimen
from app.specimen.schemas import SpecimenSchemaUpdate
from app.tests import TestClass, TestingSessionLocal
from app.specimen.controller import SpecimenController
from app.field_loc.repository import FieldLocRepository
from app.storage.repository import StorageRepository
from app.users.repository import UserRepository


class TestSpecimenController(TestClass):
    """This class tests the specimen controller"""

    def create_test_specimen_publication(self):
        """
        It creates a new specimen, and returns it
        :return: The specimen object is being returned.
        """
        with TestingSessionLocal() as db:
            field_loc_repository = FieldLocRepository(db)
            users_repository = UserRepository(db)
            storage_repository = StorageRepository(db)
            photos_repository = PhotosRepository(db)
            field_loc = field_loc_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                              1400, "woods", 43.0, 22.0)
            storage = storage_repository.create_storage("room1", "shelf1", "box1")
            user = users_repository.create_user("John", "Smith", "john@example.com", "password")
            photos = photos_repository.create_photos("field1.jpg", "specimen1.jpg")
            specimen = SpecimenController.create_new_specimen("100",
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
            return specimen

    def test_create_specimen_publication(self):
        """
        This function creates a specimen object and returns it
        """
        specimen = self.create_test_specimen_publication()
        assert isinstance(specimen, Specimen)

    def test_read_specimen_by_id(self):
        """
        This function tests the ability to read a specimen by its id
        """
        specimen = self.create_test_specimen_publication()
        read_specimen = SpecimenController.get_specimen_by_id(specimen.specimen_id)
        assert read_specimen is not None
        assert read_specimen.specimen_id == specimen.specimen_id

    def test_delete_specimen(self):
        """
        This function tests the deletion of a specimen by its id
        """
        specimen = self.create_test_specimen_publication()
        outcome = SpecimenController.delete_specimen_by_id(specimen.specimen_id)
        assert outcome.status_code == 200

    def test_get_specimens_per_year(self):
        """
        This function tests the get_specimens_per_year function in the SpecimenController class
        """
        self.create_test_specimen_publication()
        specimens_per_year = SpecimenController.get_specimens_per_year()
        assert specimens_per_year.status_code == 200

    def test_get_specimens_per_user(self):
        """
        This function tests the get_specimens_per_user function in the SpecimenController class
        """
        self.create_test_specimen_publication()
        specimens_per_user = SpecimenController.get_specimens_per_user()
        assert specimens_per_user.status_code == 200

    def test_get_specimens_per_region(self):
        """
        This function tests the get_specimens_per_region function in the SpecimenController class
        """
        self.create_test_specimen_publication()
        specimens_per_region = SpecimenController.get_specimens_per_region()
        assert specimens_per_region.status_code == 200

    def test_count_specimens(self):
        """
        This function tests the count_specimens function in the SpecimenController class
        """
        self.create_test_specimen_publication()
        count_specimens = SpecimenController.count_specimens()
        assert count_specimens.status_code == 200

    def test_get_gps_for_genus(self):
        """
        This function tests the get_gps_for_genus function in the SpecimenController class
        """
        self.create_test_specimen_publication()
        gps_for_genus = SpecimenController.get_gps_for_search_result("Achillea")
        assert gps_for_genus.status_code == 200

    def test_get_last_specimens(self):
        """
        `test_get_last_specimens` tests that the `get_last_specimens`
        function returns a list of specimens
        """
        self.create_test_specimen_publication()
        last_specimens = SpecimenController.get_last_specimens()
        assert isinstance(last_specimens, list)
        assert len(last_specimens) == 1

    def test_update_specimen(self):
        """
        It updates the species of a specimen.
        """
        specimen = self.create_test_specimen_publication()
        updated_specimen = SpecimenController.update_specimen(
            specimen.specimen_id, SpecimenSchemaUpdate(species="new_species"))
        assert updated_specimen is not None
        assert updated_specimen.species == "new_species"

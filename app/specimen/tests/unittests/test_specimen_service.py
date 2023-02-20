"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

import pytest

from app.photos.repository import PhotosRepository
from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.models import Specimen
from app.specimen.schemas import SpecimenSchemaUpdate
from app.tests import TestClass, TestingSessionLocal
from app.specimen.services import SpecimenService
from app.field_loc.repository import FieldLocRepository
from app.storage.repository import StorageRepository
from app.users.repository import UserRepository


class TestSpecimenService(TestClass):
    """This class tests the specimen service."""
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
            specimen = SpecimenService.create_new_specimen("100",
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
        This function tests the read_specimen_by_id function in the SpecimenService class
        """
        specimen = self.create_test_specimen_publication()
        read_specimen = SpecimenService.read_specimen_by_id(specimen.specimen_id)
        assert read_specimen is not None
        assert read_specimen.specimen_id == specimen.specimen_id

    def test_delete_specimen(self):
        """
        This function tests the deletion of a specimen by id
        """
        specimen = self.create_test_specimen_publication()
        result = SpecimenService.delete_specimen_by_id(specimen.specimen_id)
        assert result is True
        with pytest.raises(SpecimenNotFoundException):
            SpecimenService.read_specimen_by_id(specimen.specimen_id)

    def test_get_specimens_per_year(self):
        """
        `test_get_specimens_per_year` tests the `get_specimens_per_year`
        function in the `SpecimenService` class
        """
        self.create_test_specimen_publication()
        specimens_per_year = SpecimenService.get_specimens_per_year()
        assert isinstance(specimens_per_year, list)

    def test_get_specimens_per_user(self):
        """
        `test_get_specimens_per_user` tests the `get_specimens_per_user`
        function in the `SpecimenService` class
        """
        self.create_test_specimen_publication()
        specimens_per_user = SpecimenService.get_specimens_per_user()
        assert isinstance(specimens_per_user, dict)

    def test_get_specimens_per_region(self):
        """
        `get_specimens_per_region()` returns a dictionary of the number of specimens per region
        """
        self.create_test_specimen_publication()
        specimens_per_region = SpecimenService.get_specimens_per_region()
        assert isinstance(specimens_per_region, dict)

    def test_count_specimens(self):
        """
        This function counts the number of specimens in the database
        """
        self.create_test_specimen_publication()
        count_specimens = SpecimenService.count_specimens()
        assert isinstance(count_specimens, dict)

    def test_get_gps_for_genus(self):
        """
        This function creates a test specimen publication, then calls
        the get_gps_for_genus function, which returns a
        dictionary of GPS coordinates for a given genus
        """
        self.create_test_specimen_publication()
        gps_for_genus = SpecimenService.get_gps_for_genus("Achillea")
        assert isinstance(gps_for_genus, dict)

    def test_get_last_specimens(self):
        """
        `test_get_last_specimens` tests that the `get_last_specimens` function
        returns a list of specimens
        """
        self.create_test_specimen_publication()
        last_specimens = SpecimenService.get_last_specimens()
        assert isinstance(last_specimens, list)
        assert len(last_specimens) == 1

    def test_update_specimen(self):
        """
        It tests the "update_specimen" function.
        """
        specimen = self.create_test_specimen_publication()
        updated_specimen = SpecimenService.update_specimen(
            specimen.specimen_id,
            SpecimenSchemaUpdate(species="new_species"))
        assert updated_specimen is not None
        assert updated_specimen.species == "new_species"

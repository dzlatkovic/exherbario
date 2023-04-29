"""
This module contains unit tests for a Python project using the `pytest` testing framework.
"""

import pytest

from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.models import Specimen
from app.specimen.schemas import SpecimenSchemaUpdate, SpecimenSchemaIn
from app.taxonomy.repository import TaxonomyRepository
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank
from app.tests import TestClass, TestingSessionLocal
from app.specimen.repository import SpecimenRepository
from app.field_loc.repository import FieldLocRepository
from app.storage.repository import StorageRepository
from app.users.repository import UserRepository


class TestSpecimenRepo(TestClass):
    """This class tests the specimen repository"""

    @staticmethod
    def create_test_specimen_object():
        with TestingSessionLocal() as db:
            taxon_repository = TaxonomyRepository(db)
            field_loc_repository = FieldLocRepository(db)
            users_repository = UserRepository(db)
            storage_repository = StorageRepository(db)
            taxon_data = TaxonomySchemaIn(taxon_name="Acer rubrum",
                                          gbif_key="2871551")
            taxon = taxon_repository.create_taxon(taxon_data=taxon_data, taxon_rank=TaxonRank.KINGDOM)
            field_loc = field_loc_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                              1400, "woods", 43.0, 22.0)
            storage = storage_repository.create_storage("room1", "shelf1", "box1")
            user = users_repository.create_user("John", "Smith", "john@example.com", "password")
            specimen_object_in = SpecimenSchemaIn(reg_no="100",
                                                  collection_date="2010-01-01",
                                                  reg_date="2010-01-01",
                                                  taxon_id=taxon.taxon_id,
                                                  subnomen="Achillea atrata",
                                                  field_loc_id=field_loc.field_loc_id,
                                                  storage_id=storage.storage_id,
                                                  collected_by=user.user_id,
                                                  verified_by=user.user_id)
            return specimen_object_in

    @staticmethod
    def create_test_specimen():
        """
        It creates a specimen, a field location, a storage, a user,
        and a photos object, and then returns the specimen object
        :return: The specimen object is being returned.
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            specimen_object_in = TestSpecimenRepo.create_test_specimen_object()
            specimen = specimen_repository.create_specimen(specimen_object_in)
            return specimen

    def test_create_specimen_publication(self):
        """
        This function creates a specimen object and returns it
        """
        specimen = self.create_test_specimen()
        assert isinstance(specimen, Specimen)

    def test_read_specimen_by_id(self):
        """
        This function tests the read_specimen_by_id function in the SpecimenRepository class
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            specimen = self.create_test_specimen()
            read_specimen = specimen_repository.read_specimen_by_id(specimen.specimen_id)
            assert read_specimen is not None
            assert read_specimen.specimen_id == specimen.specimen_id

    def test_delete_specimen(self):
        """
        This function tests the deletion of a specimen
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            specimen = self.create_test_specimen()
            result = specimen_repository.delete_specimen(specimen.specimen_id)
            assert result is True
            with pytest.raises(SpecimenNotFoundException):
                specimen_repository.read_specimen_by_id(specimen.specimen_id)

    def test_read_specimen_by_reg_num(self):
        """
        This function tests the read_specimen_by_reg_num function in the SpecimenRepository class
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            specimen = self.create_test_specimen()
            read_specimen = specimen_repository.read_specimen_by_reg_num(specimen.reg_no)
            assert read_specimen is not None
            assert read_specimen.reg_no == specimen.reg_no

    def test_get_specimens_per_year(self):
        """
        It creates a specimen publication, then gets the number of specimens per year
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            self.create_test_specimen()
            specimens_per_year = specimen_repository.get_specimens_per_year()
            assert isinstance(specimens_per_year, list)

    def test_get_specimens_per_user(self):
        """
        This function returns a dictionary of the number of specimens per user
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            self.create_test_specimen()
            specimens_per_user = specimen_repository.get_specimens_per_user()
            assert isinstance(specimens_per_user, dict)

    def test_get_specimens_per_region(self):
        """
        This function returns a dictionary of the number of specimens per region
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            self.create_test_specimen()
            specimens_per_region = specimen_repository.get_specimens_per_region()
            assert isinstance(specimens_per_region, dict)

    def test_get_gps_for_genus(self):
        """
        This function tests the get_gps_for_genus function in the SpecimenRepository class
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            self.create_test_specimen()
            gps_for_genus = specimen_repository.get_gps_for_search_results("Achillea")
            assert isinstance(gps_for_genus, dict)

    def test_get_last_specimens(self):
        """
        `test_get_last_specimens` tests that the `get_last_specimens` function
        returns a list of specimens
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            self.create_test_specimen()
            last_specimens = specimen_repository.get_last_specimens()
            assert isinstance(last_specimens, list)
            assert len(last_specimens) == 1

    def test_update_specimen(self):
        """
        It updates the species of a specimen.
        """
        with TestingSessionLocal() as db:
            specimen_repository = SpecimenRepository(db)
            specimen = self.create_test_specimen()
            updated_specimen = specimen_repository.update_specimen(
                specimen.specimen_id,
                SpecimenSchemaUpdate(reg_no="new_reg_no"))
            assert updated_specimen is not None
            assert updated_specimen.reg_no == "new_reg_no"

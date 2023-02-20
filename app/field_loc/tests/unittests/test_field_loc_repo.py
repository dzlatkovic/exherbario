"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


import pytest

from app.field_loc.exceptions import FieldLocNotFoundException
from app.tests import TestClass, TestingSessionLocal
from app.field_loc.repository import FieldLocRepository


class TestFieldLocRepo(TestClass):
    """
    This class tests the FieldLocRepo class
    """
    def create_locs_for_methods(self):
        """
        It creates two field locations in the database
        """
        with TestingSessionLocal() as db:
            study_program_repository = FieldLocRepository(db)
            study_program_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                      1400, "woods", 43.0, 22.0)
            study_program_repository.create_field_loc("Greece", "Athens", "Acropolis",
                                                      100, "urban area", 20.4, -15.4)

    def test_create_field_loc(self):
        """
        It creates a new field location in the database
        """
        with TestingSessionLocal() as db:
            field_loc_repository = FieldLocRepository(db)
            field_loc = field_loc_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                              1400, "woods", 43.0, 22.0)
            assert field_loc.country == "Serbia"
            assert field_loc.gps_lat == 43.0

    def test_read_all_locations(self):
        """
        This function creates two locations,
        then reads them back from the database and
        asserts that the number of locations
        read back is 2
        """
        self.create_locs_for_methods()
        with TestingSessionLocal() as db:
            field_loc_repository = FieldLocRepository(db)
            locations = field_loc_repository.read_all_field_locations()
            assert len(locations) == 2

    def test_read_field_loc_by_id(self):
        """
        It creates a new field location, then retrieves it by its ID
        and checks if the country is the same as the one we
        created
        """
        with TestingSessionLocal() as db:
            field_loc_repository = FieldLocRepository(db)
            field_loc = field_loc_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                              1400, "woods", 43.0, 22.0)
            retrieved_loc = field_loc_repository.read_field_loc_by_id(field_loc.field_loc_id)
            assert retrieved_loc.country == "Serbia"

    def test_delete_field_loc(self):
        """
        It deletes the field location.
        """
        with TestingSessionLocal() as db:
            field_loc_repository = FieldLocRepository(db)
            field_loc = field_loc_repository.create_field_loc("Serbia", "Nis", "Suva mt.",
                                                              1400, "woods", 43.0, 22.0)
            assert field_loc_repository.delete_field_loc(field_loc.field_loc_id) is True

    def test_read_field_loc_by_id_not_found(self):
        """
        This function tests that a FieldLocNotFoundException is raised
        when a field location is not found
        """
        with TestingSessionLocal() as db:
            field_loc_repository = FieldLocRepository(db)
            with pytest.raises(FieldLocNotFoundException):
                field_loc_repository.read_field_loc_by_id("invalid_id")

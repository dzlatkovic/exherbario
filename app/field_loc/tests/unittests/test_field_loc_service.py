"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


import pytest

from app.field_loc.exceptions import FieldLocNotFoundException
from app.tests import TestClass
from app.field_loc.services import FieldLocService


class TestFieldLocService(TestClass):
    """This class tests the FieldLocService class"""
    def create_locs_for_methods(self):
        """
        It creates two new field locations
        """
        FieldLocService.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                             1400, "woods", 43.0, 22.0)
        FieldLocService.create_new_field_loc("Greece", "Athens", "Acropolis",
                                             100, "urban area", 20.4, -15.4)

    def test_create_new_field_loc(self):
        """
        This function creates a new field location
        """
        field_loc = FieldLocService.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                                         1400, "woods", 43.0, 22.0)
        assert field_loc.country == "Serbia"

    def test_read_all_field_locations(self):
        """
        This function creates two field locations, then reads all field
        locations and asserts that the length of the list of
        field locations is 2
        """
        self.create_locs_for_methods()
        locations = FieldLocService.read_all_field_locations()
        assert len(locations) == 2

    def test_read_field_loc_by_id(self):
        """
        It creates a new field location, then it reads it by id.
        """
        field_loc = FieldLocService.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                                         1400, "woods", 43.0, 22.0)
        field_loc_id = field_loc.field_loc_id
        retrieved_field_loc = FieldLocService.read_field_loc_by_id(field_loc_id)
        assert retrieved_field_loc.field_loc_id == field_loc_id

    def test_delete_field_loc_by_id(self):
        """
        It creates a new field location, then deletes it and tries to read it
        """
        field_loc = FieldLocService.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                                         1400, "woods", 43.0, 22.0)
        field_loc_id = field_loc.field_loc_id
        FieldLocService.delete_field_loc_by_id(field_loc_id)
        with pytest.raises(FieldLocNotFoundException):
            FieldLocService.read_field_loc_by_id(field_loc_id)

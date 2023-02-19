import pytest
from fastapi import HTTPException

from app.tests import TestClass
from app.field_loc.controller import FieldLocController


class TestFieldLocController(TestClass):
    """This class tests the FieldLocController class"""
    def create_locs_for_methods(self):
        """
        It creates two new field locations
        """
        FieldLocController.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                             1400, "woods", 43.0, 22.0)
        FieldLocController.create_new_field_loc("Greece", "Athens", "Acropolis",
                                             100, "urban area", 20.4, -15.4)

    def test_create_new_field_loc(self):
        """
        This function creates a new field location
        """
        field_loc = FieldLocController.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                                         1400, "woods", 43.0, 22.0)
        assert field_loc.country == "Serbia"

    def test_read_all_field_locations(self):
        """
        This function creates two field locations, then reads all field
        locations and asserts that the length of the list of
        field locations is 2
        """
        self.create_locs_for_methods()
        locations = FieldLocController.get_all_field_locations()
        assert len(locations) == 2

    def test_read_field_loc_by_id(self):
        """
        It creates a new field location, then it reads it by id.
        """
        field_loc = FieldLocController.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                                         1400, "woods", 43.0, 22.0)
        field_loc_id = field_loc.field_loc_id
        retrieved_field_loc = FieldLocController.get_field_loc_by_id(field_loc_id)
        assert retrieved_field_loc.field_loc_id == field_loc_id

    def test_delete_field_loc_by_id(self):
        """
        It creates a new field location, then deletes it and tries to read it
        """
        field_loc = FieldLocController.create_new_field_loc("Serbia", "Nis", "Suva mt.",
                                                         1400, "woods", 43.0, 22.0)
        field_loc_id = field_loc.field_loc_id
        FieldLocController.delete_field_loc_by_id(field_loc_id)
        with pytest.raises(HTTPException):
            FieldLocController.get_field_loc_by_id(field_loc_id)

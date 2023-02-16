"""
This class provides methods for creating, reading, updating,
and deleting field location data.

The methods in this class use a `SessionLocal` instance to interact with the
database through a `FieldLocRepository` object. The `SessionLocal` instance
is created and managed by the methods in this class, and is used to ensure
that database connections are properly managed and closed.
"""


from app.field_loc.models import FieldLoc
from app.db import SessionLocal
from app.field_loc.repository import FieldLocRepository


class FieldLocService:
    """
    This class provides methods for creating, reading, updating, and
    deleting field location data.

    The methods in this class use a `SessionLocal` instance to interact
    with the database through a `FieldLocRepository` object.
    The `SessionLocal` instance is created and managed by the methods
    in this class, and is used to ensure that database connections are
    properly managed and closed.
    """
    @staticmethod
    def create_new_field_loc(country: str, region: str, locality: str, altitude: int,
                             habitat: str, gps_lat: float, gps_long: float) -> FieldLoc:
        """
        It creates a new field location in the database
        :param country: The country of the field location
        :param region: The region of the field location
        :param locality: The locality of the field location
        :param altitude: The altitude of the field location
        :param habitat: The habitat of the field location
        :param gps_lat: The GPS latitude of the field location
        :param gps_long: The GPS longitude of the field location
        :return: The created field location.
        """
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.create_field_loc(country, region, locality, altitude,
                                                   habitat, gps_lat, gps_long)
        except Exception as error:
            raise error

    @staticmethod
    def read_all_field_locations():
        """
        It reads all the field locations from the database
        :return: A list of all field locations
        """
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.read_all_field_locations()
        except Exception as error:
            raise error

    @staticmethod
    def read_field_loc_by_id(field_loc_id: str):
        """
        It takes a field_loc_id as a string, and returns a FieldLoc object
        :param field_loc_id: str
        :return: A field location object
        """
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.read_field_loc_by_id(field_loc_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_field_loc_by_id(field_loc_id: str):
        """
        It deletes a field location by id
        :param field_loc_id: str
        :return: The field_loc_id of the deleted field_loc.
        """
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.delete_field_loc(field_loc_id)
        except Exception as error:
            raise error

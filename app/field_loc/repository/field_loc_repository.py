"""
Module for the FieldLocRepository class.

This module defines the `FieldLocRepository` class, which is used to
interact with the database layer of the application for field location
operations. The class provides methods for creating, reading, and
deleting field location data in the database.
"""


from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import lock_for_update
from app.field_loc.models import FieldLoc
from app.field_loc.exceptions import FieldLocExceptionCode, FieldLocNotFoundException
from app.field_loc.schemas import FieldLocSchemaUpdate
from app.specimen.models import ScientificCorrection


class FieldLocRepository:
    """
    Repository class for field location operations.

    This class provides methods for interacting with the database layer of the application
    for field location operations. The methods allow for creating, reading, and deleting field
    location data in the database.
    """
    def __init__(self, db: Session):
        """
        Constructor method for creating a new instance of the FieldLocRepository
        class.

        This method creates a new instance of the FieldLocRepository class with
        the specified database session.
        """
        self.db = db

    def create_field_loc(self, country: str, region: str, locality: str, altitude: int,
                         habitat: str, gps_lat: float, gps_long: float, coordinate_uncertainty_m=None, geodetic_datum=None, georeference_source=None):
        """
        Method for creating a new field location in the database.

        This method creates a new field location in the database with the specified
        values for the field location attributes
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
            field_loc = FieldLoc(country, region, locality, altitude, habitat, gps_lat, gps_long,
                                 coordinate_uncertainty_m=coordinate_uncertainty_m, geodetic_datum=geodetic_datum, georeference_source=georeference_source)
            self.db.add(field_loc)
            self.db.commit()
            self.db.refresh(field_loc)
            return field_loc
        except ValueError as error:
            raise error
        except IntegrityError as error:
            raise error
        except Exception as error:
            raise error

    def read_all_field_locations(self):
        """
        It returns all the field locations in the database
        :return: A list of all the field locations in the database.
        """
        courses = self.db.query(FieldLoc).all()
        return courses

    def read_field_loc_by_id(self, field_loc_id: str):
        """
        This function takes in a field_loc_id and returns the
        field_loc object with that id
        :param field_loc_id: str
        :return: The field_loc object is being returned.
        """
        field_loc = self.db.query(FieldLoc).filter(FieldLoc.field_loc_id
                                                   == field_loc_id).first()
        if field_loc is None:
            raise FieldLocNotFoundException(f"Location with provided ID: "
                                            f"{field_loc_id} not found.", 404)
        return field_loc

    def delete_field_loc(self, field_loc_id: str):
        """
        This function deletes a field location from the database
        :param field_loc_id: The ID of the field location to be deleted
        :return: True
        """
        try:
            field_loc = self.db.query(FieldLoc).filter(FieldLoc.field_loc_id
                                                       == field_loc_id).first()
            if field_loc is None:
                raise FieldLocNotFoundException(f"Location with provided ID: "
                                                f"{field_loc_id} not found.", 400)
            self.db.delete(field_loc)
            self.db.commit()
            return True
        except IntegrityError as error:
            self.db.rollback()
            raise FieldLocExceptionCode(
                "This collection site is referenced by a voucher or a scientific correction.", 409
            ) from error

    def update_field_loc(self, field_loc_id: str, field_loc_data: FieldLocSchemaUpdate, actor_id: str):
        """
        It takes a field_loc_id and a field_loc_data object,
        finds the field_loc in the database with the matching
        field_loc_id, and updates the field_loc with the data
        in the field_loc_data object
        :param field_loc_id: str
        :type field_loc_id: str
        :param field_loc_data: FieldLocSchemaUpdate
        :type field_loc_data: FieldLocSchemaUpdate
        :return: The field_loc object is being returned.
        """
        query = self.db.query(FieldLoc).filter_by(field_loc_id=field_loc_id)
        field_loc = lock_for_update(self.db, query).first()
        if field_loc:
            changes = {
                key: value for key, value in field_loc_data.model_dump(
                    exclude={"correction_reason"}, exclude_unset=True
                ).items() if getattr(field_loc, key) != value
            }
            if changes:
                if any(key in changes and changes[key] is None for key in ("country", "region", "locality")):
                    raise ValueError("Country, region and locality cannot be cleared.")
                self.db.add(ScientificCorrection(
                    field_loc_id=field_loc_id, actor_id=actor_id, reason=field_loc_data.correction_reason,
                    old_values={key: getattr(field_loc, key) for key in changes}, new_values=changes,
                ))
                for key, value in changes.items():
                    setattr(field_loc, key, value)
                self.db.commit()
                self.db.refresh(field_loc)
            return field_loc
        return None

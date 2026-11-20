"""
Controller for handling field location operations.

This module defines a controller for handling field location operations, such as creating,
retrieving, and deleting field locations. It uses a service to interact with the database,
and handles any exceptions that may occur during these operations.
"""

from fastapi import HTTPException, Response

from app.field_loc.schemas import FieldLocSchemaUpdate
from app.field_loc.services import FieldLocService
from app.field_loc.exceptions import FieldLocExceptionCode, FieldLocNotFoundException


class FieldLocController:
    """
    Controller class for managing field locations.

    This class provides methods for handling requests related to field locations. It uses
    a service to handle the logic of field location operations.
    """
    @staticmethod
    def create_new_field_loc(country: str, region: str, locality: str, altitude: int,
                             habitat: str, gps_lat: float, gps_long: float, coordinate_uncertainty_m=None, geodetic_datum=None, georeference_source=None):
        """
        Creates a new field location with the provided data.

        This function creates a new field location with the data provided as parameters,
        and returns the created field location as a response
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
            course = FieldLocService.create_new_field_loc(country, region, locality, altitude,
                                                          habitat, gps_lat, gps_long,
                                                          coordinate_uncertainty_m=coordinate_uncertainty_m, geodetic_datum=geodetic_datum, georeference_source=georeference_source)
            return course
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FieldLocExceptionCode as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_all_field_locations():
        """
        Retrieves all field locations from the database.

        This function retrieves all field locations from the database, and returns them as a
        response.
        :return: A list of all field locations
        """
        field_locations = FieldLocService.read_all_field_locations()
        return field_locations

    @staticmethod
    def get_field_loc_by_id(field_loc_id: str):
        """
        Retrieves a field location with the specified ID from the database.

        This function retrieves a field location with the specified ID from the database,
        and returns it as a response
        :param field_loc_id: The ID of the field location to be retrieved
        :return: A field_loc object
        """
        try:
            field_loc = FieldLocService.read_field_loc_by_id(field_loc_id)
            return field_loc
        except FieldLocNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_field_loc_by_id(field_loc_id: str):
        """
        Deletes a field location with the specified ID from the database.

        This function deletes a field location with the specified ID from the database,
        and returns a response indicating success or failure
        :param field_loc_id: The ID of the field location to delete.
        :return: The field location with the provided ID is being deleted.
        """
        try:
            FieldLocService.delete_field_loc_by_id(field_loc_id)
            return Response(content=f"Field location with provided ID: "
                                    f"{field_loc_id} deleted.", status_code=200)
        except (FieldLocNotFoundException, FieldLocExceptionCode) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def update_field_loc(field_loc_id: str, field_loc_data: FieldLocSchemaUpdate, actor_id: str):
        """
        It updates the field_loc_data for a given field_loc_id
        :param field_loc_id: The ID of the field location to update
        :type field_loc_id: str
        :param field_loc_data: This is the data that will be used to update the field_loc
        :type field_loc_data: FieldLocSchemaUpdate
        :return: The updated field_loc object
        """
        try:
            return FieldLocService.update_field_loc(field_loc_id, field_loc_data, actor_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FieldLocNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

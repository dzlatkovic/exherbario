"""
API router and controller for managing field locations.

This module defines an API router using FastAPI to handle requests related to field locations.
It includes several endpoints for creating, retrieving, and deleting field locations, and
uses a controller to handle the logic of these operations.
"""

from fastapi import APIRouter, Depends

from app.field_loc.controller import FieldLocController
from app.field_loc.schemas import FieldLocSchema, FieldLocSchemaIn, FieldLocSchemaUpdate
from app.users.controller import JWTBearer
from app.users.models import User

field_loc_router = APIRouter(prefix="/api/field-locations", tags=["FieldLoc"])


@field_loc_router.post("/create-new-field-loc", response_model=FieldLocSchema,
                       dependencies=[Depends(JWTBearer("super_user"))])
def create_new_field_loc(field_loc: FieldLocSchemaIn):
    """
    `create_new_field_loc` creates a new field location

    :param field_loc: The field location data provided in the request body
    :type field_loc: FieldLocSchemaIn
    :return: The created field location.
    """
    return FieldLocController.create_new_field_loc(country=field_loc.country,
                                                   region=field_loc.region,
                                                   locality=field_loc.locality,
                                                   altitude=field_loc.altitude,
                                                   habitat=field_loc.habitat,
                                                   gps_lat=field_loc.gps_lat,
                                                   gps_long=field_loc.gps_long)


@field_loc_router.get("/get-all-field-locations", response_model=list[FieldLocSchema])
def get_all_field_locations():
    """
    This function returns a list of all field locations

    :return: A list of all field locations
    """
    field_locations = FieldLocController.get_all_field_locations()
    return field_locations


@field_loc_router.get("/get-field-loc-by-id", response_model=FieldLocSchema)
def get_field_loc_by_id(field_loc_id: str):
    """
    Endpoint for retrieving a field location by ID.

    This function retrieves a field location with the specified ID from the database, and
    returns it as a response
    
    :param field_loc_id: The ID of the field location to retrieve.
    :return: The retrieved field location object
    """
    return FieldLocController.get_field_loc_by_id(field_loc_id)


@field_loc_router.delete("/delete-field-loc",
                         dependencies=[Depends(JWTBearer("super_user"))])
def delete_field_loc_by_id(field_loc_id: str):
    """
    Endpoint for deleting a field location by ID.

    This function deletes a field location with the specified ID from the database, and
    returns a response indicating success or failure
    :param field_loc_id: The ID of the field location to delete.
    :return: A response indicating whether the field location was successfully deleted.
    """
    return FieldLocController.delete_field_loc_by_id(field_loc_id)


@field_loc_router.put("/update-field-loc", response_model=FieldLocSchema)
def update_field_loc(field_loc_id: str, field_loc_data: FieldLocSchemaUpdate,
                     actor: User = Depends(JWTBearer("super_user"))):
    """
    Update an existing field location with the given data

    :param field_loc_id: The ID of the field location to update
    :type field_loc_id: str
    :param field_loc_data: The data to update the field location with
    :type field_loc_data: FieldLocSchemaUpdate
    :return: The updated field_loc object
    """
    return FieldLocController.update_field_loc(field_loc_id, field_loc_data, actor.user_id)

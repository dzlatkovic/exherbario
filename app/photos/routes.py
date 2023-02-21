"""
This module defines the endpoints for interacting with photo data.
"""


from fastapi import APIRouter, Depends

from app.photos.controller import PhotosController
from app.photos.schemas import PhotosSchema, PhotosSchemaIn
from app.users.controller import JWTBearer

photos_router = APIRouter(prefix="/api/photos", tags=["Photos"])


@photos_router.post("/create-new-photos", response_model=PhotosSchema,
                    dependencies=[Depends(JWTBearer("super_user"))])
def create_new_photos(photos: PhotosSchemaIn):
    """
    Endpoint for creating a new photo record in the database
    :param photos: A `PhotosSchemaIn` object containing the data for the new photo record.
    :return: A `PhotosSchema` object representing the new photo record
    """
    return PhotosController.create_new_photos(field_photo=photos.field_photo,
                                              specimen_photo=photos.specimen_photo)


@photos_router.get("/get-all-photos", response_model=list[PhotosSchema])
def get_all_photos():
    """
    Endpoint for retrieving all photo records from the database.
    :return: A list of `PhotosSchema` objects representing the photo records.
    """
    photos = PhotosController.get_all_photos()
    return photos


@photos_router.get("/get-photos-by-id", response_model=PhotosSchema)
def get_field_loc_by_id(photos_id: str):
    """
    Endpoint for retrieving a single photo record from the database by ID
    :param photos_id: A string containing the ID of the photo record to retrieve.
    :return: A `PhotosSchema` object representing the photo record.
    """
    return PhotosController.get_photos_by_id(photos_id)


@photos_router.delete("/delete-photos",
                      dependencies=[Depends(JWTBearer("super_user"))])
def delete_photos_by_id(photos_id: str):
    """
    Endpoint for deleting a photo record from the database by ID
    :param photos_id: A string containing the ID of the photo record to delete.
    :return: A `Response` object indicating the status of the delete operation.
    """
    return PhotosController.delete_photos_by_id(photos_id)

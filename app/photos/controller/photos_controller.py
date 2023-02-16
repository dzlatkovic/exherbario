"""
This module defines the `PhotosController` class, which contains the
logic for handling HTTP requests related to photos.

The `PhotosController` class provides methods for creating,
reading, and deleting photos.
"""


from fastapi import HTTPException, Response

from app.photos.services import PhotosService
from app.photos.exceptions import (PhotosNotFoundException, PhotoAlreadyExistsException, IdenticalPhotosException)


class PhotosController:
    """
    Controller for handling requests related to photos.

    This class contains methods for handling incoming requests related to photos,
    which are then passed on to the service layer for processing. If any exceptions
    occur during processing, they are caught and converted to appropriate
    HTTP errors to be returned to the client.
    """
    @staticmethod
    def create_new_photos(field_photo: str, specimen_photo: str):
        """
        Create new photos with provided photo paths
        :param field_photo: Path to the field photo
        :param specimen_photo: Path to the specimen photo
        :return: Created photos.
        """
        try:
            photos = PhotosService.create_new_photos(field_photo, specimen_photo)
            return photos
        except (PhotoAlreadyExistsException, IdenticalPhotosException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_all_photos():
        """
        Get all the photos from the database.

        :return: All the photos in the database.
        """
        photos = PhotosService.read_all_photos()
        return photos

    @staticmethod
    def get_photos_by_id(photos_id: str):
        """
        Get photos with the provided ID from the database
        :param photos_id: ID of the photos to retrieve.
        :return: Photos with the provided ID.
        """
        try:
            photos = PhotosService.read_photos_by_id(photos_id)
            return photos
        except PhotosNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_photos_by_id(photos_id: str):
        """
        Delete photos with the provided ID from the database
        :param photos_id: ID of the photos to delete.
        :return: Response indicating whether the photos were deleted or not.
        """
        try:
            PhotosService.delete_photos_by_id(photos_id)
            return Response(content=f"Photos with provided ID: "
                                    f"{photos_id} deleted.", status_code=200)
        except PhotosNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

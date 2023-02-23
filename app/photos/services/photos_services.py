"""
This module contains the implementation of the `PhotosService` class
that provides an interface to manipulate the `photos` database.
"""
from app.photos.exceptions import IdenticalPhotosException
from app.photos.models import Photos
from app.db import SessionLocal
from app.photos.repository import PhotosRepository
from app.photos.schemas import PhotosSchemaUpdate


class PhotosService:
    """
    A class used to interact with the photos repository through
    the repository layer.
    """
    @staticmethod
    def create_new_photos(field_photo: str, specimen_photo: str) -> Photos:
        """
        Adds a new photos object to the database
        :param field_photo: The path to the field photo
        :type field_photo: str
        :param specimen_photo: The path to the specimen photo
        :type specimen_photo: str
        :return: The created photos object
        :rtype: Photos
        :raises: Exception, if any error occurs while creating a photos object
        """
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.create_photos(field_photo, specimen_photo)
        except Exception as error:
            raise error

    @staticmethod
    def read_all_photos():
        """
        Reads all photos objects from the database
        :return: A list of all photos objects
        :rtype: List[Photos]
        """
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.read_all_photos()
        except Exception as error:
            raise error

    @staticmethod
    def read_photos_by_id(photos_id: str):
        """
        Reads a photos object from the database with the specified ID
        :param photos_id: The ID of the photos object to read
        :type photos_id: str
        :return: The photos object with the specified ID
        :rtype: Photos
        """
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.read_photos_by_id(photos_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_photos_by_id(photos_id: str):
        """
        Deletes a photos object from the database with the specified ID
        :param photos_id: The ID of the photos object to delete
        :type photos_id: str
        :return: A response indicating that the photos object has been deleted.
        :rtype: Response
        """
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.delete_photos(photos_id)
        except Exception as error:
            raise error

    @staticmethod
    def update_photos(photos_id: str, photos_update: PhotosSchemaUpdate):
        """
        It updates the photos of a specimen
        :param photos_id: str
        :type photos_id: str
        :param photos_update: PhotosSchemaUpdate
        :type photos_update: PhotosSchemaUpdate
        :return: The updated photos.
        """
        try:
            with SessionLocal() as db:
                if photos_update.field_photo == photos_update.specimen_photo:
                    raise IdenticalPhotosException(code=400, message="Identical photos.")
                repository = PhotosRepository(db)
                return repository.update_photos(photos_id, photos_update)
        except Exception as error:
            raise error

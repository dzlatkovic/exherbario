"""
This module defines the PhotosRepository class which is responsible for querying,
creating, updating and deleting photo records from the database.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.photos.models import Photos
from app.photos.exceptions import (PhotosNotFoundException,
                                   IdenticalPhotosException,
                                   PhotoAlreadyExistsException)


class PhotosRepository:
    """
    Photos repository class that handles database operations for Photos model.
    """
    def __init__(self, db: Session):
        """
        Constructor method for PhotosRepository
        :param db: Session object for database connection.
        """
        self.db = db

    def create_photos(self, field_photo: str, specimen_photo: str):
        """
        Method to create new Photos record
        :param field_photo: str - Path to the field photo
        :param specimen_photo: str - Path to the specimen photo
        :return: Created Photos object.
        """
        if field_photo == specimen_photo:
            raise IdenticalPhotosException(code=400, message="Identical photos.")
        try:
            photos = Photos(field_photo, specimen_photo)
            self.db.add(photos)
            self.db.commit()
            self.db.refresh(photos)
            return photos
        except IntegrityError as error:
            if "Duplicate entry" in str(error):
                raise PhotoAlreadyExistsException(
                    code=400,
                    message="Photo already exists in the database") from error
            raise error
        except Exception as error:
            raise error

    def read_all_photos(self):
        """
        Method to get all Photos records
        :return: List of all Photos objects.
        """
        courses = self.db.query(Photos).all()
        return courses

    def read_photos_by_id(self, photos_id: str):
        """
        Method to get a Photos record by ID
        :param photos_id: str - ID of the Photos record to get
        :return: Photos object.
        """
        photos = self.db.query(Photos).filter(Photos.photos_id == photos_id).first()
        if photos is None:
            raise PhotosNotFoundException(f"Photos with provided ID: "
                                          f"{photos_id} not found.", 400)
        return photos

    def delete_photos(self, photos_id: str):
        """
        Method to delete a Photos record by ID
        :param photos_id: str - ID of the Photos record to delete
        :return: True if deletion is successful
        """
        try:
            photos = self.db.query(Photos).filter(Photos.photos_id == photos_id).first()
            if photos is None:
                raise PhotosNotFoundException(f"Photos with provided ID: "
                                              f"{photos_id} not found.", 400)
            self.db.delete(photos)
            self.db.commit()
            return True
        except Exception as error:
            raise error

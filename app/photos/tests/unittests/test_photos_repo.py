"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


from app.photos.exceptions import (PhotosNotFoundException,
                                   IdenticalPhotosException,
                                   PhotoAlreadyExistsException)
from app.tests import TestClass, TestingSessionLocal
from app.photos.repository import PhotosRepository


class TestPhotosRepository(TestClass):
    """
    This class tests the PhotosRepository class.
    """
    def create_photos_for_methods(self):
        """
        Create two new photos.
        """
        with TestingSessionLocal() as db:
            photos_repository = PhotosRepository(db)
            photos_repository.create_photos("field1.jpg", "specimen1.jpg")
            photos_repository.create_photos("field2.jpg", "specimen2.jpg")

    def test_create_photos(self):
        """
        This function tests the create_photos method.
        """
        with TestingSessionLocal() as db:
            photos_repository = PhotosRepository(db)
            photos = photos_repository.create_photos("field1.jpg",
                                                     "specimen1.jpg")
            assert photos.field_photo == "field1.jpg"
            assert photos.specimen_photo == "specimen1.jpg"
            try:
                photos_repository.create_photos("field1.jpg", "field1.jpg")
            except IdenticalPhotosException as error:
                assert error.code == 400
                assert error.message == "Identical photos."

            try:
                photos_repository.create_photos("field1.jpg", "specimen1.jpg")
            except PhotoAlreadyExistsException as error:
                assert error.code == 400
                assert error.message == "Photo already exists in the database"

    def test_read_all_photos(self):
        """
        This function tests the read_all_photos method.
        """
        self.create_photos_for_methods()
        with TestingSessionLocal() as db:
            photos_repository = PhotosRepository(db)
            photos = photos_repository.read_all_photos()
            assert len(photos) == 2

    def test_read_photos_by_id(self):
        """
        This function tests the read_photos_by_id method.
        """
        self.create_photos_for_methods()
        with TestingSessionLocal() as db:
            photos_repository = PhotosRepository(db)
            photos = photos_repository.create_photos("field3.jpg",
                                                     "specimen3.jpg")
            photos_id = photos.photos_id
            result = photos_repository.read_photos_by_id(photos_id)
            assert result.photos_id == photos_id
            try:
                photos_repository.read_photos_by_id("999")
            except PhotosNotFoundException as error:
                assert error.code == 400
                assert error.message == "Photos with provided ID: 999 not found."

    def test_delete_photos(self):
        """
        This function tests the delete_photos method.
        """
        self.create_photos_for_methods()
        with TestingSessionLocal() as db:
            photos_repository = PhotosRepository(db)
            photos = photos_repository.create_photos("field3.jpg", "specimen3.jpg")
            photos_id = photos.photos_id
            result = photos_repository.delete_photos(photos_id)
            assert result is True
            try:
                photos_repository.delete_photos("999")
            except PhotosNotFoundException as error:
                assert error.code == 400
                assert error.message == "Photos with provided ID: 999 not found."

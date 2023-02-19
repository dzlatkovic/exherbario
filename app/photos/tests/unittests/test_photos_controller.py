import pytest
from fastapi import HTTPException

from app.photos.controller import PhotosController
from app.photos.exceptions import IdenticalPhotosException, PhotoAlreadyExistsException, PhotosNotFoundException
from app.tests import TestClass


class TestPhotosController(TestClass):
    """
    Test class for PhotosController.
    """
    def test_create_new_photos(self):
        """
        Test creating a new photo.
        """
        photo = PhotosController.create_new_photos("path/to/field/photo", "path/to/specimen/photo")
        assert photo is not None

    def test_create_existing_photos(self):
        """
        Test creating a photo that already exists.
        """
        with pytest.raises(HTTPException):
            PhotosController.create_new_photos("path/to/field/photo", "path/to/specimen/photo")
            PhotosController.create_new_photos("path/to/field/photo", "path/to/specimen/photo")

    def test_create_identical_photos(self):
        """
        Test creating photos with identical paths.
        """
        with pytest.raises(HTTPException):
            PhotosController.create_new_photos("path/to/photo", "path/to/photo")

    def test_get_all_photos(self):
        """
        Test retrieving all photos.
        """
        PhotosController.create_new_photos("path/to/field/photo", "path/to/specimen/photo")
        photos = PhotosController.get_all_photos()
        assert len(photos) > 0

    def test_get_photos_by_id(self):
        """
        Test retrieving photos by ID.
        """
        photos = PhotosController.create_new_photos("path/to/field/photo", "path/to/specimen/photo")
        retrieved_photos = PhotosController.get_photos_by_id(str(photos.photos_id))
        assert photos.specimen_photo == retrieved_photos.specimen_photo
        assert photos.field_photo == retrieved_photos.field_photo

    def test_get_nonexistent_photos_by_id(self):
        """
        Test retrieving nonexistent photos by ID.
        """
        with pytest.raises(HTTPException):
            PhotosController.get_photos_by_id("nonexistent-id")

    def test_delete_photos_by_id(self):
        """
        Test deleting photos by ID.
        """
        photos = PhotosController.create_new_photos("path/to/field/photo", "path/to/specimen/photo")
        response = PhotosController.delete_photos_by_id(str(photos.photos_id))
        assert response.status_code == 200

    def test_delete_nonexistent_photos_by_id(self):
        """
        Test deleting nonexistent photos by ID.
        """
        with pytest.raises(HTTPException):
            PhotosController.delete_photos_by_id("nonexistent-id")
